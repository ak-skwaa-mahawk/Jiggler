#!/usr/bin/env python3
# Platform/tests/test_core_math.py
import pytest
import numpy as np
from core.octagonal_fpt_agent import OctagonalFPTAgent

def test_mass_preservation_and_normalization():
    """Verifies that step optimization output vectors are consistently normalized to a sum of 1.0."""
    agent = OctagonalFPTAgent()
    
    # Define arbitrary valid initial state and highly volatile task bursts
    initial_state = np.array([0.5, 0.2, 0.3], dtype=np.float32)
    volatile_task = np.array([2.5, -1.8, 0.9], dtype=np.float32)
    
    output = agent.compute_phase_step(initial_state, volatile_task)
    final_state = output["state"]
    
    # The output array must sum precisely to 1.0 (mass preservation)
    assert pytest.approx(sum(final_state), rel=1e-5) == 1.0
    assert all(x >= 0.0 for x in final_state), "Negative state energy leak detected"

def test_ground_state_fallback_on_zero_magnitude():
    """Verifies handling of null optimization states to prevent divide-by-zero errors."""
    agent = OctagonalFPTAgent()
    
    initial_state = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    task_vector = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    
    output = agent.compute_phase_step(initial_state, task_vector)
    assert output["state"] == [0.0, 0.0, 0.0]
    assert output["energy"] == 0.0
