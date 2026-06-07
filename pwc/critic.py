# pwc/critic.py
from __future__ import annotations
from .types import (
    Trajectory, TrajectoryScore, Violation,
    ManifoldPlan, PlannerContext
)
from typing import Dict, Optional, Union, List
import numpy as np
import logging

logger = logging.getLogger(__name__)


class Critic:
    """
    Critic component of the Planner–Walker–Critic loop.

    Supports two evaluation modes:
      - Legacy: evaluate_trajectory(trajectory: Trajectory) -> TrajectoryScore
      - Modern:  evaluate_plan(plan, execution_results) -> Dict (with topological guidance)
    """

    def evaluate_trajectory(self, trajectory: Trajectory) -> TrajectoryScore:
        """Evaluate a full executed Trajectory (legacy path)."""
        if not trajectory.samples:
            return TrajectoryScore(
                plan_id=trajectory.plan_id,
                stability_score=0.0,
                safety_score=0.0,
                efficiency_score=0.0,
                integrity_score=0.0,
                overall_score=0.0,
                violations=[]
            )

        spins = [sample.gs_state.spin for sample in trajectory.samples]
        pressures = [sample.gs_state.pressure for sample in trajectory.samples]
        temps = [sample.gs_state.temp for sample in trajectory.samples]
        safeties = [sample.safety_flags for sample in trajectory.samples]

        stability = 1.0 / (1.0 + np.var(spins) + np.var(pressures) + np.var(temps))
        safe_ticks = sum(
            1 for flags in safeties
            if not (flags.delta_violation or flags.stability_warning or flags.pressure_cap_active)
        )
        safety = safe_ticks / len(safeties)
        efficiency = 1.0 / (1.0 + np.mean(pressures) + np.mean(temps))

        overall = 0.4 * stability + 0.4 * safety + 0.2 * efficiency

        violations: List[Violation] = []
        for i, flags in enumerate(safeties):
            if flags.delta_violation:
                violations.append(Violation(
                    tick_index=i, type="delta_violation", severity=0.8,
                    details="Closed loop delta exceeded threshold"
                ))
            if flags.stability_warning:
                violations.append(Violation(
                    tick_index=i, type="stability_warning", severity=0.6,
                    details="Stability dropped below 0.99"
                ))

        return TrajectoryScore(
            plan_id=trajectory.plan_id,
            stability_score=float(stability),
            safety_score=float(safety),
            efficiency_score=float(efficiency),
            integrity_score=float(safety),
            overall_score=float(overall),
            violations=violations
        )

    def evaluate_plan(
        self,
        plan: ManifoldPlan,
        execution_results: Dict[str, float | int | str],
        context: Optional[PlannerContext] = None
    ) -> Dict[str, float | str | List[str]]:
        """
        Modern evaluation path using ManifoldPlan + topological guidance.
        """
        guidance: Dict = plan.topological_guidance or {}

        drift_error: float = guidance.get("curvature_drift_error", 0.0)
        topo_stability: float = guidance.get("sovereign_stability", 1.0)
        gs_alignment: float = guidance.get("gs_alignment", 0.87)

        final_stability: float = float(execution_results.get("final_stability", 1.0))
        delta_violations: int = int(execution_results.get("delta_violations", 0))
        avg_relaxation: float = float(execution_results.get("avg_relaxation", 1.0))
        holonomy_mode: str = str(execution_results.get("holonomy_mode", "normal"))

        # Scoring
        stability_score = min(1.0, final_stability)
        drift_penalty = max(0.0, 1.0 - (drift_error * 8))
        safety_score = max(0.0, 1.0 - (delta_violations * 0.15))
        adaptation_score = 0.95 if holonomy_mode in ("refinement", "conservative") else 0.7

        overall_score = (
            stability_score * 0.35 +
            drift_penalty * 0.25 +
            safety_score * 0.2 +
            adaptation_score * 0.2
        )

        # Critique generation
        critique: List[str] = []
        if drift_error > 0.06:
            critique.append("High curvature drift — consider tighter regularization or GS adjustment")
        if final_stability < 0.95:
            critique.append("Stability degraded during execution")
        if delta_violations > 0:
            critique.append(f"{delta_violations} delta violations detected")
        if holonomy_mode == "conservative":
            critique.append("Walker entered conservative mode (plan may be too aggressive)")
        if not critique:
            critique.append("Plan executed cleanly with good topological alignment")

        recommendation = "ACCEPT" if overall_score > 0.78 else "REFINE"

        report: Dict[str, float | str | List[str]] = {
            "plan_id": str(plan.id),
            "overall_score": round(overall_score, 3),
            "stability_score": round(stability_score, 3),
            "drift_penalty": round(drift_penalty, 3),
            "safety_score": round(safety_score, 3),
            "adaptation_score": round(adaptation_score, 3),
            "holonomy_mode_used": holonomy_mode,
            "topological_drift_error": drift_error,
            "topological_stability": topo_stability,
            "critique": critique,
            "recommendation": recommendation
        }

        logger.info(f"[Critic] Plan {str(plan.id)[:8]} → {overall_score:.3f} | {recommendation}")
        return report

    def evaluate(
        self,
        plan_or_trajectory: Union[ManifoldPlan, Trajectory],
        execution_results: Optional[Dict[str, float | int | str]] = None,
        context: Optional[PlannerContext] = None
    ) -> Union[TrajectoryScore, Dict[str, float | str | List[str]]]:
        """Unified entry point for both evaluation styles."""
        if isinstance(plan_or_trajectory, Trajectory):
            return self.evaluate_trajectory(plan_or_trajectory)
        elif isinstance(plan_or_trajectory, ManifoldPlan):
            return self.evaluate_plan(
                plan_or_trajectory,
                execution_results or {},
                context
            )
        else:
            raise TypeError("Critic.evaluate expects ManifoldPlan or Trajectory")