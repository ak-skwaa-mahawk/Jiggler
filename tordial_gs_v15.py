"""
tordial_gs_v15_fixed.py
Tordial–GS Manifold v15 Fixed — Triple-Ring + Density Control + Visualization
"""

import math
import yaml
import numpy as np
import random
import os
import sqlite3
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# =============================================================================
# CONFIG LOAD
# =============================================================================
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

t = config["tordial"]
t["base_frequency_hz"] = 79.79

PHI_OP: float = float(t["phi_op"])
GEAR_SHIFT: float = float(t.get("gear_shift_correction", 1.04))
PI_3D: float = float(t["pi_3d"])
BASE_HZ: float = float(t["base_frequency_hz"])

# =============================================================================
# GS SWEEP
# =============================================================================
@dataclass
class GSMetrics:
    sigma_T: float
    kappa_GS_T: float
    lambda_GS_T: float
    rho_GS_T: float
    band: str

class GSSweep:
    def __init__(self, phi_op: float = PHI_OP, gear_shift: float = GEAR_SHIFT):
        self._denom = 4.0 * phi_op * gear_shift

    def compute_gs(self, d: int, r: int) -> GSMetrics:
        sigma_T = r - (d ** 2) / self._denom
        if sigma_T <= 0:
            return GSMetrics(sigma_T=sigma_T, kappa_GS_T=0.0, lambda_GS_T=0.0, rho_GS_T=0.0, band="SUBCRITICAL")
        kappa = sigma_T / d
        lam = math.sqrt(sigma_T)
        rho = lam / d
        band = "MARGINAL" if kappa < 3.0 else "GOLDILOCKS" if kappa < 8.0 else "DEEP_GS"
        return GSMetrics(sigma_T=sigma_T, kappa_GS_T=kappa, lambda_GS_T=lam, rho_GS_T=rho, band=band)

gs_sweep = GSSweep()

# =============================================================================
# SURFACE CODE + ANYON
# =============================================================================
class Anyon:
    def __init__(self, anyon_type: str, node_id: int, position: float):
        self.type = anyon_type
        self.node_id = node_id
        self.position = position
        self.lifetime = 0

class SurfaceCodeDecoder:
    def decode(self, syndromes: List[Tuple[int, str]]) -> List[Tuple[int, int]]:
        corrections: List[Tuple[int, int]] = []
        unpaired = list(syndromes)
        i = 0
        while i < len(unpaired):
            matched = False
            for j in range(i + 1, len(unpaired)):
                if unpaired[i][1] == unpaired[j][1]:
                    corrections.append((unpaired[i][0], unpaired[j][0]))
                    del unpaired[j]
                    del unpaired[i]
                    matched = True
                    break
            if not matched:
                i += 1
        return corrections

# =============================================================================
# RING GOVERNOR (Fixed)
# =============================================================================
class RingGovernor:
    def __init__(self, target_sigma: float = 120.0, kp: float = 0.012, ki: float = 0.003, kd: float = 0.006):
        self.target = target_sigma
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self._integral = 0.0
        self._prev_error = 0.0

    def step(self, current_sigma: float) -> Tuple[int, int]:
        error = self.target - current_sigma
        self._integral = max(-500.0, min(500.0, self._integral + error))
        derivative = error - self._prev_error
        self._prev_error = error
        u = self.kp * error + self.ki * self._integral + self.kd * derivative
        delta_d = int(round(max(-2, min(2, u * 0.3))))
        delta_r = int(round(max(-8, min(8, u * 1.2))))
        return delta_d, delta_r

# =============================================================================
# NODES
# =============================================================================
class TordialAgentNode:
    TAU_3D: float = 2.0 * PI_3D
    OMEGA_RADS: float = 2.0 * math.pi * BASE_HZ
    CHASE_RATIO_TAU: float = TAU_3D / PHI_OP

    def __init__(self, d: int, r: int, node_id: int):
        self.node_id = node_id
        self.d = d
        self.r = r
        self.load = 0.0
        self.decision = "STABLE"
        self.load_history: List[float] = []

