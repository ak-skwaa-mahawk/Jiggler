#!/usr/bin/env python3
# policy_governance/evaluator.py — Hard Direction & HITL Weight Interceptor
import json
import os
from typing import Dict, Tuple, Any

class SovereignPolicyGuard:
    def __init__(self, base_path: str = "policy_governance"):
        self.avoid_path = os.path.join(base_path, "hard_rules/rigid_avoidances.json")
        self.weights_path = os.path.join(base_path, "human_in_the_loop/weights_matrix.json")
        self.rules = self._load_json(self.avoid_path)
        self.weights = self._load_json(self.weights_path)

    def _load_json(self, path: str) -> dict:
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return {}

    def verify_safety_bounds(self, action_name: str, metrics: dict) -> bool:
        """Enforces absolute hardcoded avoidance rules."""
        # 1. Prohibited Actions Intercept
        if action_name in self.rules.get("hard_constraints", {}).get("prohibited_actions", []):
            return False
            
        # 2. Variational Thresholds Check
        thresholds = self.rules.get("hard_constraints", {}).get("containment_thresholds", {})
        if metrics.get("variational_energy", 0.0) > thresholds.get("max_variational_energy", 999.0):
            return False
            
        return True

    def evaluate_thought_pros_cons(self, observation_report: Dict[str, bool]) -> Tuple[float, str]:
        """
        Computes the weighted observation value for human-in-the-loop review.
        Fuses custom pro/con weights to generate a definitive confirmation score.
        """
        score = 0.0
        matrix = self.weights.get("evaluation_criteria", {})
        justification_log = []

        for criterion, state_is_positive in observation_report.items():
            if criterion in matrix:
                if state_is_positive:
                    weight = matrix[criterion]["pro_weight"]
                    score += weight
                    justification_log.append(f"(+) Verified {criterion}: {weight}")
                else:
                    weight = matrix[criterion]["con_weight"]
                    score += weight
                    justification_log.append(f"(-) Violated {criterion}: {weight}")

        decision = "APPROVE" if score >= 1.0 else "HALT_FOR_HUMAN_OVERRIDE"
        return score, " | ".join(justification_log) + f" -> STATUS: {decision}"

if __name__ == "__main__":
    guard = SovereignPolicyGuard()
    
    # Test a rogue agent behavior
    is_safe = guard.verify_safety_bounds("bypassing_zk_proof_verification", {"variational_energy": 1.2})
    print(f"Safety Bound Pass: {is_safe} (Expected: False)")

    # Simulate scoring a proposed network phase change
    simulated_observations = {
        "sovereignty_alignment": True,
        "computational_efficiency": True,
        "cryptographic_certainty": False
    }
    score, log_summary = guard.evaluate_thought_pros_cons(simulated_observations)
    print(f"\nHITL Score: {score:.2f}")
    print(f"Log: {log_summary}")
