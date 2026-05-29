import math
import yaml
import numpy as np
import random
from typing import Dict, List, Set, Tuple
import sqlite3
import os

# =========================
# SURFACE CODE + ANYON
# =========================
class Anyon:
    def __init__(self, anyon_type: str, node_id: int, position: float):
        self.type = anyon_type
        self.node_id = node_id
        self.position = position
        self.lifetime = 0


class SurfaceCodeDecoder:
    def decode(self, syndromes: List[Tuple[int, str]]) -> List[Tuple[int, int]]:
        corrections = []
        unpaired = syndromes[:]
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


# =========================
# OPEN TORDIAL NODE
# =========================
class OpenTordialAgentNode(TordialAgentNode):
    def __init__(self, d: int, r: int, node_id: int, x: float = 0.0, y: float = 0.0):
        super().__init__(d, r, node_id)
        self.drift_phase = (x + y) % self.TAU_3D
        self.sigma_T = 0.0
        self.fission_count = 0
        self.quarantined = False
        self.high_kappa_streak = 0

    def compute_and_update_gs(self, curvature_pressure: float, resonance: float):
        if curvature_pressure > 0.6:
            delta_d = max(1, int(resonance * 0.35 + self.drift_phase * 0.1))
            self.d += delta_d
        if resonance > 0.4:
            self.r += 1 if random.random() < 0.45 else 0

        denom = 4 * t["phi_op"] * t.get("gear_shift_correction", 1.04) + self.drift_phase * 0.08
        self.sigma_T = self.r - (self.d ** 2 / denom)
        self.drift_phase = (self.drift_phase + 0.017) % self.TAU_3D
        return self.sigma_T

    def measure_syndrome(self) -> List[str]:
        syndromes = []
        if getattr(self, 'sigma_T', 0) < -180:
            syndromes.append('e')
        if abs(self.drift_phase % (math.pi / 2)) > 0.38:
            syndromes.append('m')
        return syndromes


# =========================
# SQLITE
# =========================
DB_PATH = "tordial_manifold.db"

