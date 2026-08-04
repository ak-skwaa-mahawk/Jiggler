#!/usr/bin/env python3
"""
Full Closed-Loop PWC: Planner → Walker → Critic → Feedback to Planner
"""

import time
import logging
from six_cylinder_boundary import SubstrateEngine
from pwc.planner import Planner
from pwc.walker import Walker
from pwc.critic import Critic
from pwc.types import PlannerContext
from typing import Optional, Dict

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
logger = logging.getLogger("pwc.closed_loop")


def main() -> None:
    engine = SubstrateEngine(particle_count=100)
    planner = Planner()
    walker = Walker()
    critic = Critic()

    previous_critique: Optional[Dict] = None

    for cycle in range(6):
        logger.info(f"=== Cycle {cycle + 1} ===")

        snapshot = engine.snapshot_substrate()
        context = PlannerContext(
            gs_state=snapshot.gs_state,
            manifold_state=snapshot.manifold_state,
            pid_state=snapshot.pid_state,
            lifecycle_state=snapshot.lifecycle_state,
            recent_telemetry=snapshot.telemetry
        )

        # === Planner (now receives previous critique) ===
        plan = planner.propose_plan(
            context,
            horizon=18,
            use_topo_critic=True,
            previous_critique=previous_critique
        )

        # === Walker ===
        schedule = walker.compile_schedule(plan, snapshot)

        results = {"delta_violations": 0, "avg_relaxation": 0.0, "steps": 0}
        new_snap = snapshot

        for step in schedule.steps[:4]:
            new_snap = walker.tick(engine, step)
            results["steps"] += 1
            results["avg_relaxation"] += step.relaxation_strength
            if new_snap.safety_flags.delta_violation:
                results["delta_violations"] += 1

        results["avg_relaxation"] /= max(results["steps"], 1)
        results["final_stability"] = 1.0 if not new_snap.safety_flags.stability_warning else 0.88
        results["holonomy_mode"] = walker.get_status()["holonomy_mode"]

        # === Critic ===
        evaluation = critic.evaluate(plan, results, context)
        previous_critique = evaluation   # ← Feedback to next Planner

        logger.info(
            f"  Score: {evaluation['overall_score']} | "
            f"{evaluation['recommendation']}"
        )
        for note in evaluation["critique"]:
            logger.info(f"    → {note}")

        time.sleep(0.08)

    logger.info("=== Closed Loop Finished ===")


if __name__ == "__main__":
    main()