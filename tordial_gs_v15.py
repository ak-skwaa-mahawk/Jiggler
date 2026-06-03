cat << 'EOF' > tordial_gs_v15_fixed.py
"""
tordial_gs_v15_fixed.py
Tordial–GS Manifold v15 Fixed — Bounded Triple-Ring Architecture
"""

import math
import yaml
import numpy as np
import random
import os
import sqlite3
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

try:
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    t = config["tordial"]
except Exception:
    t = {
        "phi_op": 1.65036, "gear_shift_correction": 1.04, "pi_3d": 3.20442315,
        "base_frequency_hz": 60.0, "coupling_A_to_B": 0.1, "coupling_B_to_A": 0.1,
        "coupling_A_to_C": 0.1, "coupling_C_to_A": 0.1, "coupling_B_to_C": 0.1, "coupling_C_to_B": 0.1
    }

PHI_OP: float = float(t["phi_op"])
GEAR_SHIFT: float = float(t.get("gear_shift_correction", 1.04))
PI_3D: float = float(t["pi_3d"])
BASE_HZ: float = float(t["base_frequency_hz"])

MAX_NODES_PER_RING = int(t.get("max_nodes_per_ring", 380))
VIZ_UPDATE_INTERVAL = int(t.get("viz_update_interval", 25))
VIZ_ENABLED = bool(t.get("viz_enabled", True))

GOV_A_TARGET = float(t.get("governor_a_target_sigma", 135.0))
GOV_B_TARGET = float(t.get("governor_b_target_sigma", 78.0))
GOV_C_TARGET = float(t.get("governor_c_target_sigma", 108.0))

print(f"[+] Loaded Config with Safety Bounds | Max Nodes/Ring={MAX_NODES_PER_RING}")

class TordialAgentNode:
    TAU_3D: float = 2.0 * 3.20442315
    def __init__(self, d: int, r: int, node_id: int):
        self.node_id = node_id; self.d = d; self.r = r; self.load = 0.0

class OpenTordialAgentNode(TordialAgentNode):
    def __init__(self, d: int, r: int, node_id: int, x: float = 0.0, y: float = 0.0):
        super().__init__(d, r, node_id)
        self.drift_phase = (x + y) % self.TAU_3D
        self.sigma_T: float = 0.0
        self._denom = 4.0 * PHI_OP * GEAR_SHIFT

    def compute_and_update_gs(self, curvature_pressure: float, resonance: float) -> float:
        # SAFETY BOUND 1: Clamp environmental inputs to avoid extreme multiplier spikes
        curvature_pressure = max(0.0, min(1.5, curvature_pressure))
        resonance = max(0.0, min(1.0, resonance))

        if curvature_pressure > 0.6:
            # SAFETY BOUND 2: Cap max structural shift per execution tick
            delta_d = max(1, int(resonance * 0.35 + self.drift_phase * 0.1))
            self.d += min(3, delta_d) # Never allow a tick increment > 3
            if resonance > 0.4 and random.random() < 0.45: 
                self.r += 1

        # SAFETY BOUND 3: Absolute Hard Saturation Clamps for node parameters
        self.d = max(4, min(150, self.d))
        self.r = max(12, min(500, self.r))

        self.sigma_T = self.r - (self.d ** 2 / (self._denom + self.drift_phase * 0.08))
        self.drift_phase = (self.drift_phase + 0.017) % self.TAU_3D
        return self.sigma_T

    def apply_governor_correction(self, delta_d: int, delta_r: int) -> None:
        # SAFETY BOUND 4: Prevent Governor feedback from crushing or over-inflating geometry
        self.d = max(4, min(150, self.d + delta_d))
        self.r = max(12, min(500, self.r + delta_r))

