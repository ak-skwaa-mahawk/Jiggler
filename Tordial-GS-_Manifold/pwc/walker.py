# pwc/walker.py
from .types import *
from six_cylinder_boundary import SubstrateEngine
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class Walker:
    """
    Walker component of the Planner–Walker–Critic loop.

    Builds control schedules from ManifoldPlan and executes them on the SubstrateEngine.
    Respects topological guidance from TopoCritic and logs holonomy mode transitions.
    """

    def __init__(self):
        self.current_holonomy_mode: str = "normal"  # normal | conservative | refinement

    def _set_holonomy_mode(self, new_mode: str, reason: str = ""):
        """Internal helper to change mode with logging."""
        if new_mode != self.current_holonomy_mode:
            logger.info(
                f"Holonomy mode changed: {self.current_holonomy_mode} → {new_mode}"
                + (f" | Reason: {reason}" if reason else "")
            )
            self.current_holonomy_mode = new_mode

    def compile_schedule(
        self, 
        plan: ManifoldPlan, 
        snapshot: SubstrateSnapshot
    ) -> ControlSchedule:
        """
        Build a full ControlSchedule, modulated by topological guidance.
        """
        steps = []
        gs = snapshot.gs_state
        guidance = plan.topological_guidance or {}

        # === Extract topological signals ===
        drift_error = guidance.get("curvature_drift_error", 0.0)
        stability = guidance.get("sovereign_stability", 1.0)
        priority_actions = guidance.get("priority_actions", [])

        # === Determine modulation factors ===
        relaxation_base = 1.0
        pressure_scale = 1.0

        # === Holonomy mode logic with logging ===
        if drift_error > 0.06:
            self._set_holonomy_mode("conservative", f"high curvature drift ({drift_error:.4f})")
            relaxation_base = 0.75
            pressure_scale = 0.92

        elif stability > 0.98:
            self._set_holonomy_mode("refinement", f"strong sovereign lock (stability={stability:.3f})")
            relaxation_base = 1.12

        else:
            self._set_holonomy_mode("normal")

        # React to specific TopoCritic priority actions
        for action in priority_actions:
            action_type = action.get("action", "")
            if action_type == "curvature_regularization":
                relaxation_base *= 0.88
            elif action_type == "holonomy_enrichment":
                self._set_holonomy_mode("refinement", "holonomy_enrichment requested by TopoCritic")

        for t in range(plan.horizon_steps):
            α = t / max(plan.horizon_steps - 1, 1)

            spin_target = (1 - α) * gs.spin + α * plan.drift_envelope.preferred_drift
            pressure_target = (1 - α) * gs.pressure + α * (plan.pressure_budget.global_budget * pressure_scale)
            temp_target = (1 - α) * gs.temp + α * 0.0

            relaxation = relaxation_base
            if drift_error > 0.05 and t > plan.horizon_steps * 0.6:
                relaxation *= 0.9

            steps.append(ControlStep(
                tick=t,
                spin_setpoint=spin_target,
                pressure_setpoint=pressure_target,
                temp_setpoint=temp_target,
                relaxation_strength=relaxation,
                quarantine_spin=False,
                quarantine_pressure=False,
                quarantine_temp=False,
            ))

        return ControlSchedule(plan_id=plan.id, steps=steps)

    def tick(self, engine: SubstrateEngine, step: ControlStep) -> SubstrateSnapshot:
        """Execute one control step on the engine."""
        engine.set_setpoints(
            spin=step.spin_setpoint,
            pressure=step.pressure_setpoint,
            temp=step.temp_setpoint,
        )

        return engine.closed_loop_tick(
            relaxation_strength=step.relaxation_strength,
            quarantine_spin=step.quarantine_spin,
            quarantine_pressure=step.quarantine_pressure,
            quarantine_temp=step.quarantine_temp,
        )

    def get_status(self) -> Dict:
        return {
            "holonomy_mode": self.current_holonomy_mode
        }