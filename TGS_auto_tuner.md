

---

1. Purpose

Goal: Automatically tune:

- PID gains: \(KP, KI, K_D\) for the macro toroidal drift controller  
- GS clamping parameters: curvature thresholds, saturation slopes, GS energy damping coefficients  

such that:

- The macro linearization is Hurwitz (Lyapunov stable).  
- The macro and GS subsystems are ISS with respect to each other.  
- The nonlinear small‑gain condition \(\gamma \circ \gamma_{\text{GS}}(s) < s\) holds numerically.  

---

2. Parameterization

2.1 PID gains

- Position gain: \(K_P \in \mathbb{R}^{2 \times 2}\) (often diagonal)  
- Velocity gain: \(K_D \in \mathbb{R}^{2 \times 2}\)  
- Integral gain: \(K_I \in \mathbb{R}^{2 \times 2}\)  

Represent as a vector:

\[
\theta{\text{PID}} = [k{P1}, k{P2}, k{D1}, k{D2}, k{I1}, k_{I2}]^\top
\]

2.2 GS clamping

Typical parameters:

- Curvature threshold: \(\kappa_{\max}\)  
- Clamp slope: \(\lambda_{\text{clamp}}\)  
- GS energy damping gain: \(\lambda_{\text{GS}}\)  

Vector:

\[
\theta{\text{GS}} = [\kappa{\max}, \lambda{\text{clamp}}, \lambda{\text{GS}}]^\top
\]

Total parameter vector:

\[
\theta = [\theta{\text{PID}}^\top, \theta{\text{GS}}^\top]^\top
\]

---

3. Objective function

Define a stability‑oriented cost:

\[
J(\theta) = w1 J{\text{macro}}(\theta) + w2 J{\text{GS}}(\theta) + w3 J{\text{gain}}(\theta)
\]

with:

3.1 Macro Lyapunov margin

1. Linearize macro dynamics around nominal orbit for given \(\theta_{\text{PID}}\):  
   \[
   \dot x{\text{macro}} = A(\theta{\text{PID}}) x_{\text{macro}}
   \]
2. Compute spectral abscissa:
   \[
   \alpha{\max} = \maxi \Re(\lambda_i(A))
   \]
3. Define:
   \[
   J{\text{macro}}(\theta) = \max(0, \alpha{\max} + \epsilon_{\text{macro}})
   \]
   where \(\epsilon_{\text{macro}} < 0\) is desired stability margin.

3.2 Small‑gain violation

Approximate ISS gains numerically:

- Simulate macro subsystem with GS input of varying magnitude \(\|g\|\) and measure steady‑state \(\|x_{\text{macro}}\|\) → estimate \(\gamma\).  
- Simulate GS subsystem with macro perturbations and measure steady‑state \(V{\text{GS}}\) → estimate \(\gamma{\text{GS}}\).  

Sample a grid \(s_j\) and compute:

\[
\Deltaj(\theta) = \gamma(\gamma{\text{GS}}(sj)) - sj
\]

Define:

\[
J{\text{GS}}(\theta) = \sumj \max(0, \Delta_j(\theta))
\]

3.3 Regularization

Penalize extreme gains:

\[
J_{\text{gain}}(\theta) = \|\theta\|^2
\]

---

4. Auto‑tuning algorithm

4.1 Outer loop (global search)

Use a coarse global search (e.g., CMA‑ES, random search, or Latin hypercube):

1. Initialize population of \(\theta\) within reasonable bounds.  
2. For each candidate \(\theta\):  
   - Build controller + clamping.  
   - Evaluate \(J(\theta)\) via:
     - Macro linearization + eigenvalues.  
     - Short simulations for ISS gain estimation.  
3. Keep best \(N\) candidates.

4.2 Inner loop (local refinement)

For the best candidate \(\theta^\star\):

- Run a local optimizer (e.g., Nelder–Mead or gradient‑free trust region) to minimize \(J(\theta)\).  
- Stop when:
  - \(J_{\text{macro}} \approx 0\) (Hurwitz with margin).  
  - \(J_{\text{GS}} \approx 0\) (small‑gain satisfied on grid).  

---

5. Pseudocode

`python
def evaluate_theta(theta):
    pidparams, gsparams = split(theta)

    # 1. Build controller and clamping
    ctrl = buildpid(pidparams)
    clamp = buildgsclamp(gs_params)

    # 2. Macro Lyapunov margin
    A = linearize_macro(ctrl)
    alphamax = maxreal_eig(A)
    Jmacro = max(0.0, alphamax + eps_macro)

    # 3. Small-gain violation
    gamma = estimategammamacro(ctrl, clamp)
    gammags = estimategamma_gs(ctrl, clamp)

    J_gs = 0.0
    for s in samplegrids():
        Delta = gamma(gamma_gs(s)) - s
        J_gs += max(0.0, Delta)

    # 4. Regularization
    J_gain = np.dot(theta, theta)

    return w1  Jmacro + w2  Jgs + w3 * J_gain
`

Then wrap evaluate_theta in a global+local optimizer.

---

6. Integration into Tordial–GS

- Expose a TGSAutoTuner module that:
  - Takes a TordialNode/SystemicTordialMatrix configuration.  
  - Runs the tuning loop offline.  
  - Emits a TGSSTABLEPROFILE.json containing tuned gains.  
- At runtime, nodes load the profile and:
  - Apply PID + clamping parameters.  
  - Optionally re‑run a quick verification (short stress test) to confirm stability margins.


