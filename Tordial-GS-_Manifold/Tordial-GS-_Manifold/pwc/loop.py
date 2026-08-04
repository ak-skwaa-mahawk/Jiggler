# pwc/loop.py
from .planner import Planner
from .walker import Walker
from .critic import Critic
from .types import Trajectory, TrajectorySample


class PWCController:
    def __init__(self, engine):
        self.engine = engine
        self.planner = Planner()
        self.walker = Walker()
        self.critic = Critic()

    def run_episode(self, horizon=200):
        snapshot = self.engine.snapshot_substrate()
        plan = self.planner.propose_plan(snapshot, horizon)
        schedule = self.walker.compile_schedule(plan, snapshot)

        samples = []

        for step in schedule.steps:
            snap = self.walker.tick(self.engine, step)
            samples.append(TrajectorySample(
                tick=step.tick,
                snapshot=snap,
            ))

            if not snap.lifecycle_state.healthy:
                break

        trajectory = Trajectory(plan_id=plan.id, samples=samples)
        score = self.critic.evaluate(trajectory)

        return trajectory, score