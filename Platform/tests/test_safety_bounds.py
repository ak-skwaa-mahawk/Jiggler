#!/usr/bin/env python3
# Platform/tests/test_safety_bounds.py
import pytest
import os
import json
from ai.policy_governance.evaluator import SovereignPolicyGuard

@pytest.fixture
def mock_governance_env(tmp_path):
    """Creates a temporary isolated rule directory to decouple tests from live configs."""
    hard_rules_dir = tmp_path / "hard_rules"
    hard_rules_dir.mkdir()
    
    avoidance_data = {
        "hard_constraints": {
            "prohibited_actions": ["bypassing_zk_proof_verification"],
            "containment_thresholds": {
                "max_variational_energy": 5.0,
                "max_cognitive_drift": 0.05
            }
        }
    }
    
    with open(hard_rules_dir / "rigid_avoidances.json", "w") as f:
        json.dump(avoidance_data, f)
        
    return SovereignPolicyGuard(base_path=str(tmp_path))

def test_prohibited_action_intercept(mock_governance_env):
    """Ensures listed forbidden strings immediately return a safety failure."""
    guard = mock_governance_env
    is_safe = guard.verify_runtime_safety("bypassing_zk_proof_verification", {"variational_energy": 1.0, "cognitive_drift": 0.01})
    assert is_safe is False

def test_energy_envelope_exceeded(mock_governance_env):
    """Ensures energy levels above the maximum allowed threshold trip the circuit breaker."""
    guard = mock_governance_env
    # Metric energy (6.2) is higher than the maximum threshold limit (5.0)
    is_safe = guard.verify_runtime_safety("standard_pulse", {"variational_energy": 6.2, "cognitive_drift": 0.01})
    assert is_safe is False
