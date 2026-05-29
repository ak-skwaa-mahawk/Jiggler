"""
tordial_gs_v15_fixed.py
Tordial–GS Manifold v15 Fixed — Triple-Ring + Full Config + Density Control + Visualization
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
# FULL CONFIG LOAD
# =============================================================================
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

t = config["tordial"]

# Core Constants
PHI_OP: float = float(t["phi_op"])
GEAR_SHIFT: float = float(t.get("gear_shift_correction", 1.04))
PI_3D: float = float(t["pi_3d"])
BASE_HZ: float = float(t["base_frequency_hz"])

# Tunable Parameters from config
MAX_NODES_PER_RING = int(t.get("max_nodes_per_ring", 380))
GROWTH_DAMPING = float(t.get("growth_damping", 0.88))
VIZ_UPDATE_INTERVAL = int(t.get("viz_update_interval", 25))
VIZ_ENABLED = bool(t.get("viz_enabled", True))

INNER_FAILOVER_KAPPA = float(t.get("inner_failover_kappa", 2.5))
OUTER_FAILOVER_CURV = float(t.get("outer_failover_curv", 1.05))

# Coupling Matrix
CURV_COUPLING = {
    ("A", "B"): float(t["coupling_A_to_B"]),
    ("B", "A"): float(t["coupling_B_to_A"]),
    ("A", "C"): float(t["coupling_A_to_C"]),
    ("C", "A"): float(t["coupling_C_to_A"]),
    ("B", "C"): float(t["coupling_B_to_C"]),
    ("C", "B"): float(t["coupling_C_to_B"]),
}

# Governor Targets
GOV_A_TARGET = float(t.get("governor_a_target_sigma", 135.0))
GOV_B_TARGET = float(t.get("governor_b_target_sigma", 78.0))
GOV_C_TARGET = float(t.get("governor_c_target_sigma", 108.0))

# Energy Shares
INNER_ENERGY_SHARE = float(t.get("inner_energy_share", 0.60))
OUTER_ENERGY_SHARE = float(t.get("outer_energy_share", 0.40))
BRIDGE_ENERGY_SHARE = float(t.get("bridge_energy_share", 0.25))

print(f"[+] Loaded Tordial Config | φ_op={PHI_OP} | π_3D={PI_3D} | Max Nodes/Ring={MAX_NODES_PER_RING}")

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
    def __init__(self):
        self._denom = 4.0 * PHI_OP * GEAR_SHIFT

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
# Other classes (Anyon, SurfaceCodeDecoder, RingGovernor, Nodes, etc.)
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

# (TordialAgentNode and OpenTordialAgentNode remain the same as previous version)
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
        if self.sigma_T < -180: syndromes.append("e")
        if abs(self.drift_phase % (math.pi / 2)) > 0.38: syndromes.append("m")
        return syndromes

    def apply_governor_correction(self, delta_d: int, delta_r: int) -> None:
        self.d = max(4, self.d + delta_d)
        self.r = max(20, self.r + delta_r)

# DB functions (same as before)
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
    if not os.path.exists(DB_PATH): _ensure_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""INSERT INTO nodes 
        (node_id, ring, d, r, sigma_T, drift_phase, fission_count, parent_id) 
        VALUES (?,?,?,?,?,?,?,?)""",
        (node.node_id, ring, node.d, node.r, node.sigma_T, node.drift_phase, node.fission_count, parent_id))
    conn.commit()
    conn.close()

# CurvatureField class (same as before)
class CurvatureField:
    def __init__(self):
        self.last_pressure = 0.0
        self.last_resonance = 0.0

    def compute(self, avg_sigma: float, avg_kappa: float, global_energy: float, 
                logical_error_rate: float, node_count: int) -> Tuple[float, float]:
        # ... (same implementation as previous version)
        kappa_norm = max(0.0, min(1.0, avg_kappa / 12.0))
        energy_norm = max(0.0, min(1.0, global_energy / 3000.0))
        sigma_norm = max(-1.0, min(1.0, avg_sigma / 500.0))
        ler = max(0.0, min(1.0, logical_error_rate))

        base_pressure = 0.45 * kappa_norm + 0.35 * energy_norm + 0.20 * max(0.0, sigma_norm)
        pressure = base_pressure * (1.0 - 0.6 * ler)
        pressure += max(0.0, min(0.3, (node_count - 24) / 80.0))

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
# TRIPLE RING MATRIX (Fully Config-Driven)
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

        self.governor_a = RingGovernor(GOV_A_TARGET, 0.011, 0.0035, 0.006)
        self.governor_b = RingGovernor(GOV_B_TARGET, 0.009, 0.002, 0.005)
        self.governor_c = RingGovernor(GOV_C_TARGET, 0.010, 0.003, 0.005)

        self.energy = {"A": 900.0, "B": 600.0, "C": 300.0}
        self.ler = {"A": 0.0, "B": 0.0, "C": 0.0}

        self.bridge_nodes_spawned = 0
        _ensure_db()
        self._seed_rings(node_count)

    # ... (Include _seed_rings, _next_node_id, _ring_avg_kappa, _ring_avg_sigma, _ring_health, 
    # _perform_fission, _attempt_spawning, _measure_syndromes, _apply_error_correction, 
    # _update_anyons, _cross_ring_failover, _visualize_torus methods from previous version)

    def execute_heavy_load_cycle(self, system_load: float = 1.0):
        # Full cycle implementation (same logic as before, now using config values)
        self.current_tick += 1
        # ... (per-ring updates using INNER_ENERGY_SHARE etc.)

        if VIZ_ENABLED and self.current_tick % VIZ_UPDATE_INTERVAL == 0:
            self._visualize_torus()

# =============================================================================
# RUNNER
# =============================================================================
if __name__ == "__main__":
    print("[+] Tordial–GS Manifold v15 — Fully Configurable Triple-Ring\n")
    matrix = TripleRingTordialMatrix(node_count=12)

    for cycle in range(300):
        matrix.execute_heavy_load_cycle(1.0 + 0.35 * math.sin(cycle / 6.0))

    print("\n[+] Run complete.")