# intent/intent_planner.py
from pwc.types import ManifoldPlan, PlannerContext
from pwc.planner import Planner
from intent.intent import Intent
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


GS_REGIME_PRESSURE_TARGETS = {
    "SUBCRITICAL": 0.7,
    "MARGINAL":    1.0,
    "GOLDILOCKS":  1.3,
    "DEEP_GS":     1.8,
}


class IntentPlanner:
    """
    Intent-aware planner that:
    - Biases ManifoldPlan toward Intent (classical + GS-regime)
    - Produces GS parameter suggestions for existing feedback laws
    """

    def __init__(self, base_planner: Planner):
        self.base_planner = base_planner

    def propose_intent_plan(
        self,
        context: PlannerContext,
        intent: Intent,
        horizon: int = 30,
        previous_critique: Optional[dict] = None
    ) -> ManifoldPlan:

        plan = self.base_planner.propose_plan(
            context,
            horizon=horizon,
            use_topo_critic=True,
            previous_critique=previous_critique
        )

        original_pressure = plan.pressure_budget.global_budget
        original_max_drift = plan.drift_envelope.max_drift

        plan = self._bias_toward_intent(plan, intent, context)
        plan = self._enforce_invariants(plan, intent)

        # === Generate GS parameter suggestions ===
        gs_suggestions = self._suggest_gs_parameters(intent)
        if plan.topological_guidance is None:
            plan.topological_guidance = {}

        plan.topological_guidance["gs_parameter_suggestions"] = gs_suggestions
        plan.topological_guidance["active_intent"] = intent.name
        plan.topological_guidance["preference_strength"] = intent.preference_strength

        # Logging
        self._log_intent_influence(intent, original_pressure, plan.pressure_budget.global_budget,
                                   original_max_drift, plan.drift_envelope.max_drift)
        if gs_suggestions:
            logger.info(f"[IntentPlanner] GS suggestions: {gs_suggestions}")

        return plan

    def _bias_toward_intent(self, plan: ManifoldPlan, intent: Intent, context: PlannerContext) -> ManifoldPlan:
        strength = intent.preference_strength

        if intent.target_spin is not None:
            plan.drift_envelope.preferred_drift = (
                (1 - 0.4 * strength) * plan.drift_envelope.preferred_drift +
                0.4 * strength * intent.target_spin
            )

        if intent.target_pressure is not None:
            plan.pressure_budget.global_budget = (
                (1 - 0.35 * strength) * plan.pressure_budget.global_budget +
                0.35 * strength * intent.target_pressure
            )

        # GS-Regime biasing
        if intent.has_gs_target():
            target_pressure = None
            if intent.gs_pressure_preference is not None:
                target_pressure = intent.gs_pressure_preference
            elif intent.gs_regime_target in GS_REGIME_PRESSURE_TARGETS:
                target_pressure = GS_REGIME_PRESSURE_TARGETS[intent.gs_regime_target]

            if target_pressure is not None:
                plan.pressure_budget.global_budget = (
                    (1 - 0.3 * strength) * plan.pressure_budget.global_budget +
                    0.3 * strength * target_pressure
                )

            if intent.gs_direction == "increase":
                plan.pressure_budget.global_budget *= (1 + 0.1 * strength)
            elif intent.gs_direction == "decrease":
                plan.pressure_budget.global_budget *= (1 - 0.08 * strength)

        return plan

    def _enforce_invariants(self, plan: ManifoldPlan, intent: Intent) -> ManifoldPlan:
        if plan.drift_envelope.max_drift > intent.max_drift:
            plan.drift_envelope.max_drift = intent.max_drift
        return plan

    def _suggest_gs_parameters(self, intent: Intent) -> Dict:
        """
        Generate suggested GS / SH values based on the intent.
        These can be fed into your existing GS feedback laws.
        """
        if not intent.has_gs_target():
            return {}

        suggestions = {}
        base_gs = 1.02
        base_sh = 1.03

        if intent.gs_regime_target == "DEEP_GS":
            suggestions["suggested_gs"] = round(base_gs + 0.04 * intent.preference_strength, 4)
            suggestions["suggested_sh"] = round(base_sh + 0.02 * intent.preference_strength, 4)
            suggestions["reason"] = "Pushing toward DEEP_GS regime"

        elif intent.gs_regime_target == "GOLDILOCKS":
            suggestions["suggested_gs"] = round(base_gs, 4)
            suggestions["suggested_sh"] = round(base_sh - 0.01 * intent.preference_strength, 4)
            suggestions["reason"] = "Maintaining GOLDILOCKS stability band"

        elif intent.gs_direction == "increase":
            suggestions["suggested_gs"] = round(base_gs + 0.03 * intent.preference_strength, 4)
            suggestions["reason"] = "Increasing GS pressure per intent"

        elif intent.gs_direction == "decrease":
            suggestions["suggested_gs"] = round(base_gs - 0.02 * intent.preference_strength, 4)
            suggestions["reason"] = "Decreasing GS pressure per intent"

        if intent.gs_pressure_preference is not None:
            suggestions["target_pressure"] = intent.gs_pressure_preference

        return suggestions

    def _log_intent_influence(self, intent, original_pressure, new_pressure, original_max_drift, new_max_drift):
        pressure_delta = new_pressure - original_pressure
        drift_delta = new_max_drift - original_max_drift

        logger.info(f"[IntentPlanner] Intent '{intent.name}' applied (strength={intent.preference_strength})")
        if abs(pressure_delta) > 0.01:
            logger.info(f"  Pressure changed by {pressure_delta:+.3f}")
        if abs(drift_delta) > 0.01:
            logger.info(f"  Max drift changed by {drift_delta:+.3f}")
        if intent.gs_regime_target:
            logger.info(f"  Targeting GS regime: {intent.gs_regime_target}")