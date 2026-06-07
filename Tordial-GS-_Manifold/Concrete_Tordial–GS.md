

---

1. Geometry choice and Laplacian

Thin torus approximation: take a 2‑torus

\[
T = S^1R \times S^1r,\quad (\theta,\phi)\in[0,2\pi)^2
\]

with radii \(R\) (major) and \(r\) (minor), and assume \(r \ll R\) so the metric is approximately diagonal and constant:

\[
g \approx 
\begin{pmatrix}
R^2 & 0 \\
0 & r^2
\end{pmatrix}
\]

Then the Laplace–Beltrami operator is approximately

\[
\Delta_g \Phi \;\approx\; \frac{1}{R^2}\,\frac{\partial^2 \Phi}{\partial \theta^2}
\;+\; \frac{1}{r^2}\,\frac{\partial^2 \Phi}{\partial \phi^2}.
\]

We’ll work exactly with this operator.

---

2. Explicit choices for \(\rho_{GS}\) and \(\kappa\)

Pick a simple but nontrivial GS pressure field:

\[
\rho{GS}(\theta,\phi) \;=\; \rho0 \;+\; \rho_1 \cos\theta \cos\phi
\]

with constants \(\rho0, \rho1 \in \mathbb{R}\).

Pick a constant curvature approximation:

\[
\kappa(\theta,\phi) \;=\; K_0
\]

with constant \(K_0 \in \mathbb{R}\).

Then the unified law becomes

\[
\Delta_g \Phi(\theta,\phi)
\;=\;
\alpha\bigl(\rho0 + \rho1 \cos\theta \cos\phi\bigr)
\;-\;
\beta K_0.
\]

Define

\[
C0 := \alpha\rho0 - \beta K_0, 
\qquad
C1 := \alpha\rho1.
\]

So the PDE is

\[
\Delta_g \Phi(\theta,\phi)
\;=\;
C0 \;+\; C1 \cos\theta \cos\phi.
\]

---

3. Solvability condition on the torus

On a compact manifold like the torus, the Poisson equation

\[
\Delta_g \Phi = f
\]

has a periodic solution iff the right‑hand side has zero mean:

\[
\int{T} f\, d\mug = 0.
\]

The mean of \(\cos\theta \cos\phi\) over \([0,2\pi)^2\) is zero, but the mean of the constant \(C0\) is not unless \(C0 = 0\).

So for a well‑posed, periodic \(\Phi\), we impose:

\[
C_0 = 0
\quad\Longleftrightarrow\quad
\alpha\rho0 = \beta K0.
\]

Interpretation: average GS pressure is exactly balanced by average curvature.

Under this condition, the PDE reduces to

\[
\Delta_g \Phi(\theta,\phi)
\;=\;
C_1 \cos\theta \cos\phi.
\]

---

4. Solving the Poisson equation

We now solve

\[
\frac{1}{R^2}\,\frac{\partial^2 \Phi}{\partial \theta^2}
\;+\;
\frac{1}{r^2}\,\frac{\partial^2 \Phi}{\partial \phi^2}
\;=\;
C_1 \cos\theta \cos\phi.
\]

Given the right‑hand side is a single Fourier mode \(\cos\theta \cos\phi\), we look for a solution of the form

\[
\Phi(\theta,\phi) \;=\; A \cos\theta \cos\phi
\]

for some constant \(A\).

Compute the derivatives:

- \(\theta\) derivatives:

  \[
  \frac{\partial \Phi}{\partial \theta}
  = -A \sin\theta \cos\phi,
  \quad
  \frac{\partial^2 \Phi}{\partial \theta^2}
  = -A \cos\theta \cos\phi.
  \]

- \(\phi\) derivatives:

  \[
  \frac{\partial \Phi}{\partial \phi}
  = -A \cos\theta \sin\phi,
  \quad
  \frac{\partial^2 \Phi}{\partial \phi^2}
  = -A \cos\theta \cos\phi.
  \]

Plug into \(\Delta_g\):

\[
\Delta_g \Phi
=
\frac{1}{R^2}(-A \cos\theta \cos\phi)
+
\frac{1}{r^2}(-A \cos\theta \cos\phi)
=
-A\left(\frac{1}{R^2} + \frac{1}{r^2}\right)\cos\theta \cos\phi.
\]

Set this equal to the right‑hand side:

\[
-A\left(\frac{1}{R^2} + \frac{1}{r^2}\right)\cos\theta \cos\phi
\;=\;
C_1 \cos\theta \cos\phi.
\]

Since \(\cos\theta \cos\phi\) is not identically zero, we can divide by it and obtain:

\[
-A\left(\frac{1}{R^2} + \frac{1}{r^2}\right) = C_1.
\]

Thus

\[
A
=
-\frac{C_1}{\frac{1}{R^2} + \frac{1}{r^2}}
=
-\frac{\alpha\rho_1}{\frac{1}{R^2} + \frac{1}{r^2}}.
\]

So one explicit solution is

\[
\boxed{
\Phi(\theta,\phi)
=
-\frac{\alpha\rho_1}{\frac{1}{R^2} + \frac{1}{r^2}}
\;\cos\theta \cos\phi
}
\]

with the balance condition

\[
\boxed{
\alpha\rho0 = \beta K0
}
\]

ensuring solvability and periodicity.

Note: any additional constant can be added to \(\Phi\) (kernel of \(\Delta_g\)), but it doesn’t affect the drift field.

---

5. Drift field for this example

The drift vector field is

\[
v(\theta,\phi) = -\nabla_g \Phi.
\]

With the diagonal metric \(g = \mathrm{diag}(R^2, r^2)\), the gradient components are

\[
\nabla_g \Phi
=
\left(
\frac{1}{R^2}\frac{\partial \Phi}{\partial \theta},
\frac{1}{r^2}\frac{\partial \Phi}{\partial \phi}
\right).
\]

We already computed:

\[
\frac{\partial \Phi}{\partial \theta}
=
A(-\sin\theta \cos\phi),
\quad
\frac{\partial \Phi}{\partial \phi}
=
A(-\cos\theta \sin\phi).
\]

So

\[
\nabla_g \Phi
=
\left(
-\frac{A}{R^2}\sin\theta \cos\phi,
-\frac{A}{r^2}\cos\theta \sin\phi
\right),
\]

and therefore

\[
v(\theta,\phi)
=
- \nabla_g \Phi
=
\left(
\frac{A}{R^2}\sin\theta \cos\phi,
\frac{A}{r^2}\cos\theta \sin\phi
\right).
\]

Substitute \(A\):

\[
v(\theta,\phi)
=
-\frac{\alpha\rho_1}{\frac{1}{R^2} + \frac{1}{r^2}}
\left(
\frac{1}{R^2}\sin\theta \cos\phi,
\frac{1}{r^2}\cos\theta \sin\phi
\right).
\]

This is a fully explicit drift field induced by a specific GS pressure mode and constant curvature, under the Tordial–GS unified law.

---

