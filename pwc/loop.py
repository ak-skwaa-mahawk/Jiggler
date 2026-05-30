# pwc/loop.py
from typing import List

from .planner import Planner
from .walker import Walker
from .critic import Critic
from .types import PlannerContext, ExternalObjective, Trajectory
from Asynchronous_Telemetry_Architecture import get_recent_telemetry
from Production_Lifecycle_Framework import get_lifecycle_state
from substrate_snapshot import snapshot_substrate  # you’ll implement this


class PWCController:
    def __init__(self):
        self.planner = Planner()
        self.walker = Walker()
        self.critic = Critic()

    def run_episode(
        self,
        objective: ExternalObjective,
        horizon_steps: int = 256,
        dt: float = 1.0 / 79.0,
    ) -> Trajectory:
        # Snapshot initial substrate
        snap = snapshot_substrate()
        ctx = PlannerContext(
            gs_state=snap.gs_state,
            manifold_state=snap.manifold_state,
            pid_state=snap.pid_state,
            lifecycle_state=snap.lifecycle_state,
            recent_telemetry=get_recent_telemetry(),
        )

        plan = self.planner.propose_plan(ctx, objective, horizon_steps=horizon_steps)
        schedule = self.walker.compile_schedule(plan, ctx.manifold_state)

        samples = []
        lifecycle_state = ctx.lifecycle_state
        gs_state = ctx.gs_state
        manifold_state = ctx.manifold_state
        pid_state = ctx.pid_state

        for t in range(horizon_steps):
            gs_state, manifold_state, pid_state, lifecycle_state, sample = (
                self.walker.tick(
                    plan=plan,
                    schedule=schedule,
                    tick_index=t,
                    gs_state=gs_state,
                    manifold_state=manifold_state,
                    pid_state=pid_state,
                    lifecycle_state=lifecycle_state,
                    dt=dt,
                )
            )
            samples.append(sample)

            if lifecycle_state.name in ("SAFE_SHUTDOWN", "QUARANTINED"):
                break

        trajectory = Trajectory(plan_id=plan.id, samples=samples)
        score = self.critic.evaluate_trajectory(trajectory)

        # Optionally: feed back into planner for next episode
        snap = snapshot_substrate()
        ctx = PlannerContext(
            gs_state=snap.gs_state,
            manifold_state=snap.manifold_state,
            pid_state=snap.pid_state,
            lifecycle_state=snap.lifecycle_state,
            recent_telemetry=get_recent_telemetry(),
        )
        _ = self.planner.revise_plan(ctx, plan, score)

        return trajectory