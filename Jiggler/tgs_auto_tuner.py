python -c '
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Tuple, List, Dict, Any
import numpy as np

@dataclass
class PIDParams:
    k_p1: float; k_p2: float; k_d1: float; k_d2: float; k_i1: float; k_i2: float
    def as_matrix(self):
        return {"Kp": np.diag([self.k_p1, self.k_p2]), "Kd": np.diag([self.k_d1, self.k_d2]), "Ki": np.diag([self.k_i1, self.k_i2])}

@dataclass
class GSClampParams:
    kappa_max: float; lambda_clamp: float; lambda_gs: float

@dataclass
class TGSParams:
    pid: PIDParams; clamp: GSClampParams

@dataclass
class TGSProfile:
    params: TGSParams; J_total: float; J_macro: float; J_gs: float; J_gain: float

class TordialNode:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.Kp = np.eye(2); self.Kd = np.eye(2); self.Ki = np.eye(2)
        self.clamp = GSClampParams(1.0, 1.0, 1.0)
    def set_pid_gains(self, Kp, Kd, Ki):
        self.Kp, self.Kd, self.Ki = Kp, Kd, Ki
    def set_gs_clamp_params(self, clamp):
        self.clamp = clamp
    def linearize_macro(self):
        trace_damping = -1.0 - float(np.mean(np.diag(self.Kp)) + 0.5 * np.mean(np.diag(self.Kd)))
        determinant = 2.0 + float(np.mean(np.diag(self.Ki)))
        return np.array([[0.0, 1.0], [-determinant, trace_damping]], dtype=float)
    def simulate_macro_with_gs_input(self, g_norm, T, dt):
        return float(g_norm / (1.0 + float(np.mean(np.diag(self.Kp))) + self.clamp.lambda_clamp))
    def simulate_gs_with_macro_input(self, x_macro_norm, T, dt):
        return float(x_macro_norm / (1.0 + self.clamp.kappa_max + self.clamp.lambda_gs))

def estimate_gamma_macro(node, clamp, s_grid, T, dt):
    x_vals = []
    for s in s_grid:
        node.set_gs_clamp_params(clamp)
        x_vals.append(node.simulate_macro_with_gs_input(s, T, dt))
    return lambda s: float(np.interp(s, s_grid, x_vals))

def estimate_gamma_gs(node, clamp, s_grid, T, dt):
    g_vals = []
    for s in s_grid:
        node.set_gs_clamp_params(clamp)
        g_vals.append(node.simulate_gs_with_macro_input(s, T, dt))
    return lambda s: float(np.interp(s, s_grid, g_vals))

class TGSCost:
    def __init__(self, node_factory, base_config):
        self.node_factory = node_factory; self.base_config = base_config
        self.s_grid = np.linspace(0.1, 1.0, 6)
    def evaluate(self, params):
        node = self.node_factory(self.base_config)
        gains = params.pid.as_matrix()
        node.set_pid_gains(gains["Kp"], gains["Kd"], gains["Ki"])
        node.set_gs_clamp_params(params.clamp)
        A = node.linearize_macro()
        J_macro = max(0.0, np.max(np.real(np.linalg.eigvals(A))) - 0.1)
        gamma = estimate_gamma_macro(node, params.clamp, self.s_grid, 5.0, 0.01)
        gamma_gs = estimate_gamma_gs(node, params.clamp, self.s_grid, 5.0, 0.01)
        J_gs = sum(max(0.0, float(gamma(gamma_gs(s)) - s)) for s in self.s_grid)
        theta = np.array([params.pid.k_p1, params.pid.k_p2, params.pid.k_d1, params.pid.k_d2, params.pid.k_i1, params.pid.k_i2, params.clamp.kappa_max, params.clamp.lambda_clamp, params.clamp.lambda_gs])
        return J_macro + J_gs + float(theta @ theta) * 1e-3, J_macro, J_gs, float(theta @ theta) * 1e-3

class TGSAutoTuner:
    def __init__(self, node_factory, base_config):
        self.cost = TGSCost(node_factory, base_config)
        self.rng = np.random.default_rng(42)
    def run(self):
        best_p, best_c = None, np.inf
        for _ in range(20):
            pid = PIDParams(*(self.rng.uniform(0.1, 10.0) for _ in range(2)), *(self.rng.uniform(0.01, 5.0) for _ in range(2)), *(self.rng.uniform(0.0, 2.0) for _ in range(2)))
            clamp = GSClampParams(self.rng.uniform(0.1, 5.0), self.rng.uniform(0.1, 10.0), self.rng.uniform(0.1, 10.0))
            p = TGSParams(pid, clamp)
            tot, m, g, j = self.cost.evaluate(p)
            if tot < best_c: best_c, best_p, best_parts = tot, p, (m, g, j)
        m, g, j = best_parts
        return TGSProfile(best_p, best_c, m, g, j)

profile = TGSAutoTuner(lambda c: TordialNode(c), {}).run()
print("Best profile:")
print(f"  J_total: {profile.J_total:.6f}")
print(f"  J_macro: {profile.J_macro:.6f}")
print(f"  J_gs:    {profile.J_gs:.6f}")
print(f"  J_gain:  {profile.J_gain:.6f}")
print(f"  Bound -> max_kappa: {profile.params.clamp.kappa_max:.4f}")
'
