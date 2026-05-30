"""
Tordial–GS Auto Tuner
Lyapunov-guided tuner for PID gains + GS clamping parameters.

Intended integration points:
- TordialNode (macro toroidal drift geometry)
- tordial_gs_v13 (GS regime engine)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Tuple, List, Dict, Any
import numpy as np


# ---------------------------------------------------------------------------
# Config structures
# ---------------------------------------------------------------------------

@dataclass
class PIDParams:
    k_p1: float
    k_p2: float
    k_d1: float
    k_d2: float
    k_i1: float
    k_i2: float

    def as_matrix(self) -> Dict[str, np.ndarray]:
        """Return diagonal matrices for Kp, Kd, Ki."""
        Kp = np.diag([self.k_p1, self.k_p2])
        Kd = np.diag([self.k_d1, self.k_d2])
        Ki = np.diag([self.k_i1, self.k_i2])
        return {"Kp": Kp, "Kd": Kd, "Ki": Ki}


@dataclass
class GSClampParams:
    kappa_max: float
    lambda_clamp: float
    lambda_gs: float


@dataclass
class TGSParams:
    pid: PIDParams
    clamp: GSClampParams


@dataclass
class TGSProfile:
    params: TGSParams
    J_total: float
    J_macro: float
    J_gs: float
    J_gain: float


# ---------------------------------------------------------------------------
# External API hooks (to be implemented against your repo)
# ---------------------------------------------------------------------------

class TordialNode:
    """
    Placeholder interface for your actual TordialNode.

    You should adapt this to your real class:
    - geometry state
    - PID controller injection
    - simulation hooks
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def set_pid_gains(self, Kp: np.ndarray, Kd: np.ndarray, Ki: np.ndarray) -> None:
        """Wire PID gains into the node's controller."""
        raise NotImplementedError

    def set_gs_clamp_params(self, clamp: GSClampParams) -> None:
        """Wire GS clamping parameters into the node."""
        raise NotImplementedError

    def linearize_macro(self) -> np.ndarray:
        """
        Return Jacobian A of macro subsystem around nominal orbit.

        Shape: (n_macro, n_macro)
        """
        raise NotImplementedError

    def simulate_macro_with_gs_input(
        self,
        g_norm: float,
        T: float,
        dt: float,
    ) -> float:
        """
        Simulate macro subsystem with GS input of magnitude g_norm.
        Return steady-state ||x_macro|| (or some norm proxy).
        """
        raise NotImplementedError

    def simulate_gs_with_macro_input(
        self,
        x_macro_norm: float,
        T: float,
        dt: float,
    ) -> float:
        """
        Simulate GS subsystem with macro perturbation of magnitude x_macro_norm.
        Return steady-state V_GS (or ||g|| proxy).
        """
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Utility: ISS gain estimation
# ---------------------------------------------------------------------------

def estimate_gamma_macro(
    node: TordialNode,
    clamp: GSClampParams,
    s_grid: np.ndarray,
    T: float,
    dt: float,
) -> Callable[[float], float]:
    """
    Estimate macro ISS gain gamma: ||g|| -> ||x_macro||.

    Returns a function gamma(s) via interpolation over s_grid.
    """
    x_vals = []
    for s in s_grid:
        # Configure GS clamp (if needed per run)
        node.set_gs_clamp_params(clamp)
        x_ss = node.simulate_macro_with_gs_input(g_norm=s, T=T, dt=dt)
        x_vals.append(x_ss)

    s_grid = np.array(s_grid, dtype=float)
    x_vals = np.array(x_vals, dtype=float)

    def gamma(s: float) -> float:
        return float(np.interp(s, s_grid, x_vals))

    return gamma


def estimate_gamma_gs(
    node: TordialNode,
    clamp: GSClampParams,
    s_grid: np.ndarray,
    T: float,
    dt: float,
) -> Callable[[float], float]:
    """
    Estimate GS ISS gain gamma_GS: ||x_macro|| -> V_GS (or ||g||).
    """
    g_vals = []
    for s in s_grid:
        node.set_gs_clamp_params(clamp)
        g_ss = node.simulate_gs_with_macro_input(x_macro_norm=s, T=T, dt=dt)
        g_vals.append(g_ss)

    s_grid = np.array(s_grid, dtype=float)
    g_vals = np.array(g_vals, dtype=float)

    def gamma_gs(s: float) -> float:
        return float(np.interp(s, s_grid, g_vals))

    return gamma_gs


