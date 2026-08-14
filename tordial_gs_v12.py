# tordial_gs_v12.py
import math
import yaml
import numpy as np
from typing import Dict, List

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

t = config["tordial"]
t["base_frequency_hz"] = 79.79

class TordialAgentNode:
    """Node with tiny decision loop (Agent Mode)"""
    def __init__(self, d: int, r: int, node_id: int):
        self.node_id = node_id
        self.OMEGA_RADS = 2 * math.pi * t["base_frequency_hz"]
        self.TAU_3D = 2 * t["pi_3d"]
        self.CHASE_RATIO_TAU = self.TAU_3D / t["phi_op"]
        self.d = d
        self.r = r
        self.load = 0.0
        self.load_history = []   # for replay & charting
        self.decision = "STABLE"

    def make_decision(self, current_load: float, kappa: float) -> str:
        """Tiny per-node agent logic"""
        if current_load > 3.2 and kappa < 5.0:
            return "SHED"
        elif current_load > 2.0:
            return "THROTTLE"
        else:
            return "STABLE"

    def run_step(self, t_seconds: float, external_load: float = 1.0) -> Dict:
        phase = (self.OMEGA_RADS * t_seconds) % self.TAU_3D
        coupling = GSSweep().compute_gs(self.d, self.r)  # assume GSSweep exists
        self.load = external_load
        self.load_history.append(external_load)

        kappa = coupling.get("kappa_GS_T", 0)
        self.decision = self.make_decision(external_load, kappa)

        return {
            "node_id": self.node_id,
            "raw_phase_rads": phase,
            "chase_lock_status": "LOCKED" if phase < self.CHASE_RATIO_TAU else "DRIFTING",
            "coupling_telemetry": coupling,
            "load": external_load,
            "decision": self.decision,
            "load_history": self.load_history[-50:]   # last 50 ticks
        }