class OpenTordialAgentNode(TordialAgentNode):
    def __init__(self, d: int, r: int, node_id: int, x: float = 0.0, y: float = 0.0):
        super().__init__(d, r, node_id)
        self.drift_phase = (x + y) % self.TAU_3D
        self.sigma_T: float = 0.0
        self.fission_count: int = 0
        self.quarantined: bool = False
        self.high_kappa_streak: int = 0
        self._phi_op = PHI_OP
        self._gear_shift = GEAR_SHIFT
        self._denom = 4.0 * PHI_OP * GEAR_SHIFT

    def compute_and_update_gs(self, curvature_pressure: float, resonance: float) -> float:
        if curvature_pressure > 0.6:
            delta_d = max(1, int(resonance * 0.35 + self.drift_phase * 0.1))
            self.d += delta_d
            if resonance > 0.4 and random.random() < 0.45:
                self.r += 1
        denom = self._denom + self.drift_phase * 0.08
        self.sigma_T = self.r - (self.d ** 2 / denom)
        self.drift_phase = (self.drift_phase + 0.017) % self.TAU_3D
        return self.sigma_T

    def measure_syndrome(self) -> List[str]:
        syndromes: List[str] = []
        if self.sigma_T < -180:
            syndromes.append("e")
        if abs(self.drift_phase % (math.pi / 2)) > 0.38:
            syndromes.append("m")
        return syndromes

    def apply_governor_correction(self, delta_d: int, delta_r: int) -> None:
        self.d = max(4, self.d + delta_d)
        self.r = max(20, self.r + delta_r)

# =============================================================================
# DB PERSISTENCE
# =============================================================================
DB_PATH = "tordial_manifold.db"

