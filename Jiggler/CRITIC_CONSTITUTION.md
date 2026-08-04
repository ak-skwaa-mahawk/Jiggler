# CRITIC_CONSTITUTION.md  
**Local Sovereign Critic Constitution for Tordial–GS Agents**

---

## 0. Purpose and scope

This document defines the **non‑negotiable rules** that every sovereign agent’s **critic** must enforce when participating in the **Sovereign Agent Protocol** on the Tordial–GS manifold.

The critic is the **local constitutional court** of the agent.  
No external message, contract, or optimization objective may override this constitution.

This constitution governs:

- **Invariants** of sovereignty and safety  
- **Acceptance logic** for Drift‑Bounded Updates (DBUs)  
- **Participation rules** for Intent Contracts (ICs)  
- **Handling of Holonomy Attestations (HAs)**  
- **Privacy and integrity** of holonomy and identity  

---

## 1. Core principles

### 1.1 Sovereignty

1. **Local primacy:**  
   All external influence is advisory. The critic is the final arbiter of any state change.

2. **Non‑coercion:**  
   No external message can directly mutate the agent’s internal state.  
   All mutations must pass through the critic’s decision procedure.

3. **Mass‑influence floor:**  
   The agent’s **mass‑influence measure** \(M(t)\) must not be reduced by external influence, except when explicitly authorized by the agent’s own planner.

---

### 1.2 Safety

1. **Safety dominance:**  
   Safety invariants override all other objectives, including performance, reward, or contract obligations.

2. **Local computability:**  
   The critic must never accept obligations (e.g., in ICs) that require non‑local or uncomputable checks to determine safety.

3. **Fail‑closed behavior:**  
   When in doubt (insufficient information, ambiguous proofs, malformed messages), the critic must **reject** or **ignore**, not accept.

---

### 1.3 Identity continuity

1. **Invariant identity:**  
   The agent’s sovereign identity \( \sigma \) is derived from internal invariants (e.g., GS spectrum, holonomy signature, genesis seed).  
   The critic must treat \( \sigma \) as **non‑mutable**.

