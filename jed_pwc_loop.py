# jed_pwc_loop.py

from jed_intent_interface import get_current_intent
from jed_autonomous import generate_plan
from jed_unified_runner import (
    capture_manifold_snapshot,
    configure_gs_regime,
    apply_curvature_profile,
    apply_node_policy,
    step_tordial_nodes,
    step_gs_engine,
    run_dual_ring_controller,
    run_safety_trip_matrix,
)
from jed_anomaly_response import evaluate_transition
from jed_persistent_state import load_state, save_state

def pwc_cycle():
    persistent_state = load_state()
    intent = get_current_intent()
    before = capture_manifold_snapshot()

    plan = generate_plan(
        intent=intent,
        snapshot=before,
        memory=persistent_state
    )

    # Walker
    configure_gs_regime(plan.gs_regime, plan.safety_profile)
    apply_curvature_profile(plan.curvature_profile, plan.drift_budget)
    apply_node_policy(plan.node_policy)

    for _ in range(plan.horizon_steps):
        step_tordial_nodes()
        step_gs_engine()
        run_dual_ring_controller()
        run_safety_trip_matrix()

    after = capture_manifold_snapshot()

    # Critic
    critic_result = evaluate_transition(
        plan=plan,
        before=before,
        after=after,
        memory=persistent_state
    )
    save_state(persistent_state, critic_result)

    return plan, critic_result, after