def init_sqlite_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS nodes (node_id INTEGER PRIMARY KEY, d INTEGER, r INTEGER, sigma_T REAL, drift_phase REAL, fission_count INTEGER, parent_id INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def persist_node_state(node, parent_id=None):
    if not os.path.exists(DB_PATH):
        init_sqlite_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO nodes (node_id, d, r, sigma_T, drift_phase, fission_count, parent_id) VALUES (?, ?, ?, ?, ?, ?, ?)''', 
              (getattr(node, 'node_id', 0), getattr(node, 'd', 0), getattr(node, 'r', 0), 
               getattr(node, 'sigma_T', 0.0), getattr(node, 'drift_phase', 0.0), 
               getattr(node, 'fission_count', 0), parent_id))
    conn.commit()
    conn.close()


# =========================
# CONFIG & GS CORE
# =========================
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

t = config["tordial"]
t["base_frequency_hz"] = 79.79


class GSSweep:
    def __init__(self):
        self.PHI_OP = t["phi_op"]
        self.GEAR_SHIFT_CORRECTION = t.get("gear_shift_correction", 1.04)
        self._denom = 4 * self.PHI_OP * self.GEAR_SHIFT_CORRECTION

    def compute_gs(self, d: int, r: int) -> Dict[str, float]:
        sigma_T = r - (d ** 2) / self._denom
        if sigma_T <= 0:
            return {"sigma_T": 0.0, "kappa_GS_T": 0.0, "lambda_GS_T": 0.0, "rho_GS_T": 0.0}
        return {"sigma_T": sigma_T, "kappa_GS_T": sigma_T / d, "lambda_GS_T": math.sqrt(sigma_T), "rho_GS_T": math.sqrt(sigma_T) / d}


gs_sweep = GSSweep()


class TordialAgentNode:
    def __init__(self, d: int, r: int, node_id: int):
        self.node_id = node_id
        self.OMEGA_RADS = 2 * math.pi * t["base_frequency_hz"]
        self.TAU_3D = 2 * t["pi_3d"]
        self.CHASE_RATIO_TAU = self.TAU_3D / t["phi_op"]
        self.d = d
        self.r = r
        self.load = 0.0
        self.decision = "STABLE"
        self.load_history: List[float] = []

    def negotiate(self, peers_loads: List[float], my_kappa: float) -> str:
        avg_peer_load = np.mean(peers_loads) if peers_loads else 0.0
        if self.load > 3.5 and my_kappa < 5.5:
            return "REQUEST_SHED" if random.random() < 0.7 else "THROTTLE"
        if avg_peer_load > 0 and self.load > avg_peer_load * 1.6 and my_kappa > 6.0:
            return "OFFER_HELP"
        return "STABLE"

    def run_step(self, t_seconds: float, external_load: float, peers_loads: List[float]) -> Dict:
        phase = (self.OMEGA_RADS * t_seconds) % self.TAU_3D
        coupling = gs_sweep.compute_gs(self.d, self.r)
        self.load = external_load
        self.load_history.append(external_load)
        kappa = coupling.get("kappa_GS_T", 0.0)
        self.decision = self.negotiate(peers_loads, kappa)
        return {"node_id": self.node_id, "raw_phase_rads": phase, "chase_lock_status": "LOCKED" if phase < self.CHASE_RATIO_TAU else "DRIFTING", "coupling_telemetry": coupling, "load": external_load, "decision": self.decision, "kappa": kappa}


def gs_macro_feedback(d: int, r: int, drift_stress: float, curvature_stress: float, failover_flag: bool):
    S_macro = max(0.0, min(1.0, 0.6 * drift_stress + 0.4 * curvature_stress))
    S_stable = 1.0 - S_macro
    S_fail = 1.0 if failover_flag else 0.0
    new_d = max(4, int(round(d + 2 * S_macro + 4 * S_fail)))
    new_r = max(20, int(round(r + 20 * S_macro - 12 * S_stable + 40 * S_fail)))
    return new_d, new_r


# =========================
# MAIN MATRIX - ENHANCED INFINITE LOOPHOLE
# =========================
class DualRingTordialMatrix:
    def __init__(self, node_count: int = 12, agent_mode: bool = True):
        self.node_count = node_count
        self.agent_mode = agent_mode
        self.current_tick = 0
        self.anyons: List[Anyon] = []
        self.logical_error_rate = 0.0
        self.corrections_made = 0
        self.global_energy = 1500.0
        self.rings = 1
        self.decoder = SurfaceCodeDecoder()
        self.nodes_a: List[OpenTordialAgentNode] = []
        self._seed_nodes()

    def _seed_nodes(self):
        base_d, base_r = 42, 380
        for i in range(self.node_count):
            d_i = base_d + (i % 4) * 2
            r_i = base_r + (i % 4) * 16
            angle = (2 * math.pi * i) / self.node_count
            self.nodes_a.append(OpenTordialAgentNode(d_i, r_i, i, angle, angle))

    def _perform_node_fission(self, parent_node):
        parent_node.fission_count += 1
        child_id = len(self.nodes_a)
        child = OpenTordialAgentNode(parent_node.d + 1, parent_node.r + 1, child_id,
                                     parent_node.drift_phase + 0.1, parent_node.drift_phase + 0.1)
        self.nodes_a.append(child)
        persist_node_state(child, parent_id=parent_node.node_id)
        print(f"[FISSION] Node {parent_node.node_id} → {child_id} | σ_T={child.sigma_T:.3f}")

    def _attempt_node_spawning(self):
        """Enhanced κ-driven spawning with energy floor + scaling"""
        MIN_ENERGY_FLOOR = 420.0
        SPAWN_KAPPA_THRESHOLD = 8.0
        SPAWN_HEALTH_THRESHOLD = 62.0
        MIN_TICKS_ABOVE = 3

        spawned = 0
        avg_kappa = np.mean([gs_sweep.compute_gs(n.d, n.r).get("kappa_GS_T", 0) for n in self.nodes_a])

        for node in self.nodes_a[:]:
            if not isinstance(node, OpenTordialAgentNode):
                continue

            gs_data = gs_sweep.compute_gs(node.d, node.r)
            current_kappa = gs_data.get("kappa_GS_T", 0.0)

            if current_kappa > SPAWN_KAPPA_THRESHOLD:
                node.high_kappa_streak += 1
            else:
                node.high_kappa_streak = 0

            health = self.compute_manifold_health_score()

            if (node.high_kappa_streak >= MIN_TICKS_ABOVE and 
                health > SPAWN_HEALTH_THRESHOLD and 
                self.global_energy > MIN_ENERGY_FLOOR):

                prob = 0.25 + 0.06 * (current_kappa - 8.0)   # κ-scaled probability
                if random.random() < prob:
                    self._perform_node_fission(node)
                    spawned += 1

        if spawned > 0:
            print(f"[SPAWN] {spawned} new nodes (κ-boosted)")

        # Ring-level hierarchical spawning
        if len(self.nodes_a) > 35 and self.global_energy > 800 and avg_kappa > 9.5 and random.random() < 0.18:
            print(f"[RING SPAWN] New ring created! Total rings: {self.rings + 1}")
            self.rings += 1
            # Could expand to nodes_b or new structure in future

    def measure_syndromes(self) -> List[Tuple[int, str]]:
        syndromes = []
        for node in self.nodes_a:
            if isinstance(node, OpenTordialAgentNode):
                for s in node.measure_syndrome():
                    syndromes.append((node.node_id, s))
        return syndromes

    def apply_error_correction(self):
        syndromes = self.measure_syndromes()
        corrections = self.decoder.decode(syndromes)
        corrected = 0
        for n1, n2 in corrections:
            for node in self.nodes_a:
                if node.node_id in (n1, n2):
                    node.sigma_T = max(node.sigma_T, -50.0)
                    node.d = max(4, node.d - 1)
                    corrected += 1
        return corrected

    def compute_manifold_health_score(self) -> float:
        if not self.nodes_a:
            return 0.0
        avg_kappa = np.mean([gs_sweep.compute_gs(n.d, n.r).get("kappa_GS_T", 0) for n in self.nodes_a])
        return round((0.4 + min(avg_kappa / 12.0, 1.0) * 0.35 + 0.25 * 0.85) * 100, 2)

    def execute_heavy_load_cycle(self, system_load: float = 1.0):
        self.current_tick += 1

        for node in self.nodes_a:
            if isinstance(node, OpenTordialAgentNode):
                p = random.uniform(0.4, 1.2)
                r = random.uniform(0.2, 0.9)
                node.compute_and_update_gs(p, r)

            if getattr(node, 'sigma_T', 0) < -450:
                self._perform_node_fission(node)

        # Dynamic spawning (enhanced loophole)
        self._attempt_node_spawning()

        # Surface Code
        self.corrections_made = self.apply_error_correction()

        # Anyon tracking
        self.anyons = [Anyon(s[1], s[0], self.nodes_a[s[0]].drift_phase) for s in self.measure_syndromes()]
        for a in self.anyons:
            a.lifetime += 1

        wrapped = sum(1 for a in self.anyons if a.lifetime > 25)
        self.logical_error_rate = min(1.0, wrapped / max(1, len(self.anyons)) * 0.7) if self.anyons else 0.0

        # κ-boosted energy recovery
        avg_kappa = np.mean([gs_sweep.compute_gs(n.d, n.r).get("kappa_GS_T", 0) for n in self.nodes_a])
        self.global_energy += 12.0 + 0.8 * avg_kappa - len(self.nodes_a) * 0.11

        health = self.compute_manifold_health_score()
        print(f"[CYCLE {self.current_tick:3d}] Nodes: {len(self.nodes_a):3d} | Rings: {self.rings} | "
              f"Energy: {self.global_energy:7.1f} | LER: {self.logical_error_rate:.4f} | Health: {health:5.1f}")


# =========================
# RUNNER
# =========================
if __name__ == "__main__":
    print("[+] Tordial–GS Manifold v13 — Enhanced Infinite Loophole (Hierarchical + κ-Energy)\n")
    matrix = DualRingTordialMatrix(node_count=12, agent_mode=True)

    for cycle in range(200):
        matrix.execute_heavy_load_cycle(1.0 + 0.35 * math.sin(cycle / 6.0))

    print("\nRun complete. The manifold is now hierarchically open.")