# pwc/planner.py
from .types import *
import numpy as np
from uuid import uuid4
from pwc.TopoCritic import get_topo_critic_feedback
from typing import Optional, Dict


class Planner:
    def propose_plan(
        self,
        context: PlannerContext,
        horizon: int = 200,
        use_topo_critic: bool = True,
        previous_critique: Optional[Dict] = None
    ) -> ManifoldPlan:
        gs = context.gs_state

        # === Base values ===
        base_max_drift = abs(gs.spin) * 1.5
        base_pressure = min(gs.pressure * 1.5, 2.0)
        base_curvature_target = 1.40
        base_curvature_tolerance = 0.08

        # === React to previous Critic feedback ===
        if previous_critique:
            recommendation = previous_critique.get("recommendation", "ACCEPT")
            drift_error = previous_critique.get("topological_drift_error", 0.0)

            if recommendation == "REFINE":
                # Become more conservative
                base_max_drift *= 0.85
                base_curvature_tolerance = min(0.05, base_curvature_tolerance)
                if drift_error > 0.05:
                    base_curvature_target = 1.36

        # === Topological modulation (existing logic) ===
        topo_feedback = None
        if use_topo_critic:
            try:
                topo_feedback = get_topo_critic_feedback()
            except Exception as e:
                print(f"[Planner] TopoCritic unavailable: {e}")

        if topo_feedback:
            drift_error = topo_feedback.get("curvature_drift_error", 0.0)
            stability = topo_feedback.get("sovereign_stability", 1.0)
            gs_alignment = topo_feedback.get("gs_alignment", 0.87)

            if drift_error > 0.05:
                base_max_drift *= 0.82
            if gs_alignment > 0.85 and stability > 0.96:
                base_pressure = min(base_pressure * 1.08, 2.0)
            if drift_error > 0.06:
                base_curvature_target = 1.37
                base_curvature_tolerance = 0.06
            elif stability > 0.98:
                base_curvature_target = 1.40
                base_curvature_tolerance = 0.05

        # === Build plan ===
        drift_envelope = DriftEnvelope(
            max_drift=base_max_drift,
            preferred_drift=1.5,
            time_horizon=float(horizon)
        )

        curvature_profile = CurvatureProfile(
            target_curvature_field=[base_curvature_target] * 4,
            tolerance=base_curvature_tolerance
        )

        pressure_budget = PressureBudget(
            global_budget=base_pressure,
            per_region_budget=[base_pressure] * 4,
            time_horizon=float(horizon)
        )

        safety_posture = SafetyPosture(
            max_trip_rate=0.02,
            hard_quarantine_allowed=True,
            degradation_preferred=False
        )

        plan = ManifoldPlan(
            id=uuid4(),
            drift_envelope=drift_envelope,
            curvature_profile=curvature_profile,
            pressure_budget=pressure_budget,
            safety_posture=safety_posture,
            horizon_steps=horizon,
        )

        if topo_feedback:
            plan.topological_guidance = {
                "curvature_drift_error": topo_feedback.get("curvature_drift_error", 0.0),
                "sovereign_stability": topo_feedback.get("sovereign_stability", 1.0),
                "gs_alignment": topo_feedback.get("gs_alignment", 0.87),
                "priority_actions": topo_feedback.get("priority_actions", []),
                "recommended_curvature_target": topo_feedback.get("recommended_curvature_target", 1.4),
                "recommended_gs_adjustments": topo_feedback.get("recommended_gs_adjustments", {}),
            }

        return plan