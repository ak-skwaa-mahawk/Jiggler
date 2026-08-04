#!/usr/bin/env python3
import numpy as np

class OctagonalFPTAgent:
    def __init__(self):
        self.phase_bias = 0.088

    def compute_phase_step(self, current_state: np.ndarray, task_vector: np.ndarray) -> dict:
        state = np.array(current_state, dtype=np.float32)
        task = np.array(task_vector, dtype=np.float32)

        # Execute mass-preserving state optimization step
        stabilized_state = np.maximum(state + (task * self.phase_bias), 0.0)
        magnitude = np.sum(stabilized_state)
        
        final_state = stabilized_state / magnitude if magnitude > 0 else np.zeros_like(state)
        calculated_energy = float(15.0 * np.linalg.norm(final_state - state)**2)

        return {
            "state": final_state.tolist(),
            "energy": calculated_energy
        }
