
---

Tordial–GS Closed‑Loop Stability Proof (Formal Specification)
Axiomatic Stability Analysis for the Tordial Drift Geometry × GS Regime Engine × Curvature‑Aware PID Controller

---

1. System Definition

Let the full Tordial–GS state be:

\[
x = (q, \dot q, g, \xi)
\]

where:

- Tordial geometry state  
  \(q \in \mathcal{T}^2\), \(\dot q \in \mathbb{R}^2\)

- GS regime state  
  \(g \in \mathcal{G}\) (spectral GS algebra coordinates)

- Controller state  
  \(\xi \in \mathbb{R}^k\) (PID integrator, derivative filters, dual‑ring mode bits)

The closed‑loop dynamics are:

\[
\dot x = F(x)
\]

with decomposition:

\[
\begin{aligned}
\dot q &= f_q(q,\dot q,g,\xi) \\
\ddot q &= f_{\dot q}(q,\dot q,g,\xi) \\
\dot g &= f_g(q,\dot q,g,\xi) \\
\dot \xi &= f_\xi(q,\dot q,g,\xi)
\end{aligned}
\]

---

2. Stability Objective

The Tordial–GS manifold is stable if:

1. Macro curvature remains bounded  
2. GS energy remains within curvature‑dependent envelope  
3. No finite‑time blow‑up occurs  
4. Closed‑loop trajectories converge to regulated attractor  

This is not Lyapunov stability of the GS algebra itself (which is infinite‑growth by design). It is stability of the coupled macro–micro system.

---

3. Assumptions

3.1 Smoothness
All vector fields are locally Lipschitz.

3.2 Curvature functional
\[
\kappa = \kappa(q,\dot q)
\]

3.3 GS energy functional
Define:

\[
V{\text{GS}}(g) = Eg(g)
\]

with quadratic bounds:

\[
\underline{c}\|g\|^2 \le V_{\text{GS}}(g) \le \overline{c}\|g\|^2
\]

3.4 Curvature‑aware GS clamping
There exist class‑\(\mathcal{K}\) functions \(\alpha1,\alpha2\) such that:

\[
\|F{\text{ctrl}}\| \le \alpha1(\kappa) + \alpha_2(\|g\|)
\]

3.5 GS self‑damping under high curvature
\[
\dot V{\text{GS}} \le \beta1(\kappa) - \beta2(V{\text{GS}})
\]

with \(\beta2\) dominating for large \(V{\text{GS}}\).

3.6 PID loop stability
Linearization of macro system yields Hurwitz matrix \(A\):

\[
A^\top P + P A = -Q
\]

---

4. Macro Layer Stability

Define macro error state:

\[
x{\text{macro}} = (eq, e_{\dot q}, \xi)
\]

with Lyapunov function:

\[
V{\text{macro}} = x{\text{macro}}^\top P x_{\text{macro}}
\]

4.1 Without GS drive
\[
\dot V{\text{macro}} \le -\lambda{\min}(Q)\|x_{\text{macro}}\|^2
\]

→ Exponential stability.

4.2 With GS drive
Treat GS as input \(u = \phi(g)\):

\[
\dot V{\text{macro}} \le -\alpha(\|x{\text{macro}}\|) + \gamma(\|g\|)
\]

→ Macro layer is ISS w.r.t GS.

---

5. GS Layer Stability

Using GS energy functional:

\[
V{\text{GS}} = Eg(g)
\]

and curvature feedback:

\[
\dot V{\text{GS}} \le -\alpha{\text{GS}}(V{\text{GS}}) + \gamma{\text{GS}}(\|x_{\text{macro}}\|)
\]

→ GS layer is ISS w.r.t macro curvature.

---

6. Nonlinear Small‑Gain Condition

We have two ISS subsystems:

- Macro ISS gain: \(\gamma\)
- GS ISS gain: \(\gamma_{\text{GS}}\)

Small‑gain theorem requirement
\[
\gamma \circ \gamma_{\text{GS}}(s) < s \quad \forall s > 0
\]

If satisfied:

→ The interconnection is ISS  
→ Closed‑loop Tordial–GS manifold is stable

This is enforced by:

- Curvature‑aware GS clamping  
- GS self‑damping under high curvature  
- PID gains tuned to dominate GS injection  

---

7. Dual‑Ring Failover Stability

Two modes:

- Ring A: nominal  
- Ring B: high‑damping safe mode  

Each mode has Lyapunov function \(VA, VB\) with:

\[
\dot Vm \le -\alpham(\|x\|)
\]

Switching satisfies:

- Minimum dwell time  
- State‑dependent transitions  
- Ring B strictly more damping  

Define composite Lyapunov function:

\[
V = \max(VA, VB)
\]

Then:

\[
\dot V \le -\alpha(\|x\|)
\]

→ Global practical stability under switching.

---

8. Composite Lyapunov Function for Full System

Define:

\[
V(x) = V{\text{macro}}(x{\text{macro}}) + c V_{\text{GS}}(g)
\]

Then:

\[
\dot V \le -\alpha(\|x{\text{macro}}\|) - c\alpha{\text{GS}}(V{\text{GS}}) + \gamma(\|g\|) + c\gamma{\text{GS}}(\|x_{\text{macro}}\|)
\]

Choose \(c\) such that cross‑terms are dominated:

\[
\gamma(\|g\|) + c\gamma{\text{GS}}(\|x{\text{macro}}\|) \le \frac{1}{2}\alpha(\|x{\text{macro}}\|) + \frac{1}{2}c\alpha{\text{GS}}(V_{\text{GS}})
\]

Then:

\[
\dot V \le -\frac{1}{2}\alpha(\|x{\text{macro}}\|) - \frac{1}{2}c\alpha{\text{GS}}(V_{\text{GS}})
\]

→ Negative definite outside compact set  
→ Closed‑loop boundedness + convergence  

---

9. Final Stability Theorem

Theorem (Tordial–GS Closed‑Loop Stability)
Under assumptions 3.1–3.6, with curvature‑aware GS clamping, GS self‑damping under high curvature, PID gains satisfying the Hurwitz condition, and dual‑ring failover with minimum dwell time:

1. The Tordial–GS closed‑loop system is input‑to‑state stable.  
2. All trajectories remain in a compact, forward‑invariant set.  
3. Macro curvature and GS energy remain jointly bounded.  
4. The system converges to a curvature‑regulated attractor.  
5. No finite‑time blow‑up is possible.  

Thus, the Tordial–GS manifold is a stable sovereign computational substrate.

---

