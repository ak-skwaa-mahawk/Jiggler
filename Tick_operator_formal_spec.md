Tick operator formal spec (for TripleRingTordialMatrix.executeheavyload_cycle)

I’ll treat one kernel tick as a map on the full triple‑ring state:

\[
\mathcal{T} : Sk \rightarrow S{k+1}
\]

where \(S_k\) is the joint state of all rings and nodes at tick \(k\).

---

1. State space

For each node \(n\):

- Discrete structure:  
  \[
  dn \in [4, 42] \subset \mathbb{Z},\quad rn \in [12, 500] \subset \mathbb{Z}
  \]
- Continuous fields:  
  \[
  \sigma{T,n} \in \mathbb{R},\quad \phin \in [0, \tau_{3D})
  \]
- Ring assignment: \(n \in RA \cup RB \cup R_C\)

For each ring \(R \in \{A,B,C\}\):

- Curvature field: \(C_R\) (implemented by CurvatureField)
- Governor: \(G_R\) (implemented by RingGovernor)

Global:

- Tick counter: \(k \in \mathbb{N}\)

---

2. Tick operator decomposition

One tick is:

\[
\mathcal{T} = \mathcal{L} \circ \mathcal{N} \circ \mathcal{G} \circ \mathcal{C}
\]

in order:

1. \(\mathcal{C}\): curvature/resonance computation per ring  
2. \(\mathcal{G}\): governor control per ring  
3. \(\mathcal{N}\): node‑level evolution (governor + GS + drift)  
4. \(\mathcal{L}\): telemetry logging

---

3. Curvature/resonance operator \(\mathcal{C}\)

For each ring \(R\) with node set \(N_R\):

- Average GS:
  \[
  \bar{\sigma}R = \frac{1}{|NR|} \sum{n \in NR} \sigma_{T,n}
  \]
- Average “kappa”:
  \[
  \bar{\kappa}R = \frac{1}{|NR|} \sum{n \in NR} \frac{\sigma{T,n}}{dn}
  \]

CurvatureField computes:

- Normalized curvature:
  \[
  k{\text{norm}} = \text{clip}\left(\frac{\bar{\kappa}R}{12.0}, 0.0, 1.0\right)
  \]
- Base pressure:
  \[
  bp = 0.45 \cdot k{\text{norm}} + 0.20 \cdot \text{clip}\left(\frac{\bar{\sigma}_R}{500.0}, 0.0, 1.0\right)
  \]
- Node‑count term:
  \[
  \deltaN = \text{clip}\left(\frac{|NR| - 24}{80.0}, 0.0, 0.3\right)
  \]
- Final pressure and resonance:
  \[
  pR = \text{clip}(bp + \delta_N, 0.0, 1.25)
  \]
  \[
  rR = \text{clip}(0.55 \cdot k{\text{norm}}, 0.0, 1.0)
  \]

This yields \((pR, rR)\) for each ring.

---

4. Governor operator \(\mathcal{G}\)

For each ring \(R\):

- Error:
  \[
  eR = \text{target}R - \bar{\sigma}_R
  \]
- Integral (clamped):
  \[
  IR \leftarrow \text{clip}(IR + e_R, -50.0, 50.0)
  \]
- Derivative:
  \[
  DR = eR - eR^{\text{prev}},\quad eR^{\text{prev}} \leftarrow e_R
  \]
- Control signal:
  \[
  uR = 0.012 eR + 0.003 IR + 0.006 DR
  \]
- Discrete corrections:
  \[
  \Delta dR = \text{round}\left(\text{clip}(0.2 uR, -1, 1)\right)
  \]
  \[
  \Delta rR = \text{round}\left(\text{clip}(0.8 uR, -4, 4)\right)
  \]

These \((\Delta dR, \Delta rR)\) are applied uniformly to all nodes in ring \(R\).

---

5. Node evolution operator \(\mathcal{N}\)

For each node \(n \in N_R\):

5.1 Apply governor correction

\[
dn \leftarrow \text{clip}(dn + \Delta d_R, 4, 42)
\]
\[
rn \leftarrow \text{clip}(rn + \Delta r_R, 12, 500)
\]

5.2 GS update with curvature/resonance

Inputs: \(pR, rR\).

- Clamp inputs:
  \[
  p = \text{clip}(pR, 0.0, 1.5),\quad \rho = \text{clip}(rR, 0.0, 1.0)
  \]

- Curvature‑driven structural adjustment (only if high pressure):

  If \(p > 0.6\):

  - base delta:
    \[
    \deltad^{\text{base}} = \max\left(1,\ \left\lfloor 0.35 \rho + 0.1 \phin \right\rfloor\right)
    \]
  - apply at most +1:
    \[
    dn \leftarrow \text{clip}(dn + \min(1, \delta_d^{\text{base}}), 4, 42)
    \]
  - probabilistic radius growth:
    - with probability \(0.45\) if \(\rho > 0.4\):
      \[
      rn \leftarrow \text{clip}(rn + 1, 12, 500)
      \]

- GS field update:

  Let
  \[
  Dn = 4.0 \cdot \phi{op} \cdot \text{GEAR\SHIFT} + 0.08 \phin
  \]
  then
  \[
  \sigma{T,n} \leftarrow rn - \frac{dn^2}{Dn}
  \]

- Drift phase update:

  \[
  \phin \leftarrow (\phin + 0.017) \mod \tau_{3D}
  \]

This completes the per‑node map \((dn, rn, \sigma{T,n}, \phin)k \mapsto (\cdot){k+1}\).

---

6. Telemetry operator \(\mathcal{L}\)

After all rings and nodes are updated:

For each node \(n \in N_R\), for each ring label:

- Insert row into nodes table:

  - ring ∈ {LiveA, LiveB, Live_C}  
  - fields: nodeid, ring, d, r, sigmaT, driftphase, fissioncount=0, parent_id=NULL

This defines a pure append‑only audit of the tick’s post‑state.

---

7. Kernel tick contract

For each tick \(k \to k+1\), the tick operator guarantees:

1. Bounded geometry:
   - \(dn \in [4,42]\), \(rn \in [12,500]\) preserved.
2. Phase continuity:
   - \(\phin\) evolves on a circle of length \(\tau{3D}\) with fixed step 0.017.
3. Ring‑coherent control:
   - All nodes in a ring share the same \((pR, rR, \Delta dR, \Delta rR)\) for that tick.
4. Deterministic evolution (given RNG seed):
   - With fixed random seed, \(\mathcal{T}\) is deterministic.
5. Full post‑state observability:
   - Every tick’s node state is persisted and reconstructible from the DB log.

