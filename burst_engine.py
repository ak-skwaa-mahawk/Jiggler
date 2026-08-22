#!/usr/bin/env python3
import time
import logging
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class BurstEngine:
    def __init__(self, strain_threshold=75.0, burst_budget_sats=500, default_lyapunov=-7.683965):
        self.strain_threshold = strain_threshold
        self.base_burst_budget = burst_budget_sats
        self.current_lyapunov = default_lyapunov
        self.total_evaluations = 0
        self.throttled_events = 0

    def update_lyapunov_state(self, lyapunov_exp):
        self.current_lyapunov = float(lyapunov_exp)

    def calculate_stability_multiplier(self, delta_t=0.01):
        if self.current_lyapunov < 0:
            return float(np.exp(self.current_lyapunov * delta_t))
        return float(1.0 + (self.current_lyapunov * delta_t))

    def evaluate_node_telemetry(self, node_id, strain_percent, vitality_score, lyapunov_exp=None):
        self.total_evaluations += 1
        if lyapunov_exp is not None:
            self.update_lyapunov_state(lyapunov_exp)

        mult = self.calculate_stability_multiplier()
        effective_strain = strain_percent * (1.0 / max(mult, 0.05)) if self.current_lyapunov < 0 else strain_percent * mult

        is_divergent = self.current_lyapunov > 0.0
        is_overstrained = effective_strain >= self.strain_threshold

        if is_divergent:
            self.throttled_events += 1
            allocated_budget = int(self.base_burst_budget * max(0.0, 1.0 - (self.current_lyapunov * 0.1)))
            status = "THROTTLED_CHAOTIC"
            action = "CHOKE_BURST_EMISSION"
        elif is_overstrained:
            self.throttled_events += 1
            allocated_budget = 0
            status = "THROTTLED_OVERSTRAINED"
            action = "BACKOFF_RETRY"
        else:
            allocated_budget = int(self.base_burst_budget * vitality_score)
            status = "SUCCESS"
            action = "DISPATCH_BURST"

        result = {
            "status": status,
            "action": action,
            "node_id": node_id,
            "raw_strain": round(float(strain_percent), 2),
            "effective_strain": round(float(effective_strain), 2),
            "vitality_score": round(float(vitality_score), 4),
            "lyapunov_exp": round(float(self.current_lyapunov), 6),
            "allocated_budget_sats": allocated_budget,
            "timestamp": time.time()
        }

        if status != "SUCCESS":
            logging.warning(
                f"⚠️  [BURST THROTTLE]: Node={node_id} | State={status} | "
                f"EffStrain={effective_strain:.1f}% | Lyap={self.current_lyapunov:.3f} | Budget={allocated_budget} sats"
            )
        else:
            logging.info(
                f"✅ [BURST DISPATCH]: Node={node_id} | EffStrain={effective_strain:.1f}% | "
                f"Budget={allocated_budget} sats"
            )

        return result
