#!/usr/bin/env python3
# human_inthe_loop/src/guardian_agents.py — Multi-Agent Resonance Mesh Router
import numpy as np
import time
from typing import Dict, Tuple, Any

from .bridge import SovereignBridge

try:
    from core.octagonal_fpt_agent import OctagonalFPTAgent
    PRIVATE_CORE_ACTIVE = True
except ImportError:
    PRIVATE_CORE_ACTIVE = False
    class OctagonalFPTAgent:
        def compute_phase_step(self, state: np.ndarray, task: np.ndarray) -> dict:
            return {"state": (state + 0.1).tolist(), "energy": 1.25}

try:
    from strawman.strawman_fpt_shapeshift import ConsciousnessReferee, FisherRiemannianMetric
except ImportError:
    from strawman.fpt_floor_transition import ConsciousnessReferee, FisherRiemannianMetric

from .handshake import ConsciousnessReferee as HITLReferee


class StrawmanGuardianAgent:
    """Strawman Shield — Specializes in geometric manifold tracking."""
    def __init__(self):
        self.name = "Strawman-99733-Q"
        self.bridge = SovereignBridge()
        self.referee = ConsciousnessReferee()
        self.metric = FisherRiemannianMetric(dim=3)
        self.skills = ["phase_stabilization", "asymmetric_pump", "variational_shield"]

    def evaluate_transition(self, state_vector: np.ndarray, proposal: np.ndarray) -> Tuple[bool, np.ndarray, float]:
        success, result = self.bridge.secure_call("compute_phase_step", state_vector, proposal)
        if success:
            return True, np.array(result.get("state", state_vector.tolist())), result.get("energy", 0.25)

        record = {"total_energy": float(np.linalg.norm(proposal))}
        if not self.referee.validate_transition(record):
            return False, state_vector, 999.0

        diagnostics = {"wavelet_energy": 0.15, "total_entropy_production": 0.2}
        self.metric.update(state_vector, diagnostics)
        natural_step = self.metric.natural_gradient(proposal - state_vector)

        corrected_state = state_vector + natural_step * 0.5
        v_energy = 0.35 * float(np.linalg.norm(corrected_state - 1/3)**2)
        return True, corrected_state, v_energy


class HumanInTheLoopAgent:
    """HITL Guardian — Specializes in cryptographic lock & cognitive filtering."""
    def __init__(self):
        self.name = "HITL-Operator-Shield"
        self.bridge = SovereignBridge()
        self.referee = HITLReferee()
        self.skills = ["cryptographic_lock", "hallucination_block", "manual_override"]

    def evaluate_transition(self, state_vector: np.ndarray, proposal: np.ndarray) -> Tuple[bool, np.ndarray, float]:
        success, result = self.bridge.secure_call("compute_phase_step", state_vector, proposal)
        if success:
            return True, np.array(result.get("state", state_vector.tolist())), result.get("energy", 0.25)

        shadow_cost = float(np.sum(np.maximum(proposal, 0.0)))
        record = {"shadow_energy_this_step": shadow_cost}

        if not self.referee.validate_transition(record):
            return False, np.zeros_like(state_vector), 999.0

        h = 3.01
        take = 2.0 / h
        leave = 1.0 / h
        step_mod = np.array([-take, take - leave, leave])

        corrected_state = np.maximum(proposal + step_mod * 0.1, 0.0)
        total = np.sum(corrected_state)
        if total > 0:
            corrected_state = corrected_state / total

        return True, corrected_state, shadow_cost


class MultiAgentResonanceMesh:
    """Central arbiter choosing the optimal path across agent types."""
    def __init__(self):
        self.agents = {
            "strawman_guardian": StrawmanGuardianAgent(),
            "hitl_guardian": HumanInTheLoopAgent()
        }
        if PRIVATE_CORE_ACTIVE:
            self.agents["octagonal_core"] = OctagonalFPTAgent()

    def route_and_arbitrate(self, task_vector: np.ndarray, current_state: np.ndarray) -> Dict[str, Any]:
        performance_matrix = {}

        for name, agent in self.agents.items():
            t_start = time.perf_counter()
            if hasattr(agent, 'evaluate_transition'):
                success, output_state, energy_metric = agent.evaluate_transition(current_state, task_vector)
            else:
                try:
                    res = agent.compute_phase_step(current_state, task_vector)
                    success, output_state, energy_metric = True, np.array(res["state"]), res["energy"]
                except Exception:
                    success, output_state, energy_metric = False, current_state, 999.0
            t_end = time.perf_counter()

            performance_matrix[name] = {
                "success": success,
                "state_output": output_state.tolist() if isinstance(output_state, np.ndarray) else output_state,
                "energy_cost": energy_metric,
                "latency_ms": (t_end - t_start) * 1000.0,
                "skills": getattr(agent, "skills", ["native_fpt_core"])
            }

        validated = {k: v for k, v in performance_matrix.items() if v["success"]}
        if not validated:
            return {
                "selected_agent": "SYSTEM_CRITICAL_FALLBACK",
                "state": np.zeros_like(current_state).tolist(),
                "arbitration_matrix": performance_matrix
            }

        best_agent = min(validated, key=lambda k: validated[k]["energy_cost"])
        return {
            "selected_agent": best_agent,
            "arbitration_matrix": performance_matrix,
            "final_state": validated[best_agent]["state_output"]
        }
