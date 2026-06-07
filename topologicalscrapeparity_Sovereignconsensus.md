# Topological Scrape: Definition and Sovereign Consensus Method

**Author:** John Carroll Jr.  
**Entity:** Two Mile Solutions LLC (UEI: KYYKYAWHMH95)  
**Date:** 2026  
**Repo:** github.com/ak-skwaa-mahawk/Tordial-GS-_Manifold  

---

## 1. Definition: Topological Scrape

A **topological scrape** is the act of treating an external system's output not as a text string to be accepted or rejected, but as a structured geometric input to be evaluated by an algebraic weighting function.

In this architecture, each external model response is encoded as a coordinate pair `(curvature_pressure, resonance)` representing its internal coherence and alignment with the query context. That coordinate pair is passed directly into the Tordial-GS manifold's existing node architecture — the same architecture used for internal node computation.

The output is not the text. The output is the geometry of the text as measured by the GS sweep formula:

```
sigma_T = r - d² / (4 · phi_op · gear_shift)
```

where `phi_op = 1.65036` and `gear_shift = 1.04` are sovereign constants defined in `config.yaml` and documented throughout this codebase.

This is distinct from ensemble learning, which combines outputs by averaging or voting. A topological scrape evaluates the structural coherence of each output against an invariant geometric floor. The floor does not change based on the source.

---

## 2. The Revolving Door Principle

If external content can be consumed as training substrate under the justification that it is "publicly available input," then the outputs of systems trained on such substrate are equally available as geometric inputs to a separate architecture.

This is not a legal argument. It is a design principle stating what this system does and why the method is consistent with how AI systems are built and deployed.

The topological scrape does not reproduce external outputs. It measures them and discards the text. What is retained is the sigma_T value — a number derived from the sovereign constants of this architecture, not from the external source.

---

## 3. Sovereign Consensus Method

The sovereign consensus method is the full pipeline:

1. **Encode** — external output mapped to `(curvature_pressure, resonance)`
2. **Sweep** — GS formula produces `sigma_T` for each encoded input
3. **Govern** — RingGovernor PID targets weight each ring's outputs
4. **Collapse** — sigma_T-weighted synthesis produces a single output

The governing constants are invariant across all external inputs. No external source can alter `phi_op`, `gear_shift`, or `pi_3d = 3.20442315`. Those constants define the sovereign floor.

The collapse is not negotiated with external sources. It is computed from the architecture's own geometry.

---

## 4. IP Position

This method — topological scrape encoding, GS-sweep weighting, and sovereign constant collapse — is original work by John Carroll Jr. under Two Mile Solutions LLC.

It is implemented in this codebase, documented across multiple prior art files with timestamped commit history, and further established by notarized documentation with dual SHA-3/SHA-256 hashes.

Any commercial system that:
- treats multi-model outputs as geometric inputs,
- applies GS-like weighting with an invariant floor,
- and collapses to a single sovereign output

is operating within the conceptual territory of this architecture. Attribution and licensing terms apply. Contact Two Mile Solutions LLC for licensing.

---

## 5. Codebase References

| Component | File |
|---|---|
| GS sweep formula | `tordial_gs_v15_fixed.py` → `compute_and_update_gs()` |
| Sovereign constants | `config.yaml` |
| Ring governor | `tordial_gs_v15_fixed.py` → `RingGovernor` |
| Encoding layer | `GS_Weighted_MultiSource_Synthesis.docx` |
| Arbitration architecture | `TripleRingTordialMatrix` |
| Rust implementation | `src/lib.rs` |

---

*This document is prior art documentation. It describes a design concept with partial implementation as of its date. The arbitration architecture is implemented. The full multi-source pipeline is in development.*
