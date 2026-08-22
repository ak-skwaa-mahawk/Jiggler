#!/usr/bin/env python3
import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.expanduser("~/Tordial-GS-_Manifold/tools"))
sys.path.insert(0, os.path.expanduser("~"))

from udp_listener import ToroidalGSManifold
from burst_engine import BurstEngine

class TestToroidalManifoldInvariants:
    def setup_method(self):
        self.manifold = ToroidalGSManifold(major_radius=2.0, minor_radius=0.75)

    def test_embedding_dimensions_and_invariants(self):
        u, v, t = 1.292748, 0.155354, 0.5
        state_4d = self.manifold.embed_torus_to_4d(u, v, time_w=t)
        
        assert state_4d.shape == (4,)
        assert state_4d[3] == pytest.approx(t, rel=1e-5)
        
        # Verify torus distance invariant: (sqrt(x^2 + y^2) - R)^2 + z^2 == r^2
        x, y, z = state_4d[0], state_4d[1], state_4d[2]
        radial_dist = np.sqrt(x**2 + y**2)
        surface_dist_sq = (radial_dist - self.manifold.R)**2 + z**2
        assert surface_dist_sq == pytest.approx(self.manifold.r**2, rel=1e-4)

    def test_dynamic_null_and_zero_projection(self):
        u, v = 1.292748, 0.155354
        state_4d = self.manifold.embed_torus_to_4d(u, v, time_w=0.0)
        
        self.manifold.dynamic_null(state_4d)
        assert self.manifold.is_calibrated is True
        
        p3d, ndc = self.manifold.slice_and_project(state_4d, damping=1.0)
        np.testing.assert_allclose(p3d, [0.0, 0.0, 0.0], atol=1e-6)
        np.testing.assert_allclose(ndc, [0.0, 0.0], atol=1e-6)

    def test_ndc_strict_boundedness(self):
        # Stress test extreme coordinate inputs across full 2pi sweep
        for u in np.linspace(-10.0, 10.0, 50):
            for v in np.linspace(-10.0, 10.0, 50):
                state_4d = self.manifold.embed_torus_to_4d(u, v, time_w=1.0)
                _, ndc = self.manifold.slice_and_project(state_4d, damping=1.0)
                assert -1.0 <= ndc[0] <= 1.0
                assert -1.0 <= ndc[1] <= 1.0

    def test_lyapunov_damping_monotonicity(self):
        d_stable = self.manifold.compute_lyapunov_damping(-7.683965, delta_t=0.01)
        d_neutral = self.manifold.compute_lyapunov_damping(0.0, delta_t=0.01)
        d_chaotic = self.manifold.compute_lyapunov_damping(2.500000, delta_t=0.01)
        
        assert 0.0 < d_stable < 1.0
        assert d_neutral == 1.0
        assert d_chaotic > 1.0

class TestBurstEngineBackpressure:
    def setup_method(self):
        self.engine = BurstEngine(strain_threshold=75.0, burst_budget_sats=500)

    def test_nominal_dispatch(self):
        result = self.engine.evaluate_node_telemetry("NODE_1", strain_percent=50.0, vitality_score=1.0, lyapunov_exp=-7.68)
        assert result["status"] == "SUCCESS"
        assert result["action"] == "DISPATCH_BURST"
        assert result["allocated_budget_sats"] == 500

    def test_chaotic_choke_trigger(self):
        result = self.engine.evaluate_node_telemetry("NODE_CHAOS", strain_percent=50.0, vitality_score=1.0, lyapunov_exp=2.50)
        assert result["status"] == "THROTTLED_CHAOTIC"
        assert result["action"] == "CHOKE_BURST_EMISSION"
        assert result["allocated_budget_sats"] < 500
