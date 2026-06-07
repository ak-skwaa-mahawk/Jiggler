Spectral relaxation on the torus for arbitrary \(\rho_{GS}\)

Let’s now drop the “single cosine mode” crutch and do the full Fourier/spectral picture for the relaxation PDE driven by an arbitrary GS pressure field.

We stay in the thin‑torus approximation:

\[
T = S^1R \times S^1r,\quad (\theta,\phi)\in[0,2\pi)^2,
\]

with metric approximately

\[
g \approx 
\begin{pmatrix}
R^2 & 0 \\
0 & r^2
\end{pmatrix},
\quad
\Delta_g
=
\frac{1}{R^2}\,\partial_{\theta\theta}
+
\frac{1}{r^2}\,\partial_{\phi\phi}.
\]

We take:

- Arbitrary GS pressure field \(\rho_{GS}(\theta,\phi)\),
- Possibly non‑constant curvature field \(\kappa(\theta,\phi)\),
- Unified law in relaxation form:

\[
\frac{\partial \Phi}{\partial t}
=
\lambda\Bigl(
\Deltag \Phi - \alpha\,\rho{GS}(\theta,\phi) + \beta\,\kappa(\theta,\phi)
\Bigr),
\quad \lambda>0.
\]

---

1. Fourier expansion of \(\rho_{GS}\) and \(\kappa\)

On the 2‑torus, the natural basis is the complex Fourier basis:

\[
e_{m,n}(\theta,\phi) := e^{i(m\theta + n\phi)},
\quad m,n\in\mathbb{Z}.
\]

Any sufficiently nice function \(f(\theta,\phi)\) can be expanded as:

\[
f(\theta,\phi)
=
\sum{m,n\in\mathbb{Z}} \hat{f}{m,n}\, e^{i(m\theta + n\phi)},
\]

with Fourier coefficients:

\[
\hat{f}_{m,n}
=
\frac{1}{(2\pi)^2}
\int0^{2\pi}\int0^{2\pi}
f(\theta,\phi)\,e^{-i(m\theta + n\phi)}\,d\theta\,d\phi.
\]

So write:

\[
\rho_{GS}(\theta,\phi)
=
\sum{m,n} \widehat{\rho}{m,n}\, e^{i(m\theta + n\phi)},
\quad
\kappa(\theta,\phi)
=
\sum{m,n} \widehat{\kappa}{m,n}\, e^{i(m\theta + n\phi)}.
\]

Define the forcing field:

\[
F(\theta,\phi)
:=
\alpha\,\rho_{GS}(\theta,\phi) - \beta\,\kappa(\theta,\phi)
=
\sum{m,n} \widehat{F}{m,n}\, e^{i(m\theta + n\phi)},
\]

with:

\[
\widehat{F}_{m,n}
=
\alpha\,\widehat{\rho}{m,n} - \beta\,\widehat{\kappa}{m,n}.
\]

---

2. Laplacian eigenvalues

The Laplacian acts diagonally on the Fourier basis:

\[
\Deltag e{m,n}
=
-\left(
\frac{m^2}{R^2} + \frac{n^2}{r^2}
\right) e_{m,n}.
\]

So the eigenvalue for mode \((m,n)\) is:

\[
\lambda_{m,n}^{(\Delta)}
=
-\left(
\frac{m^2}{R^2} + \frac{n^2}{r^2}
\right).
\]

Note:

- \(\lambda_{0,0}^{(\Delta)} = 0\) (constant mode),
- \(\lambda_{m,n}^{(\Delta)} < 0\) for \((m,n)\neq(0,0)\).

---

3. Steady‑state solution \(\Phi_{ss}\)

The steady state satisfies:

\[
\Deltag \Phi{ss}(\theta,\phi) = F(\theta,\phi).
\]

Expand:

\[
\Phi_{ss}(\theta,\phi)
=
\sum{m,n} \widehat{\Phi}{m,n}\, e^{i(m\theta + n\phi)}.
\]

Then:

\[
\Deltag \Phi{ss}
=
\sum{m,n} \lambda{m,n}^{(\Delta)} \widehat{\Phi}_{m,n}\, e^{i(m\theta + n\phi)}
=
\sum{m,n} \widehat{F}{m,n}\, e^{i(m\theta + n\phi)}.
\]

Equating coefficients:

- For \((m,n)\neq(0,0)\):

  \[
  \lambda{m,n}^{(\Delta)} \widehat{\Phi}{m,n} = \widehat{F}_{m,n}
  \quad\Rightarrow\quad
  \widehat{\Phi}_{m,n}
  =
  \frac{\widehat{F}{m,n}}{\lambda{m,n}^{(\Delta)}}
  =
  -\frac{\widehat{F}_{m,n}}{\frac{m^2}{R^2} + \frac{n^2}{r^2}}.
  \]