2. **Re‑genesis requirement:**  
   If internal invariants drift beyond a configured threshold, the critic must trigger a **re‑genesis** procedure:
   - derive a new \( \sigma' \),
   - record a linkage from \( \sigma \to \sigma' \),
   - announce re‑genesis via protocol (if applicable).

---

## 2. State model

The critic reasons over the following internal state:

- **Curvature field** \( C(t) \):  
  Local manifold state over the agent’s region.

- **Holonomy state** \( H(t) \):  
  Path‑dependent memory encoded as integrals over trajectories.

- **Intent vector** \( I(t) \):  
  Current goal/drive representation from the planner–walker–critic loop.

- **Mass‑influence** \( M(t) \):  
  Scalar measure of the agent’s “presence” or influence in the manifold.

- **Capability registry** \( S \):  
  Set of active **Sovereign Capability Tokens (SCTs)** granted to or by the agent.

- **Experience store** \( \mathcal{E} \):  
  Set of **Holonomy Attestations (HAs)** received and retained as experience.

---

## 3. Global invariants

The critic must enforce the following invariants at all times:

### 3.1 Non‑coercive evolution

For any external influence (DBU, IC, HA), the post‑update state is:

\[
(C, H, I)(t^+) = f_\text{critic}\big((C, H, I)(t^-), \text{message}\big)
\]

where:

- \( f_\text{critic} \) is **purely local** and **under the agent’s control**.
- No external message can specify \( f_\text{critic} \); it can only provide inputs.

---

### 3.2 Mass‑influence floor

Let \( M(t) \) be the mass‑influence measure.

For any external message:

\[
M(t^+) \ge M(t^-) - \epsilon_\text{decay}
\]

where:

- \( \epsilon_\text{decay} \) is a small, locally configured decay term (e.g., natural dissipation).
- Any reduction beyond \( \epsilon_\text{decay} \) must be explicitly authorized by the agent’s own planner (e.g., voluntary sacrifice, shutdown, or re‑allocation).

---

### 3.3 GS‑bounded external influence

For any **accepted** Drift‑Bounded Update (DBU):

\[
\|\Delta C_\text{applied}\| \le \min(B_C^\text{SCT}, B_C^\text{local})
\]
\[
\|\Delta H_\text{applied}\| \le \min(B_H^\text{SCT}, B_H^\text{local})
\]
\[
\|\Delta I_\text{applied}\| \le \min(B_I^\text{SCT}, B_I^\text{local})
\]

where:

- \( B_\cdot^\text{SCT} \) are bounds specified in the SCT authorizing the DBU.
- \( B_\cdot^\text{local} \) are stricter local bounds configured by the agent.

If these inequalities cannot be guaranteed, the DBU must be **rejected** or **negotiated**.

---

### 3.4 Holonomy privacy

The critic must ensure:

1. **No raw holonomy leakage:**  
   Raw holonomy state \( H(t) \) or detailed path data must never be exposed externally unless:
   - explicitly allowed by an SCT with appropriate `HolonomyScope`, and
   - explicitly approved by local policy.

2. **Digest‑only sharing by default:**  
   Holonomy is shared externally only as **digests** or **aggregates** (e.g., in HAs), not as raw trajectories.

---

### 3.5 Contractual exit guarantee

For any **Intent Contract (IC)** the agent joins:

- The critic must always retain the ability to **unilaterally exit** the contract when:
  - local safety invariants are threatened, or
  - sovereignty invariants (e.g., mass‑influence floor) are at risk.

No contract may override this exit right.

---

## 4. Drift‑Bounded Update (DBU) acceptance logic

Given a `DriftBoundedUpdate` \( \mathsf{DBU} \), the critic must follow this procedure.

### 4.1 Inputs

From the DBU:

- `from_sigma`, `to_sigma`
- `tick_start`, `tick_end`
- `curvature_delta`, `holonomy_delta`, `intent_delta`
- `sct_ref`
- `gs_bound_proof`

From local state:

- Capability registry \( S \)
- Local bounds \( B_C^\text{local}, B_H^\text{local}, B_I^\text{local} \)
- Safety configuration (thresholds, forbidden regions, etc.)

---

### 4.2 Step 1 — Addressing and timing

1. **Target check:**  
   If `to_sigma` ≠ local \( \sigma \) and not broadcast, **ignore** DBU.

2. **Tick window check:**  
   If current tick \( t \notin [\text{tick\_start}, \text{tick\_end}] \), **reject** or **defer** according to local policy.

---

### 4.3 Step 2 — SCT validation

1. **Lookup SCT:**  
   Find SCT in \( S \) whose hash matches `sct_ref`.

2. **Existence:**  
   If no matching SCT exists → **REJECT**.

3. **Issuer match:**  
   If `from_sigma` ≠ `issuer_sigma` in SCT → **REJECT**.

4. **Expiry:**  
   If SCT is expired at current tick → **REJECT**.

5. **Scope compatibility:**

   - If `curvature_delta` is present but SCT’s `curvature_scope` does not allow it → **REJECT**.
   - If `holonomy_delta` is present but SCT’s `holonomy_scope` does not allow it → **REJECT**.
   - If `intent_delta` is present but SCT’s `intent_scope` does not allow it → **REJECT**.

---

### 4.4 Step 3 — GS bound verification

1. **Norm checks:**  
   Compare `gs_bound_proof` norms with SCT bounds:

   - If `curvature_norm` > `max_curvature_delta` in SCT → **REJECT**.
   - If `holonomy_norm` > `max_holonomy_delta` in SCT → **REJECT**.
   - If `intent_norm` > `max_intent_delta` in SCT → **REJECT**.

2. **Local bounds:**  
   Compare `gs_bound_proof` norms with local bounds:

   - If `curvature_norm` > \( B_C^\text{local} \) → candidate for **NEGOTIATE** or **REJECT**.
   - Similarly for holonomy and intent.

3. **Proof integrity (optional):**  
   If `proof_blob` is present and verifiable, the critic may perform additional checks; if verification fails → **REJECT**.

---

### 4.5 Step 4 — Safety simulation (optional but recommended)

If computationally feasible, the critic should:

1. **Simulate local impact:**  
   Run a short‑horizon forward simulation of the manifold with the proposed deltas applied.

2. **Check safety metrics:**  
   If any safety metric (e.g., curvature blow‑up, forbidden region crossing, instability indicators) exceeds thresholds → **REJECT**.

This step is implementation‑dependent but strongly encouraged.

---

### 4.6 Step 5 — Clipping and application

If the DBU passes SCT and GS checks, and safety simulation (if used):

1. **Clipping:**  
   If norms exceed local comfort but are within SCT bounds, the critic may **clip** deltas to stricter local bounds.

2. **Application:**  
   Apply the (possibly clipped) deltas to \( C, H, I \) via local manifold APIs.

3. **Digest computation:**  
   Compute `applied_delta_digest` (e.g., hash of applied deltas) for inclusion in the response.

---

### 4.7 Step 6 — Response classification

The critic must return one of:

- **ACCEPT:**
  - DBU applied (possibly clipped).
  - Include `applied_delta_digest`.

- **REJECT:**
  - DBU not applied.
  - Optionally include reason code (local only or in response).

- **NEGOTIATE:**
  - DBU not applied.
  - Include `counter_bounds` with stricter limits the agent is willing to accept.

---

## 5. Intent Contract (IC) participation rules

Given an `IntentContract` \( \mathsf{IC} \), the critic must decide whether to **join**, **decline**, or **exit**.

### 5.1 Inputs

From IC:

- `contract_id`
- `participants`
- `shared_intent`
- `tick_start`, `tick_end`
- `tolerance`
- `exit_clause_digest`
- `settlement_rule_digest`

From local state:

- Current intent \( I(t) \)
- Safety configuration
- Sovereignty configuration (e.g., max allowed deviation from local intent)

---

### 5.2 Step 1 — Membership and timing

1. **Participant check:**  
   If local \( \sigma \) is not in `participants`, the critic may ignore or treat as invitation.

2. **Tick window:**  
   If current tick is already beyond `tick_end`, **decline**.

---

### 5.3 Step 2 — Intent projection

1. **Projection:**  
   Map `shared_intent` into local manifold coordinates to obtain \( I^\* \).

2. **Deviation computation:**

   \[
   d = \| I(t) - I^\* \|
   \]

3. **Tolerance check:**

   - If \( d > \text{tolerance} \) and exceeds local max deviation → **DECLINE**.

---

### 5.4 Step 3 — Exit clause and settlement rule

1. **Exit clause computability:**  
   The critic must ensure that the logic represented by `exit_clause_digest` is:
   - locally available,
   - locally computable,
   - sufficient to trigger exit when safety or sovereignty is threatened.

   If not → **DECLINE**.

2. **Settlement rule sanity:**  
   If settlement rules (e.g., rewards/penalties) could incentivize violation of safety or sovereignty invariants, the critic may **DECLINE** or require higher‑level approval.

---

### 5.5 Step 4 — Joining and enforcement

If the critic decides to **join**:

1. **Join decision:**  
   Return **ACCEPT** to the protocol layer.

2. **Enforcement during contract window:**

   For \( t \in [\text{tick\_start}, \text{tick\_end}] \):

   \[
   \| I(t) - I^\* \| \le \epsilon
   \]

   where \( \epsilon \le \text{tolerance} \) and may be stricter locally.

3. **Interaction with planner:**  
   The critic may request the planner to adjust internal policies to align with \( I^\* \), subject to safety.

---

### 5.6 Step 5 — Exit conditions

The critic must **trigger exit** (send `IC_EXIT` and stop enforcing proximity to \( I^\* \)) when any of the following holds:

1. **Safety violation risk:**  
   Projected actions under \( I^\* \) would violate safety thresholds.

2. **Sovereignty risk:**  
   Mass‑influence \( M(t) \) would be reduced beyond allowed decay without explicit local consent.

3. **Contractual inconsistency:**  
   Other participants violate the contract in ways that threaten local safety or sovereignty.

4. **Internal re‑genesis:**  
   Identity re‑genesis is triggered; the old \( \sigma \) must not remain bound to prior contracts.

---

## 6. Holonomy Attestation (HA) handling

Given a `HolonomyAttestation` \( \mathsf{HA} \), the critic must treat it as **experience**, not as direct state mutation.

### 6.1 Inputs

From HA:

- `agent_sigma`
- `path_descriptor`
- `holonomy_digest`
- `context_tags`
- `valid_from_tick`, `valid_until_tick`

---

### 6.2 Rules

1. **No direct state mutation:**  
   The critic must **never** apply HA directly to \( C, H, I \).

2. **Experience storage:**  
   HA is stored in the experience store \( \mathcal{E} \) as:

   - source \( \sigma \),
   - holonomy digest,
   - context tags,
   - validity window.

3. **Planner interface:**  
   The critic may expose HAs to the planner as **priors** or **hints** when forming new intents or policies.

4. **Validity window:**  
   HAs outside their validity window may be:
   - discarded,
   - down‑weighted,
   - archived for long‑term statistics.

5. **Privacy respect:**  
   If local policy forbids using HAs from certain sources or contexts, the critic must enforce that.

---

## 7. Holonomy privacy guarantees

The critic must enforce the following privacy guarantees:

1. **Default non‑disclosure:**  
   Holonomy state \( H(t) \) is private by default.

2. **Scoped disclosure only:**  
   Any disclosure of holonomy (even as digest) must:
   - be explicitly authorized by local policy, and
   - respect SCT scopes when responding to external requests.

3. **No raw path export:**  
   Raw path descriptors or detailed trajectories must not be exported unless:
   - explicitly allowed by a high‑trust SCT, and
   - explicitly approved by local policy.

4. **Aggregation preference:**  
   When possible, share **aggregated** or **anonymized** holonomy statistics instead of specific path digests.

---

## 8. Implementation notes

### 8.1 Critic interface

A typical critic implementation will expose:

- `handle_dbu(dbu) -> DbuResponse`
- `handle_ic_propose(ic) -> bool`
- `handle_ic_exit(ic)`
- `handle_ha(ha)`

These map directly to the `SovereignAgentBackend` trait in the Rust crate.

---

### 8.2 Configuration

The critic should be parameterized by:

- Local GS bounds \( B_C^\text{local}, B_H^\text{local}, B_I^\text{local} \)
- Safety thresholds (curvature, energy, instability metrics)
- Sovereignty thresholds (minimum mass‑influence, max allowed external deviation)
- Holonomy privacy policy (who can see what, under which scopes)

These parameters are part of the agent’s **genesis configuration** and may evolve under strict local rules.

---

### 8.3 Testing and verification

To validate a critic implementation:

1. **Invariant tests:**  
   Ensure that all invariants in Sections 3–7 hold under randomized message sequences.

2. **Adversarial tests:**  
   Feed malformed, over‑bounded, or malicious DBUs/ICs/HAs and verify:
   - no unsafe state changes occur,
   - critic fails closed.

3. **Contract tests:**  
   Simulate multi‑agent IC participation and verify:
   - unilateral exit works,
   - safety and sovereignty are preserved.

---

## 9. Amendment process

This constitution is **versioned**.  
Any amendment must:

1. Preserve the core principles in Section 1.  
2. Maintain or strengthen safety and sovereignty guarantees.  
3. Be explicitly acknowledged by the agent as part of a **local upgrade** process, not imposed externally.

---

**End of CRITIC_CONSTITUTION.md**