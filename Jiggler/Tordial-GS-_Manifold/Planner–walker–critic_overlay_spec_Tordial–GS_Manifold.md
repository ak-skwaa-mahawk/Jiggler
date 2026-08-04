Planner–walker–critic overlay spec for the Tordial–GS Manifold

This sits strictly above the unified interface you just defined. Think of it as:  
PWC = sovereign cognition layer; Tordial–GS = sovereign substrate.

---

1. Conceptual role of each agent

- Planner:  
  Chooses where the manifold should go in state space over a horizon: target drift envelopes, curvature distributions, GS pressure budgets, and safety posture.

- Walker:  
  Realizes a trajectory through manifold state space by issuing concrete control schedules (PID targets, pressure caps, relaxation profiles) compatible with the closed‑loop interface.

- Critic:  
  Evaluates realized trajectories against objectives: stability, safety, spectral smoothness, resource budgets, and “sovereign integrity” metrics.

All three operate on abstract goals and evaluations, never on raw GS internals—they talk only through the formal interface: GSState, ManifoldState, PIDState, ControlCommand, telemetry, and lifecycle.

---

2. Shared type layer (PWC view of the substrate)

These types are logical overlays on top of the existing interface.

2.1 Goal and constraint types

`text
DriftEnvelope {
    max_drift: Float64
    preferred_drift: Float64
    time_horizon: Float64
}

CurvatureProfile {
    targetcurvaturefield: Field2D
    tolerance: Float64
}

PressureBudget {
    global_budget: Float64
    perregionbudget: Field2D
    time_horizon: Float64
}

SafetyPosture {
    maxtriprate: Float64
    hardquarantineallowed: Bool
    degradation_preferred: Bool
}
`

---

2.2 Plan, trajectory, and evaluation types

`text
ManifoldPlan {
    id: UUID
    drift_envelope: DriftEnvelope
    curvature_profile: CurvatureProfile
    pressure_budget: PressureBudget
    safety_posture: SafetyPosture
    horizon_steps: Int64
}

ControlSchedule {
    plan_id: UUID
    steps: array<ControlStep>
}

ControlStep {
    tick_index: Int64
    pidtargetdrift: Float64
    pressurecapglobal: Float64
    relaxationstrengthglobal: Float64
    regional_overrides: array<RegionalControlOverride>
}

RegionalControlOverride {
    region_id: Int64
    pressure_cap: Float64
    relaxation_strength: Float64
}

TrajectorySample {
    tick_index: Int64
    gs_state: GSState
    manifold_state: ManifoldState
    pid_state: PIDState
    safety_flags: SafetyFlags
}

Trajectory {
    plan_id: UUID
    samples: array<TrajectorySample>
}

TrajectoryScore {
    plan_id: UUID
    stability_score: Float64
    safety_score: Float64
    efficiency_score: Float64
    integrity_score: Float64
    overall_score: Float64
    violations: array<Violation>
}

Violation {
    tick_index: Int64
    type: string
    severity: Float64
    details: string
}
`

---

3. Planner interface

The planner never touches low‑level control; it emits ManifoldPlan objects.

3.1 Inputs

- Current substrate snapshot:
  `text
  PlannerContext {
      gs_state: GSState
      manifold_state: ManifoldState
      pid_state: PIDState
      lifecycle_state: LifecycleState
      recent_telemetry: array<TelemetryRecord>
  }
  `

- Optional external objectives (e.g., from a higher‑order system):
  `text
  ExternalObjective {
      target_mode: string          // e.g., "explore", "stabilize", "reconfigure"
      priority_safety: Float64
      priority_efficiency: Float64
      priority_exploration: Float64
  }
  `

3.2 Planner functions

`text
plannerproposeplan(
    ctx: PlannerContext,
    objective: ExternalObjective
) → ManifoldPlan
`

- Chooses drift envelope, curvature profile, pressure budget, and safety posture over a horizon.

`text
plannerreviseplan(
    ctx: PlannerContext,
    previous_plan: ManifoldPlan,
    feedback: TrajectoryScore
) → ManifoldPlan
`

- Adjusts future plans based on critic feedback.

Key constraint:  
Planner must only express desired envelopes and budgets, not direct control commands.

---

4. Walker interface

The walker is the policy executor over the substrate interface.

4.1 Inputs

- A ManifoldPlan from the planner.
- Live substrate state via the unified interface:
  - GSState, ManifoldState, PIDState, SafetyFlags.

4.2 Walker functions

`text
walkercompileschedule(
    plan: ManifoldPlan,
    initial_state: ManifoldState
) → ControlSchedule
`

- Produces a nominal control schedule (per‑tick ControlStep) consistent with the plan’s envelopes and budgets.

