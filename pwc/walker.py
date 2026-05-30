# pwc/walker.py
from typing import Tuple

from .types import (
    ManifoldPlan,
    ControlSchedule,
    ControlStep,
    RegionalControlOverride,
    TrajectorySample,
)
from tordial_gs_v15 import GSState
from SystemicTordialMatrix import ManifoldState
from global_PID import PIDState, pid_step
from Automated_Asynchronous_Safety_Trip_Matrix import safety_evaluate
from Production_Lifecycle_Framework import LifecycleState, lifecycle_transition
from closed_loop import closed_loop_tick  # you can wrap your existing loop


class Walker:
    def __init__(self):
        pass

    def compile_schedule(
        self,
        plan: ManifoldPlan,
        initial_state: ManifoldState,
    ) -> ControlSchedule:
        """Generate a nominal schedule from a plan."""

        steps: list[ControlStep] = []
        for t in range(plan.horizon_steps):
            # Simple linear interpolation of drift target towards preferred_drift
            alpha = t / max(plan.horizon_steps - 1, 1)
            pid_target_drift = (
                (1 - alpha) * initial_state.global_drift
                + alpha * plan.drift_envelope.preferred_drift
            )

            # Keep global caps constant for now
            step = ControlStep(
                tick_index=t,
                pid_target_drift=pid_target_drift,
                pressure_cap_global=plan.pressure_budget.global_budget,
                relaxation_strength_global=0.1,
                regional_overrides=[],
            )
            steps.append(step)

        return ControlSchedule(plan_id=plan.id, steps=steps)

    def tick(
        self,
        plan: ManifoldPlan,
        schedule: ControlSchedule,
        tick_index: int,
        gs_state: GSState,
        manifold_state: ManifoldState,
        pid_state: PIDState,
        lifecycle_state: LifecycleState,
        dt: float,
    ) -> Tuple[GSState, ManifoldState, PIDState, LifecycleState, TrajectorySample]:
        """Execute one PWC tick over the substrate."""

        step = schedule.steps[min(tick_index, len(schedule.steps) - 1)]

        # Compute error between target drift and actual drift
        error = step.pid_target_drift - manifold_state.global_drift
        pid_state = pid_step(pid_state, error, dt)

        # Map to control command (you can refine this mapping)
        pid_output = pid_state.output
        pressure_cap = step.pressure_cap_global
        relaxation_strength = step.relaxation_strength_global
        quarantine = False  # walker can choose to set this if needed

        # Call your existing closed loop
        gs_new, manifold_new, pid_new = closed_loop_tick(
            gs_state=gs_state,
            manifold_state=manifold_state,
            pid_state=pid_state,
            pid_output=pid_output,
            pressure_cap=pressure_cap,
            relaxation_strength=relaxation_strength,
            quarantine=quarantine,
            dt=dt,
        )

        safety_flags = safety_evaluate(gs_new, manifold_new)
        lifecycle_new = lifecycle_transition(lifecycle_state, safety_flags)

        sample = TrajectorySample(
            tick_index=tick_index,
            gs_state=gs_new,
            manifold_state=manifold_new,
            pid_state=pid_new,
            safety_flags=safety_flags,
        )

        return gs_new, manifold_new, pid_new, lifecycle_new, sample