# ---------------------------------------------------------------------------
# Cost function
# ---------------------------------------------------------------------------

class TGSCost:
    def __init__(
        self,
        node_factory: Callable[[Dict[str, Any]], TordialNode],
        base_config: Dict[str, Any],
        eps_macro: float = -0.1,
        w_macro: float = 1.0,
        w_gs: float = 1.0,
        w_gain: float = 1e-3,
        s_grid: np.ndarray | None = None,
        sim_T: float = 5.0,
        sim_dt: float = 0.01,
    ):
        self.node_factory = node_factory
        self.base_config = base_config
        self.eps_macro = eps_macro
        self.w_macro = w_macro
        self.w_gs = w_gs
        self.w_gain = w_gain
        self.s_grid = s_grid if s_grid is not None else np.linspace(0.1, 1.0, 6)
        self.sim_T = sim_T
        self.sim_dt = sim_dt

    def _build_node(self, params: TGSParams) -> TordialNode:
        node = self.node_factory(self.base_config)
        gains = params.pid.as_matrix()
        node.set_pid_gains(gains["Kp"], gains["Kd"], gains["Ki"])
        node.set_gs_clamp_params(params.clamp)
        return node

    def _macro_margin(self, node: TordialNode) -> float:
        A = node.linearize_macro()
        eigvals = np.linalg.eigvals(A)
        alpha_max = np.max(np.real(eigvals))
        return max(0.0, alpha_max + self.eps_macro)

    def _small_gain_violation(
        self,
        node: TordialNode,
        clamp: GSClampParams,
    ) -> float:
        gamma = estimate_gamma_macro(
            node=node,
            clamp=clamp,
            s_grid=self.s_grid,
            T=self.sim_T,
            dt=self.sim_dt,
        )
        gamma_gs = estimate_gamma_gs(
            node=node,
            clamp=clamp,
            s_grid=self.s_grid,
            T=self.sim_T,
            dt=self.sim_dt,
        )

        J_gs = 0.0
        for s in self.s_grid:
            Delta = gamma(gamma_gs(s)) - s
            J_gs += max(0.0, float(Delta))
        return J_gs

    def _gain_regularization(self, params: TGSParams) -> float:
        theta = np.array([
            params.pid.k_p1, params.pid.k_p2,
            params.pid.k_d1, params.pid.k_d2,
            params.pid.k_i1, params.pid.k_i2,
            params.clamp.kappa_max,
            params.clamp.lambda_clamp,
            params.clamp.lambda_gs,
        ], dtype=float)
        return float(theta @ theta)

    def evaluate(self, params: TGSParams) -> Tuple[float, float, float, float]:
        """
        Return (J_total, J_macro, J_gs, J_gain).
        """
        node = self._build_node(params)

        J_macro = self._macro_margin(node)
        J_gs = self._small_gain_violation(node, params.clamp)
        J_gain = self._gain_regularization(params)

        J_total = (
            self.w_macro * J_macro
            + self.w_gs * J_gs
            + self.w_gain * J_gain
        )
        return J_total, J_macro, J_gs, J_gain


# ---------------------------------------------------------------------------
# Simple global+local search driver (placeholder)
# ---------------------------------------------------------------------------