DB_PATH = "tordial_manifold.db"
def _ensure_db():
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS nodes (
        node_id INTEGER, ring TEXT, d INTEGER, r INTEGER, sigma_T REAL,
        drift_phase REAL, fission_count INTEGER, parent_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit(); conn.close()

def persist_node_state(node: OpenTordialAgentNode, ring: str = "A"):
    if not os.path.exists(DB_PATH): _ensure_db()
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("INSERT INTO nodes (node_id, ring, d, r, sigma_T, drift_phase, fission_count, parent_id) VALUES (?,?,?,?,?,?,0,NULL)",
        (node.node_id, ring, node.d, node.r, node.sigma_T, node.drift_phase))
    conn.commit(); conn.close()

class CurvatureField:
    def __init__(self): self.last_pressure = 0.0; self.last_resonance = 0.0
    def compute(self, avg_sigma: float, avg_kappa: float, node_count: int) -> Tuple[float, float]:
        k_norm = max(0.0, min(1.0, avg_kappa / 12.0))
        bp = 0.45 * k_norm + 0.20 * max(0.0, avg_sigma / 500.0)
        pressure = max(0.0, min(1.25, bp + max(0.0, min(0.3, (node_count - 24) / 80.0))))
        resonance = max(0.0, min(1.0, 0.55 * k_norm))
        return pressure, resonance

class RingGovernor:
    def __init__(self, target_sigma: float = 120.0):
        self.target = target_sigma; self._integral = 0.0; self._prev_error = 0.0
    def step(self, current_sigma: float) -> Tuple[int, int]:
        error = self.target - current_sigma
        self._integral = max(-50.0, min(50.0, self._integral + error)) # PID Anti-Windup Clamp
        derivative = error - self._prev_error; self._prev_error = error
        u = 0.012 * error + 0.003 * self._integral + 0.006 * derivative
        delta_d = int(round(max(-1, min(1, u * 0.2))))
        delta_r = int(round(max(-4, min(4, u * 0.8))))
        return delta_d, delta_r

class TripleRingTordialMatrix:
    def __init__(self, node_count: int = 12):
        self.current_tick = 0
        self.curv_a = CurvatureField(); self.curv_b = CurvatureField(); self.curv_c = CurvatureField()
        self.nodes_a: List[OpenTordialAgentNode] = []
        self.nodes_b: List[OpenTordialAgentNode] = []
        self.nodes_c: List[OpenTordialAgentNode] = []
        self.governor_a = RingGovernor(GOV_A_TARGET)
        self.governor_b = RingGovernor(GOV_B_TARGET)
        self.governor_c = RingGovernor(GOV_C_TARGET)
        _ensure_db()
        self._seed_rings(node_count)

    def _seed_rings(self, node_count: int):
        self.rings = {"A": self.nodes_a, "B": self.nodes_b, "C": self.nodes_c}
        for i in range(node_count):
            r_assign = ["A", "B", "C"][i % 3]
            node = OpenTordialAgentNode(d=6, r=18, node_id=i, x=float(i)*0.5, y=float(i)*0.2)
            self.rings[r_assign].append(node)
            persist_node_state(node, ring=r_assign)

    def execute_heavy_load_cycle(self, system_load: float = 1.0):
        self.current_tick += 1
        for r_name, nodes in [("A", self.nodes_a), ("B", self.nodes_b), ("C", self.nodes_c)]:
            if not nodes: continue
            avg_sigma = sum(n.sigma_T for n in nodes) / len(nodes)
            avg_kappa = sum((n.sigma_T / n.d) for n in nodes if n.d > 0) / len(nodes)
            f_obj = getattr(self, f"curv_{r_name.lower()}")
            p, r = f_obj.compute(avg_sigma, avg_kappa, len(nodes))
            gov = getattr(self, f"governor_{r_name.lower()}")
            dd, dr = gov.step(avg_sigma)
            for n in nodes: 
                n.apply_governor_correction(dd, dr)
                n.compute_and_update_gs(p, r)

if __name__ == "__main__":
    matrix = TripleRingTordialMatrix(node_count=12)
    print(f"[+] Matrix seeded | Rings A/B/C | {len(matrix.nodes_a + matrix.nodes_b + matrix.nodes_c)} nodes total")

    for tick in range(50):
        matrix.execute_heavy_load_cycle(system_load=1.0)
        if tick % 10 == 0:
            total = matrix.nodes_a + matrix.nodes_b + matrix.nodes_c
            avg_s = sum(n.sigma_T for n in total) / len(total)
            print(f"[tick {tick:03d}] nodes={len(total)} avg_sigma_T={avg_s:.4f}")
        time.sleep(0.01)

    print("[+] Run complete")
EOF
dos2unix tordial_gs_v15_fixed.py