- For \((0,0)\):

  \[
  \lambda_{0,0}^{(\Delta)} = 0,
  \quad
  \Delta_g \text{(constant)} = 0.
  \]

  So the solvability condition is:

  \[
  \widehat{F}_{0,0} = 0
  \quad\Longleftrightarrow\quad
  \frac{1}{(2\pi)^2}
  \int0^{2\pi}\int0^{2\pi}
  F(\theta,\phi)\,d\theta\,d\phi = 0.
  \]

  i.e. the mean of \(F\) must vanish. This is the global balance condition:

  \[
  \alpha \langle \rho_{GS} \rangle = \beta \langle \kappa \rangle,
  \]

  where \(\langle\cdot\rangle\) denotes spatial average over the torus.

  Under this condition, \(\widehat{\Phi}_{0,0}\) is arbitrary (constant offset), which we can set to zero.

So the steady‑state solution is:

\[
\boxed{
\Phi_{ss}(\theta,\phi)
=
-\sum_{(m,n)\neq(0,0)}
\frac{\widehat{F}_{m,n}}{\frac{m^2}{R^2} + \frac{n^2}{r^2}}
\,e^{i(m\theta + n\phi)}
}
\]

with the constraint \(\widehat{F}_{0,0}=0\).

---

4. Time‑dependent relaxation: spectral evolution

The relaxation PDE is:

\[
\frac{\partial \Phi}{\partial t}
=
\lambda\Bigl(
\Delta_g \Phi - F(\theta,\phi)
\Bigr).
\]

Decompose:

\[
\Phi(\theta,\phi,t)
=
\Phi_{ss}(\theta,\phi)
+
\Psi(\theta,\phi,t),
\]

then:

\[
\frac{\partial \Psi}{\partial t}
=
\lambda \Delta_g \Psi.
\]

Expand:

\[
\Psi(\theta,\phi,t)
=
\sum{m,n} \widehat{\Psi}{m,n}(t)\, e^{i(m\theta + n\phi)}.
\]

Plug into the PDE:

\[
\sum{m,n} \widehat{\Psi}'{m,n}(t)\, e^{i(m\theta + n\phi)}
=
\lambda \sum{m,n} \lambda{m,n}^{(\Delta)} \widehat{\Psi}_{m,n}(t)\, e^{i(m\theta + n\phi)}.
\]

Equate coefficients:

\[
\widehat{\Psi}'_{m,n}(t)
=
\lambda \lambda{m,n}^{(\Delta)} \widehat{\Psi}{m,n}(t)
=
-\lambda\left(
\frac{m^2}{R^2} + \frac{n^2}{r^2}
\right)\widehat{\Psi}_{m,n}(t).
\]

So each mode evolves independently as:

\[
\widehat{\Psi}_{m,n}(t)
=
\widehat{\Psi}_{m,n}(0)\,
\exp\left(
-\lambda\left(
\frac{m^2}{R^2} + \frac{n^2}{r^2}
\right)t
\right).
\]

The initial condition is:

\[
\Psi(\theta,\phi,0)
=
\Phi(\theta,\phi,0) - \Phi_{ss}(\theta,\phi),
\]

so:

\[
\widehat{\Psi}_{m,n}(0)
=
\widehat{\Phi}{m,n}(0) - \widehat{\Phi}{m,n}^{(ss)}.
\]

Thus the full time‑dependent solution is:

\[
\boxed{
\Phi(\theta,\phi,t)
=
\Phi_{ss}(\theta,\phi)
+
\sum_{m,n}
\bigl(
\widehat{\Phi}{m,n}(0) - \widehat{\Phi}{m,n}^{(ss)}
\bigr)
\exp\left(
-\lambda\left(
\frac{m^2}{R^2} + \frac{n^2}{r^2}
\right)t
\right)
e^{i(m\theta + n\phi)}
}
\]

with:

\[
\widehat{\Phi}_{m,n}^{(ss)}
=
\begin{cases}
-\dfrac{\widehat{F}_{m,n}}{\frac{m^2}{R^2} + \frac{n^2}{r^2}}, & (m,n)\neq(0,0),\\[6pt]
\text{arbitrary (often set to 0)}, & (m,n)=(0,0),
\end{cases}
\]

and \(\widehat{F}_{0,0}=0\) (global balance).

---

5. Interpretation in Tordial–GS terms

- GS pressure spectrum: \(\widehat{\rho}_{m,n}\) encodes how much GS “load” lives in each spatial mode.
- Curvature spectrum: \(\widehat{\kappa}_{m,n}\) encodes how curvature varies across the torus.
- Forcing spectrum: \(\widehat{F}{m,n} = \alpha\widehat{\rho}{m,n} - \beta\widehat{\kappa}_{m,n}\) is the net drive per mode.
- Steady drift potential: each non‑zero mode \((m,n)\) of \(F\) induces a mode of \(\Phi_{ss}\) scaled by the inverse eigenvalue \(-1/(\frac{m^2}{R^2} + \frac{n^2}{r^2})\).
- Relaxation dynamics: each mode relaxes exponentially with rate

  \[
  \gamma_{m,n}
  =
  \lambda\left(
  \frac{m^2}{R^2} + \frac{n^2}{r^2}
  \right).
  \]

  High‑frequency modes (large \(|m|,|n|\)) decay faster; low‑frequency modes decay slower.

This is the full spectral relaxation picture: the Tordial–GS unified law, under linear relaxation, is a mode‑wise exponential convergence to a GS/curvature‑determined drift potential.

