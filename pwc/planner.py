# pwc/planner.py
from uuid import uuid4

from .types import (
    PlannerContext,
    ExternalObjective,
    ManifoldPlan,
    DriftEnvelope,
    CurvatureProfile,
    PressureBudget,
    SafetyPosture,
    TrajectoryScore,
)


class Planner:
    def __init__(self):
        # You can keep internal state here if you want learning later
        pass

    def propose_plan(
        self,
        ctx: PlannerContext,
        objective: ExternalObjective,
        horizon_steps: int = 256,
    ) -> ManifoldPlan:
        """Generate a new plan from current context and external objective."""

        # Example: derive drift envelope from current drift and objective
        current_drift = ctx.manifold_state.global_drift
        max_drift = max(abs(current_drift) * 1.5, 0.05)
        preferred_drift = 0.0 if objective.target_mode == "stabilize" else current_drift

        drift_env = DriftEnvelope(
            max_drift=max_drift,
            preferred_drift=preferred_drift,
            time_horizon=float(horizon_steps),
        )

        # Example: keep current curvature as target, with loose tolerance
        curvature_field = ctx.manifold_state.curvature_field.flatten().tolist()
        curv_profile = CurvatureProfile(
            target_curvature_field=curvature_field,
            tolerance=0.1,
        )

        # Example: pressure budget scaled by objective priorities
        base_budget = ctx.manifold_state.global_pressure
        scale = 0.5 if objective.target_mode == "stabilize" else 1.5
        pressure_budget = PressureBudget(
            global_budget=base_budget * scale,
            per_region_budget=[base_budget * scale] * len(curvature_field),
            time_horizon=float(horizon_steps),
        )

        safety_posture = SafetyPosture(
            max_trip_rate=0.01 if objective.priority_safety > 0.7 else 0.05,
            hard_quarantine_allowed=True,
            degradation_preferred=True,
        )

        return ManifoldPlan(
            id=uuid4(),
            drift_envelope=drift_env,
            curvature_profile=curv_profile,
            pressure_budget=pressure_budget,
            safety_posture=safety_posture,
            horizon_steps=horizon_steps,
        )

    def revise_plan(
        self,
        ctx: PlannerContext,
        previous_plan: ManifoldPlan,
        feedback: TrajectoryScore,
    ) -> ManifoldPlan:
        """Adjust plan based on critic feedback (simple heuristic version)."""

        # Example: if safety_score is low, tighten drift and pressure
        drift_env = previous_plan.drift_envelope
        pressure_budget = previous_plan.pressure_budget

        if feedback.safety_score < 0.8:
            drift_env = DriftEnvelope(
                max_drift=drift_env.max_drift * 0.7,
                preferred_drift=0.0,
                time_horizon=drift_env.time_horizon,
            )
            pressure_budget = PressureBudget(
                global_budget=pressure_budget.global_budget * 0.7,
                per_region_budget=[
                    v * 0.7 for v in pressure_budget.per_region_budget
                ],
                time_horizon=pressure_budget.time_horizon,
            )

        return ManifoldPlan(
            id=uuid4(),
            drift_envelope=drift_env,
            curvature_profile=previous_plan.curvature_profile,
            pressure_budget=pressure_budget,
            safety_posture=previous_plan.safety_posture,
            horizon_steps=previous_plan.horizon_steps,
        )