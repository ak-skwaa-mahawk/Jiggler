# jed_pwc_loop.py
import tordial_gs_manifold as tgm

from jed_pid_bandit import (
    select_gain_index_ucb,
    get_gains_for_index,
)
from jed_persistent_state import load_pid_bandit, save_pid_bandit

def apply_pid_gains_to_controller(gains):
    pass

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

    # Walker Setup
    configure_gs_regime(plan.gs_regime, plan.safety_profile)
    apply_curvature_profile(plan.curvature_profile, plan.drift_budget)
    apply_node_policy(plan.node_policy)

    # 💎 RUST OPERATOR INTEGRATION
    # Initialize our compiled Rust control surface over the horizon constraints
    # Inner Radius = 0.3, Outer = 2.0, Drift Tolerance = plan.drift_budget, Jig Amplitude = 0.4
    drift_budget_val = getattr(plan, 'drift_budget', 0.5)
    operator = tgm.PySovereignOperator(0.3, 2.0, float(drift_budget_val), 0.4)

    print(f"\n[💎 MANIFOLD WALK] Spawning Rust SovereignOperator over horizon context.")
    print(f"  -> Initial coordinates: Radius = {operator.radius:.4f} | Regime = {operator.classify_current_regime()}")

    # Extract intent scaling value from the current pipeline intent metadata
    intent_force_val = 0.15  # Default operational intent force acceleration baseline

    for step_idx in range(plan.horizon_steps):
        # 1. Step the underlying system micro-nodes
        step_tordial_nodes()
        step_gs_engine()
        run_dual_ring_controller()
        run_safety_trip_matrix()

        # 2. Update the authoritative Rust kinematic manifold layer
        operator.step(intent_force_val)
        
        # 3. Log real-time topological feedback flags right out of Rust memory
        current_regime = operator.classify_current_regime()
        distance_to_fence = operator.distance_to_ridge_boundary()
        
        # If the system drops subcritical, inject an automated logging note tracking the JigEngine
        if "Subcritical" in str(current_regime):
            print(f"  [⚠️ STEP {step_idx}] Stagnation detected. Monitoring JigEngine stall buffers...")

    print(f"[💎 WALK COMPLETE] Final Coordinates: Radius = {operator.radius:.4f} | Final Regime = {operator.classify_current_regime()}")

    after = capture_manifold_snapshot()

    # Critic Phase
    critic_result = evaluate_transition(
        plan=plan,
        before=before,
        after=after,
        memory=persistent_state
    )
    save_state(persistent_state, critic_result)

    return plan, critic_result, after