`text
walker_tick(
    plan: ManifoldPlan,
    schedule: ControlSchedule,
    tick_index: Int64,
    gs_state: GSState,
    manifold_state: ManifoldState,
    pid_state: PIDState,
    dt: Float64
) → (ControlCommand, ControlSchedule)
`

- Chooses the actual ControlCommand for this tick:
  - Maps ControlStep → ControlCommand:
    `text
    ControlCommand {
        pid_output: Float64          // target or delta for PID
        pressure_cap: Float64
        relaxation_strength: Float64
        quarantine: Bool
    }
    `
- May adapt the remaining schedule based on observed deviations (e.g., safety flags, unexpected drift).

4.3 Walker–substrate coupling

The walker uses only the existing substrate functions:

- pid_step
- compute_feedback
- closedlooptick
- safety_evaluate
- lifecycle_transition

A typical tick loop (conceptual):

`text
1. Read gsstate, manifoldstate, pid_state.
2. Compute error = desireddriftfromplan - manifoldstate.global_drift.
3. Update pidstate = pidstep(pid_state, error, dt).
4. Derive ControlCommand from ControlStep + pid_state + safety flags.
5. Apply ControlCommand via closedlooptick (or equivalent).
6. Log TrajectorySample for critic.
`

---

5. Critic interface

The critic is the evaluation and learning layer.

5.1 Inputs

- A realized Trajectory (or streaming samples).
- The ManifoldPlan that generated it.
- Optional external reward/priorities.

5.2 Critic functions

`text
criticevaluatetrajectory(
    plan: ManifoldPlan,
    trajectory: Trajectory
) → TrajectoryScore
`

- Computes:
  - stability_score: inverse of drift variance, spectral smoothness, absence of oscillations.
  - safety_score: penalties for trips, quarantines, hard limits exceeded.
  - efficiency_score: GS pressure usage vs. budget, relaxation cost.
  - integrity_score: adherence to safety posture and lifecycle constraints.
  - overall_score: weighted combination.

`text
criticupdatemodels(
    history: array<(ManifoldPlan, Trajectory, TrajectoryScore)>
) → CriticState
`

- Optional: updates internal models for future evaluation (e.g., learned predictors of instability).

5.3 Feedback channels

Critic outputs are consumed by:

- Planner: via plannerreviseplan.
- Walker: optionally, to adjust schedule generation heuristics.

---

6. PWC–substrate integration contract

This is the hard boundary: what PWC is allowed to do to the Tordial–GS substrate.

6.1 Allowed substrate calls

- Read:
  - gsstate, manifoldstate, pidstate, lifecyclestate, telemetry.
- Write/act:
  - Issue ControlCommand via walker.
  - Request lifecycle transitions only through safety‑compatible paths (e.g., no direct jump from QUARANTINED to RUNNING).

6.2 Forbidden operations

- Direct mutation of GSState internals (generators, relations).
- Direct mutation of ManifoldState internals (curvature, node states).
- Bypassing safety or lifecycle transitions.

---

7. High‑level control loop (end‑to‑end)

Putting it all together:

`text
loop over episodes:
    ctx = snapshot_substrate()
    objective = external_objective()

    plan = plannerproposeplan(ctx, objective)
    schedule = walkercompileschedule(plan, ctx.manifold_state)

    trajectory_samples = []

    for tickindex in 0 .. plan.horizonsteps-1:
        state = snapshot_substrate()
        (cmd, schedule) = walker_tick(
            plan, schedule, tick_index,
            state.gsstate, state.manifoldstate, state.pid_state, dt
        )

        // Apply command via substrate closed loop
        (gsnew, manifoldnew, pidnew) = closedloop_tick(
            state.gsstate, state.manifoldstate, state.pid_state, dt
        )

        safety = safetyevaluate(gsnew, manifold_new)
        lifecycle = lifecycletransition(state.lifecyclestate, safety)

        sample = TrajectorySample { ... }
        trajectory_samples.append(sample)

        if lifecycle in {SAFE_SHUTDOWN, QUARANTINED}:
            break

    trajectory = Trajectory { planid: plan.id, samples: trajectorysamples }
    score = criticevaluatetrajectory(plan, trajectory)
    plannerstate = plannerreviseplan(snapshotsubstrate(), plan, score)
`

This is the closed cognitive loop over the closed control loop.

---

8. Extension hooks

8.1 Learning planner

- Planner can be upgraded to a learned policy over PlannerContext → ManifoldPlan.
- Critic’s historical scores become training data.

8.2 Adaptive walker

- Walker can learn mappings from (plan, state) → ControlCommand that respect safety but improve efficiency or stability.

8.3 Meta‑critic

- A higher‑order critic can evaluate sequences of plans and enforce long‑horizon constraints (e.g., wear‑and‑tear on the manifold, cumulative risk).

---