def _ensure_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS nodes (
        node_id INTEGER, ring TEXT, d INTEGER, r INTEGER, sigma_T REAL,
        drift_phase REAL, fission_count INTEGER, parent_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit()
    conn.close()

def persist_node_state(node: OpenTordialAgentNode, ring: str = "A", parent_id: Optional[int] = None):
    if not os.path.exists(DB_PATH):
        _ensure_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""INSERT INTO nodes 
        (node_id, ring, d, r, sigma_T, drift_phase, fission_count, parent_id) 
        VALUES (?,?,?,?,?,?,?,?)""",
        (node.node_id, ring, node.d, node.r, node.sigma_T, node.drift_phase, node.fission_count, parent_id))
    conn.commit()
    conn.close()

# =============================================================================
# CURVATURE FIELD
# =============================================================================
class CurvatureField:
    def __init__(self):
        self.last_pressure = 0.0
        self.last_resonance = 0.0

    def compute(self, avg_sigma: float, avg_kappa: float, global_energy: float, 
                logical_error_rate: float, node_count: int) -> Tuple[float, float]:
        kappa_norm = max(0.0, min(1.0, avg_kappa / 12.0))
        energy_norm = max(0.0, min(1.0, global_energy / 3000.0))
        sigma_norm = max(-1.0, min(1.0, avg_sigma / 500.0))
        ler = max(0.0, min(1.0, logical_error_rate))

        base_pressure = 0.45 * kappa_norm + 0.35 * energy_norm + 0.20 * max(0.0, sigma_norm)
        pressure = base_pressure * (1.0 - 0.6 * ler)
        crowding = max(0.0, min(0.3, (node_count - 24) / 80.0))
        pressure += crowding

        resonance = (0.55 * kappa_norm + 0.35 * max(0.0, sigma_norm) + 0.10 * energy_norm) * (1.0 - 0.8 * ler)

        pressure = max(0.0, min(1.25, pressure))
        resonance = max(0.0, min(1.0, resonance))

        alpha = 0.35
        pressure = alpha * pressure + (1 - alpha) * self.last_pressure
        resonance = alpha * resonance + (1 - alpha) * self.last_resonance

        self.last_pressure = pressure
        self.last_resonance = resonance
        return pressure, resonance

# =============================================================================
# GLOBAL PARAMETERS (Tuned)
# =============================================================================
CURV_COUPLING = {
    ("A","B"): 0.14, ("B","A"): 0.11,
    ("A","C"): 0.09, ("C","A"): 0.07,
    ("B","C"): 0.12, ("C","B"): 0.10,
}

INNER_FAILOVER_KAPPA = 2.5
OUTER_FAILOVER_CURV = 1.05
MAX_NODES_PER_RING = 380
GROWTH_DAMPING = 0.88

# =============================================================================
# TRIPLE RING MATRIX
# =============================================================================
class TripleRingTordialMatrix:
    def __init__(self, node_count: int = 12):
        self.current_tick = 0
        self.decoder = SurfaceCodeDecoder()

        self.curv_a = CurvatureField()
        self.curv_b = CurvatureField()
        self.curv_c = CurvatureField()

        self.nodes_a: List[OpenTordialAgentNode] = []
        self.nodes_b: List[OpenTordialAgentNode] = []
        self.nodes_c: List[OpenTordialAgentNode] = []

        self.governor_a = RingGovernor(135.0, 0.011, 0.0035, 0.006)
        self.governor_b = RingGovernor(78.0, 0.009, 0.002, 0.005)
        self.governor_c = RingGovernor(108.0, 0.010, 0.003, 0.005)

        self.energy = {"A": 900.0, "B": 600.0, "C": 300.0}
        self.ler = {"A": 0.0, "B": 0.0, "C": 0.0}

        self.bridge_nodes_spawned = 0
        _ensure_db()
        self._seed_rings(node_count)

    def _seed_rings(self, node_count):
        for i in range(node_count):
            angle = (2 * math.pi * i) / node_count
            node = OpenTordialAgentNode(42 + (i%4)*2, 380 + (i%4)*16, i, angle, angle)
            self.nodes_a.append(node)

        for i in range(8):
            angle = (2 * math.pi * i) / 8 + math.pi/8
            node_id = node_count + i
            node = OpenTordialAgentNode(28 + (i%3)*3, 210 + (i%3)*10, node_id, angle, angle)
            self.nodes_b.append(node)

    def _next_node_id(self):
        return len(self.nodes_a) + len(self.nodes_b) + len(self.nodes_c) + self.bridge_nodes_spawned

    def _ring_avg_kappa(self, ring):
        return float(np.mean([gs_sweep.compute_gs(n.d, n.r).kappa_GS_T for n in ring])) if ring else 0.0

    def _ring_avg_sigma(self, ring):
        return float(np.mean([gs_sweep.compute_gs(n.d, n.r).sigma_T for n in ring])) if ring else 0.0

    def _ring_health(self, ring):
        if not ring: return 0.0
        avg_k = self._ring_avg_kappa(ring)
        return round((0.4 + min(avg_k/12.0, 1.0)*0.35 + 0.25*0.85)*100, 2)

    def _perform_fission(self, parent, ring, label):
        parent.fission_count += 1
        child_id = self._next_node_id()
        child = OpenTordialAgentNode(parent.d + 1, parent.r + 1, child_id,
                                   parent.drift_phase + 0.1, parent.drift_phase + 0.1)
        ring.append(child)
        persist_node_state(child, label, parent.node_id)

    def _attempt_spawning(self, ring, label, energy, health):
        if len(ring) >= MAX_NODES_PER_RING:
            return 0
        spawned = 0
        for node in list(ring):
            m = gs_sweep.compute_gs(node.d, node.r)
            if m.kappa_GS_T > 8.0:
                node.high_kappa_streak += 1
            else:
                node.high_kappa_streak = 0

            if node.high_kappa_streak >= 3 and health > 62 and energy > 420:
                prob = min(0.32, 0.25 + 0.055 * (m.kappa_GS_T - 8.0)) * GROWTH_DAMPING
                if random.random() < prob:
                    self._perform_fission(node, ring, label)
                    spawned += 1
        return spawned

    def _measure_syndromes(self, ring):
        out = []
        for node in ring:
            for s in node.measure_syndrome():
                out.append((node.node_id, s))
        return out

    def _apply_error_correction(self, ring):
        syndromes = self._measure_syndromes(ring)
        decoder = self.decoder
        corrections = decoder.decode(syndromes)
        corrected = 0
        ids = {c for pair in corrections for c in pair}
        for node in ring:
            if node.node_id in ids:
                node.sigma_T = max(node.sigma_T, -50.0)
                node.d = max(4, node.d - 1)
                corrected += 1
        return corrected

    def _update_anyons(self, ring):
        syndromes = self._measure_syndromes(ring)
        node_map = {n.node_id: n for n in ring}
        anyons = [Anyon(s[1], s[0], node_map[s[0]].drift_phase) 
                 for s in syndromes if s[0] in node_map]
        for a in anyons:
            a.lifetime += 1
        wrapped = sum(1 for a in anyons if a.lifetime > 25)
        ler = min(1.0, wrapped / max(1, len(anyons)) * 0.7) if anyons else 0.0
        return anyons, ler

    def _cross_ring_failover(self):
        avg_kappa_a = self._ring_avg_kappa(self.nodes_a)
        pressure_b = self.curv_b.last_pressure

        # Inner → Bridge
        if avg_kappa_a < INNER_FAILOVER_KAPPA and self.nodes_a:
            stressed = sorted(self.nodes_a, key=lambda n: gs_sweep.compute_gs(n.d, n.r).kappa_GS_T)[:2]
            for src in stressed:
                bridge_id = self._next_node_id()
                bridge = OpenTordialAgentNode(max(4, src.d-2), src.r+15, bridge_id,
                                            src.drift_phase + math.pi, src.drift_phase + math.pi)
                self.nodes_c.append(bridge)
                self.bridge_nodes_spawned += 1
                persist_node_state(bridge, "C_bridge", src.node_id)

        # Energy transfers (simplified)
        if pressure_b > OUTER_FAILOVER_CURV and self.energy["A"] > 200:
            transfer = self.energy["A"] * 0.07
            self.energy["A"] -= transfer
            self.energy["B"] += transfer

    def _visualize_torus(self):
        fig = plt.figure(figsize=(11, 9))
        ax = fig.add_subplot(111, projection='3d')
        ax.set_title(f"Tordial-GS Triple Ring Manifold — Tick {self.current_tick}")

        def plot_ring(nodes, radius, color_base):
            for node in nodes:
                m = gs_sweep.compute_gs(node.d, node.r)
                theta = node.drift_phase
                x = radius * math.cos(theta)
                y = radius * math.sin(theta)
                z = 0.3 * math.sin(3 * theta)  # slight toroidal twist
                size = 20 + m.kappa_GS_T * 4
                ax.scatter(x, y, z, s=size, c=color_base, alpha=0.85)

        plot_ring(self.nodes_a, 1.0, 'blue')
        plot_ring(self.nodes_b, 1.8, 'red')
        plot_ring(self.nodes_c, 1.4, 'green')

        plt.show(block=False)
        plt.pause(0.15)
        plt.close()

    def execute_heavy_load_cycle(self, system_load: float = 1.0):
        self.current_tick += 1

        # Ring A
        sa = self._ring_avg_sigma(self.nodes_a)
        ka = self._ring_avg_kappa(self.nodes_a)
        da, ra = self.governor_a.step(sa)
        pa, ra_res = self.curv_a.compute(sa, ka, self.energy["A"], self.ler["A"], len(self.nodes_a))
        for n in self.nodes_a:
            n.compute_and_update_gs(pa, ra_res)
            n.apply_governor_correction(da, ra)
        self._attempt_spawning(self.nodes_a, "A", self.energy["A"], self._ring_health(self.nodes_a))
        self._apply_error_correction(self.nodes_a)
        self.anyons_a, self.ler["A"] = self._update_anyons(self.nodes_a)  # type: ignore
        self.energy["A"] += 0.6 * (12 + 0.8 * ka) - len(self.nodes_a) * 0.11

        # Ring B (similar pattern)
        sb = self._ring_avg_sigma(self.nodes_b)
        kb = self._ring_avg_kappa(self.nodes_b)
        db, rb = self.governor_b.step(sb)
        pb, rb_res = self.curv_b.compute(sb, kb, self.energy["B"], self.ler["B"], len(self.nodes_b))
        for n in self.nodes_b:
            n.compute_and_update_gs(pb, rb_res)
            n.apply_governor_correction(db, rb)
        self._attempt_spawning(self.nodes_b, "B", self.energy["B"], self._ring_health(self.nodes_b))
        self._apply_error_correction(self.nodes_b)
        self.anyons_b, self.ler["B"] = self._update_anyons(self.nodes_b)  # type: ignore
        self.energy["B"] += 0.4 * (12 + 0.8 * kb) - len(self.nodes_b) * 0.11

        # Ring C
        sc = self._ring_avg_sigma(self.nodes_c)
        kc = self._ring_avg_kappa(self.nodes_c)
        dc, rc = self.governor_c.step(sc)
        pc, rc_res = self.curv_c.compute(sc, kc, self.energy["C"], self.ler["C"], len(self.nodes_c))
        for n in self.nodes_c:
            n.compute_and_update_gs(pc, rc_res)
            n.apply_governor_correction(dc, rc)
        self._attempt_spawning(self.nodes_c, "C", self.energy["C"], self._ring_health(self.nodes_c))
        self._apply_error_correction(self.nodes_c)
        self.anyons_c, self.ler["C"] = self._update_anyons(self.nodes_c)  # type: ignore
        self.energy["C"] += 0.25 * (12 + 0.8 * kc) - len(self.nodes_c) * 0.09

        # Curvature Coupling
        pa += CURV_COUPLING[("B","A")] * pb + CURV_COUPLING[("C","A")] * pc
        pb += CURV_COUPLING[("A","B")] * pa + CURV_COUPLING[("C","B")] * pc
        pc += CURV_COUPLING[("A","C")] * pa + CURV_COUPLING[("B","C")] * pb

        self._cross_ring_failover()

        # Telemetry
        if self.current_tick % 10 == 0 or self.current_tick < 20:
            ha = self._ring_health(self.nodes_a)
            hb = self._ring_health(self.nodes_b)
            hc = self._ring_health(self.nodes_c)
            total = len(self.nodes_a) + len(self.nodes_b) + len(self.nodes_c)
            print(f"[{self.current_tick:3d}] A:{len(self.nodes_a):3d} κ={ka:5.2f} H={ha:5.1f} | "
                  f"B:{len(self.nodes_b):3d} κ={kb:5.2f} H={hb:5.1f} | "
                  f"C:{len(self.nodes_c):3d} κ={kc:5.2f} H={hc:5.1f} | total={total}")

        if self.current_tick % 25 == 0:
            self._visualize_torus()


# =============================================================================
# RUNNER
# =============================================================================
if __name__ == "__main__":
    print("[+] Tordial–GS Manifold v15 FIXED — Triple Ring with Density Control + Torus Viz\n")
    matrix = TripleRingTordialMatrix(node_count=12)

    for cycle in range(250):
        matrix.execute_heavy_load_cycle(1.0 + 0.35 * math.sin(cycle / 6.0))

    print("\n[+] Run complete. Triple-ring manifold is structurally open.")