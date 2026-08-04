Adding a global PID term and its effect on the spectrum

Let’s take the spectral relaxation picture you just built and bolt on a global PID controller, then read off how it changes the eigenvalues.

We start from the relaxation PDE on the thin torus:

\[
\frac{\partial \Phi}{\partial t}
=
\lambda\bigl(\Delta_g \Phi - F(\theta,\phi)\bigr),
\quad
\Delta_g
=
\frac{1}{R^2}\partial_{\theta\theta}
+
\frac{1}{r^2}\partial_{\phi\phi},
\]

with

\[
F = \alpha\rho_{GS} - \beta\kappa,
\quad
\langle F\rangle = 0
\ \text{(global balance)}.
\]

Fourier expansion:

\[
\Phi(\theta,\phi,t)
=
\sum{m,n} a{m,n}(t)\,e^{i(m\theta+n\phi)},
\quad
F(\theta,\phi)
=
\sum{m,n} \widehat{F}{m,n}\,e^{i(m\theta+n\phi)}.
\]

Steady state:

\[
a_{m,n}^{ss}
=
-\frac{\widehat{F}_{m,n}}{\frac{m^2}{R^2}+\frac{n^2}{r^2}},
\quad (m,n)\neq(0,0),
\quad
a_{0,0}^{ss}\ \text{free (set to 0)}.
\]

Define deviations:

\[
\psi{m,n}(t) := a{m,n}(t) - a_{m,n}^{ss}.
\]

Without PID:

\[
\psi_{m,n}'(t)
=
-\lambda\left(\frac{m^2}{R^2}+\frac{n^2}{r^2}\right)\psi_{m,n}(t),
\quad (m,n)\neq(0,0),
\]

so eigenvalues:

\[
\gamma_{m,n}
=
\lambda\left(\frac{m^2}{R^2}+\frac{n^2}{r^2}\right),
\quad (m,n)\neq(0,0),
\]

and the zero mode \((0,0)\) is neutrally drifting (no Laplacian, no forcing).

---

1. Injecting a global PID term

Now add a global scalar PID control as a spatially uniform term:

\[
\frac{\partial \Phi}{\partial t}
=
\lambda\bigl(\Delta_g \Phi - F\bigr)
+
u(t),
\]

where \(u(t)\) is the PID output.

Take the global error as the deviation of the spatial mean of \(\Phi\) from a target:

\[
E(t)
:=
\langle \Phi(\cdot,\cdot,t)\rangle - \Phi_{mean}^{target}
=
a{0,0}(t) - a{0,0}^{target},
\]

since the spatial mean is exactly the \((0,0)\) Fourier coefficient.

PID law:

\[
u(t)
=
K_P E(t)
+
KI \int0^t E(\tau)\,d\tau
+
K_D \frac{dE}{dt}(t).
\]

Because \(u(t)\) is spatially uniform, it only affects the \((0,0)\) mode in Fourier space.

---

2. Effect on nonzero modes \((m,n)\neq(0,0)\)

For \((m,n)\neq(0,0)\), the PDE in Fourier space is unchanged:

\[
\psi_{m,n}'(t)
=
-\lambda\left(\frac{m^2}{R^2}+\frac{n^2}{r^2}\right)\psi_{m,n}(t),
\]

since the uniform term \(u(t)\) has no projection onto nonzero modes.

So:

\[
\boxed{
\gamma_{m,n}^{\text{(with PID)}}
=
\gamma_{m,n}
=
\lambda\left(\frac{m^2}{R^2}+\frac{n^2}{r^2}\right),
\quad (m,n)\neq(0,0).
}
\]

All higher modes relax exactly as before.

---

3. Dynamics of the zero mode with PID

For the zero mode, \(\Delta_g\) and \(F\) both vanish (by balance), so:

\[
a_{0,0}'(t) = u(t).
\]

Define the error:

\[
E(t) = a{0,0}(t) - a{0,0}^{target}.
\]

Then:

\[
E'(t) = a_{0,0}'(t) = u(t).
\]

Plug in the PID law:

\[
E'(t)
=
K_P E(t)
+
KI \int0^t E(\tau)\,d\tau
+
K_D E'(t).
\]

Rearrange:

\[
(1 - K_D)E'(t)
=
K_P E(t)
+
KI \int0^t E(\tau)\,d\tau.
\]

Differentiate once to eliminate the integral:

\[
(1 - K_D)E''(t)
=
K_P E'(t)
+
K_I E(t).
\]

So the zero‑mode error satisfies the second‑order linear ODE:

\[
(1 - KD)E''(t) - KP E'(t) - K_I E(t) = 0.
\]

Characteristic polynomial:

\[
(1 - KD)s^2 - KP s - K_I = 0.
\]

Assuming \(1 - K_D \neq 0\), the eigenvalues for the zero mode are:

\[
\boxed{
s_{0,0}^{\pm}
=
\frac{KP \pm \sqrt{KP^2 + 4(1 - KD)KI}}{2(1 - K_D)}.
}
\]

These are the closed‑loop eigenvalues for the global (mean) mode.

---

4. Stability and interpretation

- Nonzero modes \((m,n)\neq(0,0)\):

  - Eigenvalues unchanged:
    
    \[
    \gamma_{m,n} = \lambda\left(\frac{m^2}{R^2}+\frac{n^2}{r^2}\right) > 0,
    \]
    
    so they decay as \(\exp(-\gamma_{m,n} t)\).

- Zero mode \((0,0)\):

  - Without PID: neutrally drifting (no restoring force).
  - With PID: governed by a second‑order system with eigenvalues \(s_{0,0}^{\pm}\).
  - Stability condition: you want \(\Re(s{0,0}^{\pm}) < 0\), which imposes constraints on \(KP, KI, KD\) (standard PID stability region).

So the global PID term only reshapes the spectrum at the zero mode (the global mean drift potential), leaving all higher spatial modes’ decay rates \(\gamma_{m,n}\) intact.

If you want to control a specific low‑frequency spatial pattern instead of the pure mean, you’d:

- Choose a control shape \(w(\theta,\phi)\) (e.g. a particular Fourier mode),
- Define the error as the projection of \(\Phi\) onto \(w\),
- Inject \(u(t)w(\theta,\phi)\) instead of a uniform \(u(t)\),

and then the same analysis gives you modified eigenvalues for that specific mode, while all other modes remain governed by their original \(\gamma_{m,n}\).