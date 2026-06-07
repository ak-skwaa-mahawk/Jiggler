# jed_pwc_loop.py

# inside pwc_cycle or walker_step

from jed_pid_bandit import (
    select_gain_index_ucb,
    get_gains_for_index,
)
from jed_persistent_state import load_pid_bandit, save_pid_bandit

def apply_pid_gains_to_controller(gains):
    # This should call into your existing control matrix / PID implementation
    # e.g., global_pid.set_gains(gains.kp, gains.ki, gains.kd)
    pass

def pwc_cycle(...):
    # load bandit
    pid_bandit = load_pid_bandit()

    # select gains
    gain_idx = select_gain_index_ucb(pid_bandit)
    gains = get_gains_for_index(gain_idx)
    apply_pid_gains_to_controller(gains)

    # ... run horizon, capture before/after, critic, etc.

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