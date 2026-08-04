# Human-in-the-Loop (HITL) Alignment Manual
## Cognitive Interception Operations and Value Verification Runs

This guide provides instructions for system operators monitoring the cognitive firewall and managing human-in-the-loop validation checkpoints.

### 1. Cognitive Firewall Interception
The platform utilizes an active `ConsciousnessReferee` to evaluate incoming model data strings and tracking inputs. When an autonomous node experiences local semantic drift (hallucination), the anomaly registers as a sharp spike in variational action energy ($E_{\text{variational}}$).

### 2. The Pros and Cons Weight Resolution Process
When a transaction is caught by the firewall, it is passed to the human-in-the-loop scoring matrix. System operators evaluate candidate outputs using fixed weights:

| Criterion | Pro Weight | Con Weight | Action Boundary |
| :--- | :--- | :--- | :--- |
| **Sovereignty Alignment** | $+1.5$ | $-2.0$ | Protects machine boundary isolation lines |
| **Cryptographic Certainty**| $+2.0$ | $-2.5$ | Mandates ZK proof validity before commits |
| **Telemetry Stability** | $+1.2$ | $-1.8$ | Regulates low entropy variance under load |

* **Automated Clearance Score:** $\ge 1.0$ (The transaction commits natively to the timeline).
* **Halt Threshold Score:** $< 1.0$ (Triggers a `HALT_FOR_HUMAN_OVERRIDE` event, locking process states until a verified operator private-key signature is applied).
