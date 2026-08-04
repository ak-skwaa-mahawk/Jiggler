#!/usr/bin/env python3
"""
Minimal Vertical Slice Test
Intent → IntentPlanner → Walker → Critic (with GS-regime targeting)
"""

import time
from six_cylinder_boundary import SubstrateEngine
from pwc.planner import Planner
from pwc.walker import Walker
from pwc.critic import Critic
from pwc.types import PlannerContext
from intent.intent import Intent
from intent.intent_planner import IntentPlanner


def main():
    print("=== Tordial-GS Intent Vertical Slice ===\n")

    # === Initialize components ===
    engine = SubstrateEngine(particle_count=80)
    base_planner = Planner()
    intent_planner = IntentPlanner(base_planner)
    walker = Walker()
    critic = Critic()

    # === Create a GS-focused Intent ===
    deep_gs_intent = Intent(
        name="PushTowardDeepGS",
        gs_regime_target="DEEP_GS",
        gs_direction="increase",
        preference_strength=0.85,      # fairly strong preference
        priority=0.9,
        max_amplification=2.1,
        min_stability=0.90
    )

    print(f"Intent Created: {deep_gs_intent.name}")
    print(f"  GS Target     : {deep_gs_intent.gs_regime_target}")
    print(f"  Direction     : {deep_gs_intent.gs_direction}")
    print(f"  Strength      : {deep_gs_intent.preference_strength}")
    print()

    # === Get current state ===
    snapshot = engine.snapshot_substrate()
    context = PlannerContext(
        gs_state=snapshot.gs_state,
        manifold_state=snapshot.manifold_state,
        pid_state=snapshot.pid_state,
        lifecycle_state=snapshot.lifecycle_state,
        recent_telemetry=snapshot.telemetry
    )

    # === Run one full cycle ===
    print("--- Running Intent-Driven Cycle ---\n")

    plan = intent_planner.propose_intent_plan(
        context=context,
        intent=deep_gs_intent,
        horizon=12
    )

    print(f"Plan created with intent: {plan.topological_guidance.get('active_intent')}")
    print(f"Pressure budget (biased): {plan.pressure_budget.global_budget:.3f}")
    print(f"Max drift (clamped)     : {plan.drift_envelope.max_drift:.3f}")
    print()

    # === Walker executes ===
    schedule = walker.compile_schedule(plan, snapshot)

    results = {"delta_violations": 0, "avg_relaxation": 0.0, "steps": 0}
    final_snapshot = snapshot

    for step in schedule.steps[:4]:
        final_snapshot = walker.tick(engine, step)
        results["steps"] += 1
        results["avg_relaxation"] += step.relaxation_strength
        if final_snapshot.safety_flags.delta_violation:
            results["delta_violations"] += 1

    results["avg_relaxation"] /= max(results["steps"], 1)
    results["final_stability"] = 1.0 if not final_snapshot.safety_flags.stability_warning else 0.88
    results["holonomy_mode"] = walker.get_status()["holonomy_mode"]

    # === Critic evaluates ===
    evaluation = critic.evaluate(plan, results, context)

    print("--- Critic Evaluation ---")
    print(f"Overall Score   : {evaluation['overall_score']}")
    print(f"Recommendation  : {evaluation['recommendation']}")
    print("Critique:")
    for note in evaluation["critique"]:
        print(f"  - {note}")

    print("\n=== Vertical Slice Complete ===")


if __name__ == "__main__":
    main()