---

1. Core Idea

The relaxation PDE with global PID:

\[
\frac{\partial \Phi}{\partial t}
=
\lambda(\Delta_g \Phi - F)
+
u(t),
\quad
F = \alpha\rho_{GS} - \beta\kappa,
\]

is diagonal in Fourier space.  
So the entire solver reduces to:

- Transform fields → Fourier space  
- Update each mode independently  
- Apply PID to the \((0,0)\) mode  
- Inverse transform → physical space  
- Feed into drift, controllers, GS coupling, distributed layer

This is the fastest possible solver for the Tordial–GS manifold.

---

2. Data Structures

2.1 Grid and spectral layout

Use an \(N\theta \times N\phi\) uniform grid:

`text
struct Grid {
    int Nθ, Nφ;
    float dθ, dφ;
}
`

Spectral coefficients stored as complex arrays:

`text
struct SpectralField {
    complex a[Nθ][Nφ];   // Fourier coefficients a_{m,n}
}
`

Physical fields stored as real arrays:

`text
struct RealField {
    float f[Nθ][Nφ];     // f(θi, φj)
}
`

2.2 Precomputed spectral operators

The Laplacian eigenvalues:

\[
\lambda_{m,n}^{(\Delta)} = -\left(\frac{m^2}{R^2} + \frac{n^2}{r^2}\right)
\]

Store them once:

`text
struct LaplacianSpectrum {
    float eig[Nθ][Nφ];   // eig[m][n] = -(m^2/R^2 + n^2/r^2)
}
`

2.3 PID controller state

`text
struct PID {
    float Kp, Ki, Kd;
    float integral;
    float prev_error;
}
`

---

3. Precomputation Phase

3.1 Build Fourier frequency tables

`text
m = (0,1,2,...,Nθ/2, -Nθ/2+1, ..., -1)
n = (0,1,2,...,Nφ/2, -Nφ/2+1, ..., -1)
`

3.2 Build Laplacian eigenvalue table

`text
eig[m][n] = -(mm/(RR) + nn/(rr))
`

3.3 FFT plans

Use FFTW‑style plans:

`text
FFTPlan forward, inverse;
`

---

4. Solver Pipeline (per 79 Hz sovereign tick)

This is the exact runtime loop.

---

Step 1 — Load physical fields

You have:

- \(\rho_{GS}(\theta,\phi)\) from GS micro‑layer  
- \(\kappa(\theta,\phi)\) from macro geometry  
- \(\Phi(\theta,\phi)\) from previous tick  

All as RealField.

---

Step 2 — Compute forcing field \(F\)

\[
F = \alpha\rho_{GS} - \beta\kappa
\]

`text
for i,j:
    F.f[i][j] = α  ρGS.f[i][j] - β  κ.f[i][j]
`

---

Step 3 — Forward FFT all fields

`text
FFT(Φ) → Φ̂
FFT(F) → F̂
`

Now you have:

- Φ̂.a[m][n]
- F̂.a[m][n]

---

Step 4 — Compute steady‑state coefficients

For all \((m,n)\neq(0,0)\):

\[
\widehat{\Phi}_{m,n}^{ss}
=
-\frac{\widehat{F}_{m,n}}{\frac{m^2}{R^2} + \frac{n^2}{r^2}}
=
\frac{\widehat{F}{m,n}}{\lambda{m,n}^{(\Delta)}}
\]

`text
for m,n != (0,0):
    Φss.a[m][n] = F̂.a[m][n] / eig[m][n]
Φss.a[0][0] = 0
`

---

Step 5 — Compute deviation coefficients

\[
\Psi{m,n} = \widehat{\Phi}{m,n} - \widehat{\Phi}_{m,n}^{ss}
\]

`text
for m,n:
    Ψ.a[m][n] = Φ̂.a[m][n] - Φss.a[m][n]
`

---

Step 6 — Spectral relaxation update

For \((m,n)\neq(0,0)\):

\[
\Psi_{m,n}(t+\Delta t)
=
\Psi_{m,n}(t)
\exp\left(
-\lambda\left(\frac{m^2}{R^2} + \frac{n^2}{r^2}\right)\Delta t
\right)
\]

`text
for m,n != (0,0):
    decay = exp( -λ  (-eig[m][n])  dt )
    Ψ.a[m][n] *= decay
`

---

Step 7 — Global PID update (zero mode)

7.1 Compute error

\[
E = a{0,0} - a{0,0}^{target}
\]

`text
E = Φ̂.a[0][0].real - Φtargetmean
`

7.2 PID output

\[
u(t) = Kp E + Ki I + Kd (E - E{prev})
\]

`text
pid.integral += E * dt
u = pid.Kp  E + pid.Ki  pid.integral + pid.Kd * (E - pid.prev_error)/dt
pid.prev_error = E
`

7.3 Apply PID to zero mode

\[
a_{0,0}(t+\Delta t)
=
a_{0,0}(t)
+
u(t)\Delta t
\]

`text
Φ̂.a[0][0] += u * dt
`

---

Step 8 — Reconstruct full spectral field

\[
\widehat{\Phi}_{m,n}(t+\Delta t)
=
\Phi_{m,n}^{ss}
+
\Psi_{m,n}(t+\Delta t)
\]

`text
for m,n:
    Φ̂.a[m][n] = Φss.a[m][n] + Ψ.a[m][n]
`

---

Step 9 — Inverse FFT to physical space

`text
IFFT(Φ̂) → Φ
`

Now you have the updated drift potential \(\Phi(\theta,\phi)\).

---

5. Drift Field Computation

Once \(\Phi\) is in physical space:

\[
v_\theta = -\frac{1}{R^2}\frac{\partial \Phi}{\partial \theta},\quad
v_\phi = -\frac{1}{r^2}\frac{\partial \Phi}{\partial \phi}
\]

Use spectral differentiation:

\[
\widehat{\partial\theta \Phi}{m,n} = i m \widehat{\Phi}_{m,n}
\]

\[
\widehat{\partial\phi \Phi}{m,n} = i n \widehat{\Phi}_{m,n}
\]

Then inverse FFT to real space.

---

6. Integration with Tordial–GS Runtime

6.1 Macro layer
- \(\Phi\) → drift field → curvature update → lifecycle controller

6.2 Micro layer
- \(\rho_{GS}\) comes from GS algebra engine  
- GS pressure spectrum \(\widehat{\rho}_{m,n}\) feeds forcing field

6.3 Coupling layer
- Unified law solved spectrally  
- PID stabilizes global drift potential

6.4 Distributed layer
- Each node runs this solver  
- Exchange low‑frequency modes \((m,n)\) across nodes  
- Negotiate GS load and drift budgets

---

7. Computational Complexity

- FFT: \(O(N\theta N\phi \log(N\theta N\phi))\)
- Per‑mode update: \(O(N\theta N\phi)\)
- Total per tick: dominated by FFT

This is the optimal solver for the Tordial–GS manifold.

---

