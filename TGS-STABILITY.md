Tordial–GS Stability Specification

1. Overview

This document defines the formal stability properties of the Tordial–GS closed-loop system, including macro-level toroidal drift geometry, micro-level GS regime algebra, curvature-aware PID control, and dual-ring failover logic.

2. System State

The full system state is defined as:

q: Toroidal configuration coordinates

q_dot: Drift velocity on the torus

g: GS regime algebraic state

xi: Controller internal state (PID integrator, derivative filters, mode bits)

3. Stability Objectives

The Tordial–GS system is considered stable when:

Macro curvature remains bounded.

GS energy remains within a curvature-dependent envelope.

No finite-time blow-up occurs.

Trajectories converge to a regulated attractor.

4. Assumptions

All vector fields are locally Lipschitz.

A curvature functional κ(q, q_dot) exists.

GS energy functional V_GS(g) satisfies quadratic bounds.

Curvature-aware clamping ensures bounded control influence.

GS self-damping activates under high curvature.

PID gains yield a Hurwitz linearization of the macro subsystem.

5. Macro Layer Stability

Define macro error state x_macro = (e_q, e_q_dot, xi). A quadratic Lyapunov function V_macro = x_macro^T P x_macro satisfies:

Without GS drive: V_macro_dot ≤ -λ_min(Q) ||x_macro||²

With GS drive: V_macro_dot ≤ -α(||x_macro||) + γ(||g||)

Thus, the macro layer is input-to-state stable (ISS) with respect to GS influence.

6. GS Layer Stability

Using the GS energy functional V_GS(g):

V_GS_dot ≤ -α_GS(V_GS) + γ_GS(||x_macro||)

Thus, the GS layer is ISS with respect to macro curvature.

7. Nonlinear Small-Gain Condition

The closed-loop system is stable if the ISS gains satisfy:

γ(γ_GS(s)) < s for all s > 0

This ensures the interconnection of macro and GS subsystems is ISS.

8. Dual-Ring Failover Stability

Two modes exist:

Ring A: Nominal operation

Ring B: High-damping safe mode

Each mode has a Lyapunov function V_A, V_B with:

V_m_dot ≤ -α_m(||x||)

A composite Lyapunov function V = max(V_A, V_B) ensures global practical stability under dwell-time-constrained switching.

9. Composite Lyapunov Function

Define V(x) = V_macro + c V_GS. With appropriate choice of c:

V_dot ≤ -½ α(||x_macro||) - ½ c α_GS(V_GS)

This ensures boundedness and convergence.

10. Stability Theorem

Under the stated assumptions and control laws:

The Tordial–GS system is input-to-state stable.

All trajectories remain in a compact, forward-invariant set.

Macro curvature and GS energy remain jointly bounded.

The system converges to a curvature-regulated attractor.

No finite-time blow-up occurs.

This establishes the Tordial–GS manifold as a stable computational substrate.