class TGSAutoTuner:
    """
    High-level auto-tuner.

    Usage:
        tuner = TGSAutoTuner(node_factory, base_config)
        profile = tuner.run()
    """

    def __init__(
        self,
        node_factory: Callable[[Dict[str, Any]], TordialNode],
        base_config: Dict[str, Any],
        n_global_samples: int = 50,
        n_local_iters: int = 30,
        seed: int | None = None,
    ):
        self.cost = TGSCost(node_factory=node_factory, base_config=base_config)
        self.n_global_samples = n_global_samples
        self.n_local_iters = n_local_iters
        self.rng = np.random.default_rng(seed)

    # --- parameter sampling helpers -------------------------------------------------

    def _sample_pid(self) -> PIDParams:
        # You should tune these ranges to your system
        k_p1 = self.rng.uniform(0.1, 10.0)
        k_p2 = self.rng.uniform(0.1, 10.0)
        k_d1 = self.rng.uniform(0.01, 5.0)
        k_d2 = self.rng.uniform(0.01, 5.0)
        k_i1 = self.rng.uniform(0.0, 2.0)
        k_i2 = self.rng.uniform(0.0, 2.0)
        return PIDParams(k_p1, k_p2, k_d1, k_d2, k_i1, k_i2)

    def _sample_clamp(self) -> GSClampParams:
        kappa_max = self.rng.uniform(0.1, 5.0)
        lambda_clamp = self.rng.uniform(0.1, 10.0)
        lambda_gs = self.rng.uniform(0.1, 10.0)
        return GSClampParams(kappa_max, lambda_clamp, lambda_gs)

    def _perturb_params(self, params: TGSParams, scale: float = 0.2) -> TGSParams:
        def jitter(x: float) -> float:
            return float(x * (1.0 + scale * self.rng.normal()))

        pid = PIDParams(
            jitter(params.pid.k_p1),
            jitter(params.pid.k_p2),
            jitter(params.pid.k_d1),
            jitter(params.pid.k_d2),
            jitter(params.pid.k_i1),
            jitter(params.pid.k_i2),
        )
        clamp = GSClampParams(
            jitter(params.clamp.kappa_max),
            jitter(params.clamp.lambda_clamp),
            jitter(params.clamp.lambda_gs),
        )
        return TGSParams(pid=pid, clamp=clamp)

    # --- main tuning loop -----------------------------------------------------------

    def run(self) -> TGSProfile:
        # Global search
        best_params: TGSParams | None = None
        best_cost: float = np.inf
        best_parts: Tuple[float, float, float] | None = None

        for _ in range(self.n_global_samples):
            params = TGSParams(pid=self._sample_pid(), clamp=self._sample_clamp())
            J_total, J_macro, J_gs, J_gain = self.cost.evaluate(params)
            if J_total < best_cost:
                best_cost = J_total
                best_params = params
                best_parts = (J_macro, J_gs, J_gain)

        assert best_params is not None
        assert best_parts is not None

        # Local refinement (simple hill-climb / random search)
        current_params = best_params
        current_cost = best_cost
        current_parts = best_parts

        for _ in range(self.n_local_iters):
            candidate = self._perturb_params(current_params, scale=0.1)
            J_total, J_macro, J_gs, J_gain = self.cost.evaluate(candidate)
            if J_total < current_cost:
                current_params = candidate
                current_cost = J_total
                current_parts = (J_macro, J_gs, J_gain)

        J_macro, J_gs, J_gain = current_parts
        return TGSProfile(
            params=current_params,
            J_total=current_cost,
            J_macro=J_macro,
            J_gs=J_gs,
            J_gain=J_gain,
        )


# ---------------------------------------------------------------------------
# Example wiring stub
# ---------------------------------------------------------------------------

def example_node_factory(config: Dict[str, Any]) -> TordialNode:
    """
    Replace this with a constructor that returns your real TordialNode
    wired to tordial_gs_v13 and your control stack.
    """
    return TordialNode(config)


if __name__ == "__main__":
    base_config = {
        # Fill with your TordialNode configuration
    }

    tuner = TGSAutoTuner(
        node_factory=example_node_factory,
        base_config=base_config,
        n_global_samples=20,
        n_local_iters=10,
        seed=42,
    )

    profile = tuner.run()
    print("Best profile:")
    print("  J_total:", profile.J_total)
    print("  J_macro:", profile.J_macro)
    print("  J_gs:", profile.J_gs)
    print("  J_gain:", profile.J_gain)
    print("  PID:", profile.params.pid)
    print("  Clamp:", profile.params.clamp)