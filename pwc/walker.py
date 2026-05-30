# pwc/walker.py
from .types import *
from six_cylinder_boundary import SubstrateEngine


class Walker:
    def compile_schedule(self, plan: ManifoldPlan, snapshot: SubstrateSnapshot) -> ControlSchedule:
        steps = []
        gs = snapshot.gs_state

        for t in range(plan.horizon_steps):
            α = t / max(plan.horizon_steps - 1, 1)

            spin_target = (1 - α) * gs.spin + α * plan.drift.preferred_drift
            pressure_target = (1 - α) * gs.pressure + α * plan.pressure.preferred_pressure
            temp_target = (1 - α) * gs.temp + α * plan.temp.preferred_temp

            steps.append(ControlStep(
                tick=t,
                spin_setpoint=spin_target,
                pressure_setpoint=pressure_target,
                temp_setpoint=temp_target,
                relaxation_strength=1.0,
            ))

        return ControlSchedule(plan_id=plan.id, steps=steps)

    def tick(self, engine: SubstrateEngine, step: ControlStep) -> SubstrateSnapshot:
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