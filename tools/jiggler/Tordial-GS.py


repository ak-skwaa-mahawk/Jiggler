import math
import yaml
import argparse
import numpy as np
import time
from typing import Dict
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter

# Load config
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

t = config["tordial"]
g = config["governance"]
s = config["simulation"]
sw = config["sweep"]


class GSSweep:
    def __init__(self):
        self.phi_op = t["phi_op"]
        self.gear = t["gear_shift_correction"]

    def compute_gs(self, d: int, r: int) -> Dict:
        denom = 4 * self.phi_op * self.gear
        sigma = r - (d ** 2) / denom
        if sigma <= 0:
            return {"d": d, "r": r, "sigma_T": 0.0, "kappa_GS_T": 0.0, "band": "SUBCRITICAL"}
        
        kappa = sigma / d
        band = "GOLDILOCKS" if (5.0 <= kappa <= 8.5 and sigma >= 95) else \
               "DEEP_GS" if kappa > 8.5 else \
               "MARGINAL" if kappa >= 3.2 else "SUBCRITICAL"
        
        return {"d": d, "r": r, "sigma_T": round(sigma, 4), "kappa_GS_T": round(kappa, 4), "band": band}


class TordialNode:
    def __init__(self, d: int, r: int):
        self.OMEGA_RADS = 2 * math.pi * t["base_frequency_hz"]
        self.TAU_3D = 2 * t["pi_3d"]
        self.CHASE_RATIO_TAU = self.TAU_3D / t["phi_op"]
        self.d = d
        self.r = r

    def run_step(self, t_seconds: float) -> Dict:
        phase = (self.OMEGA_RADS * t_seconds) % self.TAU_3D
        coupling = GSSweep().compute_gs(self.d, self.r)
        return {
            "raw_phase_rads": phase,
            "chase_lock_status": "LOCKED" if phase < self.CHASE_RATIO_TAU else "DRIFTING",
            "coupling_telemetry": coupling
        }


# The rest of the class (DualRingTordialMatrix) remains functionally the same as v8,
# but now pulls constants from config. For brevity, the full class is omitted here but uses:
# g["pid"], s["sleep_seconds"], etc.

# ... (keep the full DualRingTordialMatrix from previous version, just replace hardcoded values with config)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tordial-GS Manifold v8")
    parser.add_argument("--nodes", type=int, default=config["simulation"]["default_nodes"])
    parser.add_argument("--cycles", type=int, default=config["simulation"]["default_cycles"])
    parser.add_argument("--video", type=str, default=None)
    parser.add_argument("--analysis", action="store_true")
    args = parser.parse_args()

    # ... run logic as before