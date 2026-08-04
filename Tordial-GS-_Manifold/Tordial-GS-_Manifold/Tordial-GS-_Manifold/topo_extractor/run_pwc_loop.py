#!/usr/bin/env python3
"""
Full PWC Loop: Planner → Walker → Critic + Topological Guidance
"""

import time
import logging
from six_cylinder_boundary import SubstrateEngine, SubstrateSnapshot
from pwc.types import PlannerContext
from pwc.planner import Planner
from pwc.walker import Walker
from pwc.critic import Critic

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("pwc.full_loop")


def build_context(snapshot):
    return PlannerContext(
        gs_state=snapshot.gs_state,
        manifold_state=snapshot.manifold_state,
        pid_state=snapshot.pid_state,
        lifecycle_state=snapshot.lifecycle_state,
        recent_telemetry=snapshot.telemetry,
    )


def main():
    logger.info("=== Full PWC + TopoCritic + Critic Evaluation Loop ===\n")

    engine = SubstrateEngine(particle_count=120)
    planner = Planner()
    walker = Walker()
    critic = Critic()

    for cycle in range(5):
        logger.info(f"=== Cycle {cycle + 1} ===")

        snapshot = engine.snapshot_substrate()
        context = build_context(snapshot)

        # === Planner ===
        plan = planner.propose_plan(context, horizon=20, use_topo_critic=True)

        # === Walker ===
        schedule = walker.compile_schedule(plan, snapshot)
        results = {"delta_violations": 0, "avg_relaxation": 0.0, "steps": 0}

        for step in schedule.steps[:4]:
            new_snap = walker.tick(engine, step)
            results["steps"] += 1
            results["avg_relaxation"] += step.relaxation_strength
            if new_snap.safety_flags.delta_violation:
                results["delta_violations"] += 1

        results["avg_relaxation"] /= max(results["steps"], 1)
        results["final_stability"] = 1.0 if not new_snap.safety_flags.stability_warning else 0.88
        results["holonomy_mode"] = walker.get_status()["holonomy_mode"]

        # === Critic Evaluation ===
        evaluation = critic.evaluate(plan, results, context)

        logger.info(f"  Score: {evaluation['overall_score']} | Recommendation: {evaluation['recommendation']}")
        for c in evaluation["critique"]:
            logger.info(f"    - {c}")

        time.sleep(0.1)

    logger.info("\n=== Loop Complete ===")


if __name__ == "__main__":
    main()