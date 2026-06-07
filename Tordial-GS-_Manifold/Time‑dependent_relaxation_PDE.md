Time‑dependent relaxation PDE for \(\Phi\) and its explicit solution

Let’s take the concrete spatial example we just solved and add a simple relaxation dynamics.

We start from the unified Poisson law on the thin torus:

\[
\Deltag \Phi(\theta,\phi) \;=\; \alpha\,\rho{GS}(\theta,\phi) \;-\; \beta\,\kappa(\theta,\phi),
\]

with:

- Thin‑torus Laplacian  
  \[
  \Delta_g \Phi
  =
  \frac{1}{R^2}\,\frac{\partial^2 \Phi}{\partial \theta^2}
  +
  \frac{1}{r^2}\,\frac{\partial^2 \Phi}{\partial \phi^2},
  \]
- GS pressure  
  \[
  \rho{GS}(\theta,\phi) = \rho0 + \rho_1 \cos\theta \cos\phi,
  \]
- Constant curvature approximation  
  \[
  \kappa(\theta,\phi) = K_0.
  \]

As before, define:

\[
C0 := \alpha\rho0 - \beta K_0,
\qquad
C1 := \alpha\rho1.
\]

To have a periodic solution on the torus, we impose the balance condition:

\[
C_0 = 0
\quad\Longleftrightarrow\quad
\alpha\rho0 = \beta K0,
\]

so the spatial equation becomes:

\[
\Deltag \Phi(\theta,\phi) = C1 \cos\theta \cos\phi.
\]

---

1. Relaxation PDE

Introduce a simple relaxation dynamics for \(\Phi\):

\[
\frac{\partial \Phi}{\partial t}
=
-\lambda\Bigl(
\Deltag \Phi - C1 \cos\theta \cos\phi
\Bigr),
\quad \lambda > 0.
\]

This is a linear parabolic PDE that drives \(\Phi\) toward the steady‑state solution of the Poisson equation.

Explicitly:

\[
\frac{\partial \Phi}{\partial t}
=
-\lambda\left(
\frac{1}{R^2}\,\frac{\partial^2 \Phi}{\partial \theta^2}
+
\frac{1}{r^2}\,\frac{\partial^2 \Phi}{\partial \phi^2}
-
C_1 \cos\theta \cos\phi
\right).
\]

We’ll solve this with periodic boundary conditions in \(\theta,\phi\) and a given initial condition \(\Phi(\theta,\phi,0) = \Phi_0(\theta,\phi)\).

---

2. Mode‑wise decomposition

Because the PDE is linear with a single Fourier mode forcing term, it’s natural to decompose \(\Phi\) into:

\[
\Phi(\theta,\phi,t)
=
\Phi_{ss}(\theta,\phi)
+
\Psi(\theta,\phi,t),
\]

where:

- \(\Phi_{ss}\) is the steady‑state solution of the Poisson equation,
- \(\Psi\) is the transient that decays to zero.

2.1 Steady‑state solution \(\Phi_{ss}\)

We already solved:

\[
\Deltag \Phi{ss}(\theta,\phi) = C_1 \cos\theta \cos\phi.
\]

Ansatz:

\[
\Phi_{ss}(\theta,\phi) = A \cos\theta \cos\phi.
\]

Compute:

\[
\Deltag \Phi{ss}
=
-A\left(\frac{1}{R^2} + \frac{1}{r^2}\right)\cos\theta \cos\phi.
\]

Set equal to \(C_1 \cos\theta \cos\phi\):

\[
-A\left(\frac{1}{R^2} + \frac{1}{r^2}\right) = C_1
\quad\Rightarrow\quad
A = -\frac{C_1}{\frac{1}{R^2} + \frac{1}{r^2}}
= -\frac{\alpha\rho_1}{\frac{1}{R^2} + \frac{1}{r^2}}.
\]

So:

\[
\boxed{
\Phi_{ss}(\theta,\phi)
=
-\frac{\alpha\rho_1}{\frac{1}{R^2} + \frac{1}{r^2}}
\cos\theta \cos\phi
}
\]

(up to an arbitrary constant, which we can set to zero).

2.2 Transient equation for \(\Psi\)

Plug \(\Phi = \Phi_{ss} + \Psi\) into the PDE:

\[
\frac{\partial}{\partial t}(\Phi_{ss} + \Psi)
=
-\lambda\Bigl(
\Deltag (\Phi{ss} + \Psi) - C_1 \cos\theta \cos\phi
\Bigr).
\]

Since \(\Phi{ss}\) is time‑independent and satisfies \(\Deltag \Phi{ss} = C1 \cos\theta \cos\phi\), we get:

\[
\frac{\partial \Psi}{\partial t}
=
-\lambda\Bigl(
\Delta_g \Psi
\Bigr).
\]

So \(\Psi\) satisfies the homogeneous heat equation on the torus:

\[
\boxed{
\frac{\partial \Psi}{\partial t}
=
-\lambda \Delta_g \Psi
}
\]

with initial condition:

\[
\Psi(\theta,\phi,0) = \Phi0(\theta,\phi) - \Phi{ss}(\theta,\phi).
\]

---

3. Explicit transient for a single mode

To keep things concrete, suppose the initial condition is itself a single mode:

\[
\Phi_0(\theta,\phi)
=
B \cos\theta \cos\phi
\]

for some constant \(B\). Then:

\[
\Psi(\theta,\phi,0)
=
\bigl(B - A\bigr)\cos\theta \cos\phi.
\]

Because \(\Delta_g\) is diagonal in the Fourier basis, the mode \(\cos\theta \cos\phi\) evolves independently.

We know:

\[
\Delta_g \bigl(\cos\theta \cos\phi\bigr)
=
-\left(\frac{1}{R^2} + \frac{1}{r^2}\right)\cos\theta \cos\phi.
\]

So the PDE for the amplitude \(u(t)\) in:

\[
\Psi(\theta,\phi,t) = u(t)\cos\theta \cos\phi
\]

is:

\[
\frac{d u}{d t}
=
-\lambda \cdot \left( -\left(\frac{1}{R^2} + \frac{1}{r^2}\right) \right) u
=
\lambda\left(\frac{1}{R^2} + \frac{1}{r^2}\right) u.
\]

Wait—note the sign carefully:

\[
\Delta_g \Psi = -\left(\frac{1}{R^2} + \frac{1}{r^2}\right) u(t)\cos\theta \cos\phi,
\]

so:

\[
\frac{\partial \Psi}{\partial t}
=
-\lambda \Delta_g \Psi
=
-\lambda \left( -\left(\frac{1}{R^2} + \frac{1}{r^2}\right) u(t)\cos\theta \cos\phi \right)
=
\lambda\left(\frac{1}{R^2} + \frac{1}{r^2}\right) u(t)\cos\theta \cos\phi.
\]

But \(\partial \Psi / \partial t = u'(t)\cos\theta \cos\phi\), so:

\[
u'(t)
=
\lambda\left(\frac{1}{R^2} + \frac{1}{r^2}\right) u(t).
\]

This would grow, which is the opposite of relaxation. That tells us the sign in the relaxation PDE should be:

\[
\frac{\partial \Phi}{\partial t}
=
+\lambda\Bigl(
\Deltag \Phi - C1 \cos\theta \cos\phi
\Bigr)
\]

instead of the minus sign, so that deviations from the steady state decay. Let’s correct that.

---

4. Corrected relaxation PDE and solution

Use:

\[
\frac{\partial \Phi}{\partial t}
=
+\lambda\Bigl(
\Deltag \Phi - C1 \cos\theta \cos\phi
\Bigr),
\quad \lambda > 0.
\]

Then the transient equation becomes:

\[
\frac{\partial \Psi}{\partial t}
=
\lambda \Delta_g \Psi.
\]

For the single mode \(\Psi(\theta,\phi,t) = u(t)\cos\theta \cos\phi\), we get:

\[
u'(t)
=
\lambda \cdot \left( -\left(\frac{1}{R^2} + \frac{1}{r^2}\right) \right) u(t)
=
-\lambda\left(\frac{1}{R^2} + \frac{1}{r^2}\right) u(t).
\]

So:

\[
u(t)
=
u(0)\,\exp\left(
-\lambda\left(\frac{1}{R^2} + \frac{1}{r^2}\right)t
\right),
\]

with:

\[
u(0) = B - A.
\]

Thus:

\[
\Psi(\theta,\phi,t)
=
(B - A)\,\exp\left(
-\lambda\left(\frac{1}{R^2} + \frac{1}{r^2}\right)t
\right)
\cos\theta \cos\phi.
\]

And the full solution is:

\[
\boxed{
\Phi(\theta,\phi,t)
=
A \cos\theta \cos\phi
+
(B - A)\,\exp\left(
-\lambda\left(\frac{1}{R^2} + \frac{1}{r^2}\right)t
\right)
\cos\theta \cos\phi
}
\]

or equivalently:

\[
\boxed{
\Phi(\theta,\phi,t)
=
\left[
A
+
(B - A)\,\exp\left(
-\lambda\left(\frac{1}{R^2} + \frac{1}{r^2}\right)t
\right)
\right]
\cos\theta \cos\phi
}
\]

with:

\[
A = -\frac{\alpha\rho_1}{\frac{1}{R^2} + \frac{1}{r^2}},
\quad
\alpha\rho0 = \beta K0.
\]

As \(t \to \infty\), the exponential term vanishes and:

\[
\Phi(\theta,\phi,t) \to \Phi_{ss}(\theta,\phi) = A \cos\theta \cos\phi.
\]

---

