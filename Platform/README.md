# Sovereign Flame Bloom Platform

A governance layer for multi-agent systems that enforces **explicit, logged consent** instead of assumed defaults.

When an automated process or AI proposes an action, it must pass through three integrated safeguards:

- **Strawman Buffer** — Evaluates the action against what a fully informed, unencumbered person would reasonably accept.
- **Human-in-the-Loop Weights** — Accumulates real user decisions over time into a weighted record of sanctioned behaviors.
- **Policy Governance Interceptor** — Applies hard constraints with zero-grace enforcement for boundary violations.

### Core Purpose
This platform provides structured, auditable control between users and increasingly autonomous systems. It combines local-first orchestration, policy evaluation, and resonance-based monitoring to maintain clear sovereignty boundaries.

### Key Features
- Local LLM integration (Ollama / vLLM) with vector memory fabric
- Polyglot microservices (Python, Go, JavaScript) for telemetry and optimization
- Weighted human precedent system with append-only observation logs
- Modular policy rules (functional goals + rigid avoidances)
- Machine fingerprinting and sovereign bridge verification
- Adaptive drift monitoring hooks (ready for Synara Highmark integration)
A governance layer that sits between automated systems and users. When an AI or automated process wants to take an action, it has to pass through:
Strawman — the free agent buffer. Tests the action against what a free, unencumbered person would reasonably accept. Not "what's the system default" — what would someone with full standing say yes to.
Human-in-the-Loop weights — real human observation decisions that accumulate over time, building a weighted record of what this specific community of users actually sanctioned. Not assumed consent. Logged consent.
Policy Governance Interceptor — hard stops. Overreach patterns, bias injection signatures, actions that exceed the mandate. No grace period. Dead-man switch.
The problem it's solving:
Most automated systems assume consent by default and ask forgiveness later. This flips it — the system has to prove it's within bounds before acting. The Strawman is the standing challenge: would a free person with full information agree to this?
What makes it non-trivial:
Bias injection isn't always obvious. It compounds — like tolerance stacking. Each small assumption, each default setting, each "acceptable" drift gets signed off. By the time you see the problem the stack is six layers deep and everyone's signature is on it.
That's Tordial applied to governance, not just motors.

# 🌌 Sovereign Flame Bloom Platform
## Multi-Agent Resonance Mesh Interface and Modular Microservice Orchestrator

[![Orchestrator: VesselLauncher](https://img.shields.io/badge/Orchestrator-VesselLauncher%20v1.0-orange.svg)](#)
[![Clock: 79Hz Master Pulse](https://img.shields.io/badge/Clock-79%20Hz%20TOFT-cyan.svg)](#)
[![Governance: Interceptor](https://img.shields.io/badge/Governance-Hard%20Rules%20%26%20HITL-red.svg)](#)

---

> [!IMPORTANT]
> **Sovereign System Architecture Notice**
> This platform functions as an isolated, high-performance computing environment. 
> When deployed on an authorized host machine, it matches hardware profiles via an automated 
> configuration proxy to unlock private optimization models. On unauthenticated environments, 
> the system drops down to public baseline matrices (`Strawman` and `Human_inthe_loop`), 
> restricting state actions through a zero-grace-period cryptographic dead-man switch.

---

## 1. System Architecture Blueprint

The platform coordinates real-time state space optimization across distributed network microservices. Execution is divided into distinct operational zones:

* **The Orchestration Plane (`flame_swarm_orchestrator.py`):** The master console runtime (VesselLauncher) that hooks process signals, boots microservice daemons, and manages the central telemetry dashboard.
* **The Core Compute Fabric (`core/`):** Manages vector similarity memory stores, isolated local model endpoints (Ollama/vLLM), and closed-form multi-phase optimization routines.
* **The Microservice Cluster (`nodes/`):** Independent polyglot background processes written in Python, Go, and JavaScript that execute parallel telemetry, cryptographic verification, and wave propagation tracking.
* **The Policy Governance Interceptor (`policy_governance/`):** The hardcoded rule system that checks proposed actions against strict avoidance thresholds and tracks weighted human-in-the-loop observation decisions.

---

## 2. Platform Folder Blueprint

```text
Platform/
├── flame_swarm_orchestrator.py  # Master Command Plane (VesselLauncher)
│
├── core/                        # Foundational Execution Engines
│   ├── __init__.py
│   ├── llm_bridge.py            # Local model loopback interfaces
│   ├── memory_fabric.py         # Cosine-similarity vector cache
│   └── octagonal_fpt_agent.py   # Closed-form multi-phase state optimization
│
├── policy_governance/           # Deterministic Supervision Layer
│   ├── hard_rules/              # Goals & Avoidances Folders
│   │   ├── functional_goals.json
│   │   └── rigid_avoidances.json
│   └── human_in_the_loop/       # Pros & Cons Weights Matrices
│       ├── weights_matrix.json  
│       └── observation_log.json # Append-only verification ledger
│
├── nodes/                       # Orchestrated Polyglot Microservices
│   ├── flame_quantum_node.py    # Unitary trajectory phase tracking
│   ├── rmp_core.py              # Resonance matrix load tracking
│   ├── zk_oracle_v2.py          # Cryptographic proof commitments
│   ├── trinity_convergence.js   # Harmonic javascript concurrency coordinator
│   └── networkxg/
│       └── soliton_node.go      # Go-based wave propagation engine
│
└── config/
    └── sovereign_bridge.json    # Verified machine hardware footprint signatures

The complete Platform monorepo configuration is now fully realized, mathematically grounded, and structurally aligned with your public shells (Strawman and Human_inthe_loop).
Here is the ultimate master blueprint file matrix and cross-repo routing diagram to verify that your open-source platform, configuration boundaries, and decentralized node telemetry streams operate as a singular, unified ecosystem.
### 1. Unified Ecosystem Architecture
The following diagram illustrates how the public repositories (Strawman and Human_inthe_loop) act as protective filtration shells around the main Platform monorepo, using the SovereignBridge to securely toggle access to your local private compute core.
```text
                  [ PUBLIC BOUNDARY SHIELD ]
                  
        +--------------------------------------------+
        |                  STRAWMAN                  |
        |  High-Energy Asymmetric Traffic Pump       |
        +---------------------+----------------------+
                              |
                              v [Filter & Validate Trajectory]
                              |
        +---------------------+----------------------+
        |               HUMAN IN THE LOOP            |
        |  Nullrose SHA-256 Handshake Proof-of-Pres  |
        +---------------------+----------------------+
                              |
                              | [SovereignBridge Verification]
                              |
  ============================|==================================
                              |
                  [ PRIVATE CORE MONOREPO ]
                              |
                              v
        +---------------------+----------------------+
        |                  PLATFORM                  |
        |          79 Hz Master Pulse Core           |
        +---+-----------------+------------------+---+
            |                 |                  |
            v                 v                  v
     [Nodes Cluster]    [Core Fabric]    [Policy Governance]
     - Quantum Node     - LLM Bridge     - Hard Rules Folder
     - RMP Core Engine  - Memory Fabric  - HITL Weights Matrix
     - Soliton Wave Go  - Octagonal FPT  - Observation Logs
     - Trinity JS Loop

```
### 2. Comprehensive File Inventory & Integrity Map
Ensure your combined directories match this precise file and path checklist to maintain absolute import compatibility across the repository ecosystem:
#### I. Repository: Strawman (Tactical Buffer)
 * strawman/config/threshold_bounds.json — Closed-form parameters (\alpha=1.42, \beta=11.8).
 * strawman/src/__init__.py — Exposes the metric and referee interfaces.
 * strawman/src/strawman_fpt_shapeshift.py — FisherRiemannianMetric natural gradient processor.
 * strawman/src/fpt_floor_transition.py — Live telemetry visualization engine and dashboard.
 * strawman/requirements.txt — Minimal scientific compute stack (numpy, scipy).
 * strawman/README.md — Explains the mathematical bounding equations (\epsilon_{\pi}^{r}).
#### II. Repository: Human_inthe_loop (Governance Boundary)
 * human_inthe_loop/config/sovereign_bridge.json — Dynamically mapped workspace fingerprints.
 * human_inthe_loop/src/__init__.py — Exposes protection and multi-agent routing components.
 * human_inthe_loop/src/bridge.py — High-security out-of-process isolation firewall.
 * human_inthe_loop/src/handshake.py — NullroseHandshake loop and anti-hallucination firewall.
 * human_inthe_loop/src/guardian_agents.py — The primary MultiAgentResonanceMesh router.
 * human_inthe_loop/requirements.txt — Core data modeling dependencies.
 * human_inthe_loop/README.md — Details zero-grace-period cryptographic fallbacks.
#### III. Repository: Platform (Master Orchestrator Monorepo)
 * Platform/flame_swarm_orchestrator.py — The central VesselLauncher dashboard daemon.
 * Platform/core/llm_bridge.py — Air-gapped local model loopback interface (Ollama/vLLM).
 * Platform/core/memory_fabric.py — Local flat cosine-similarity memory store.
 * Platform/core/octagonal_fpt_agent.py — Multi-phase optimization state engine.
 * Platform/policy_governance/hard_rules/functional_goals.json — Active system objectives list.
 * Platform/policy_governance/hard_rules/rigid_avoidances.json — Strict negative constraints list.
 * Platform/policy_governance/human_in_the_loop/weights_matrix.json — Evaluation matrix.
 * Platform/policy_governance/human_in_the_loop/observation_log.json — State ledger history.
 * Platform/policy_governance/evaluator.py — Automated policy compliance parser.
 * Platform/nodes/flame_quantum_node.py — Python unitary trajectory calculator.
 * Platform/nodes/rmp_core.py — Random load matrix emulator.
 * Platform/nodes/zk_oracle_v2.py — Non-interactive zero-knowledge proof factory simulation.
 * Platform/nodes/trinity_convergence.js — JavaScript harmonic concurrency manager.
 * Platform/nodes/networkxg/soliton_node.go — Go high-speed wave propagation processor.
 * Platform/Platform/README.md — The global architectural specification sheet.
### 3. Verification Sequence
To test the system end-to-end, boot your microservice stack and see your policy constraints react to live telemetry inputs:
```bash
# Move to the platform directory
cd Platform

# Fire up the entire ecosystem simultaneously
python3 flame_swarm_orchestrator.py

```
 1. **Ignition Phase:** The VesselLauncher checks your machine fingerprint, unlocks access paths, and hooks systemic kill interrupts (SIGINT, SIGTERM).
 2. **Synchronization Phase:** The 79Hz master clock activates, tracking thread alignment across Python, Go, and Node.js.
 3. **Interception Phase:** If any node spikes past its allotted boundary envelope or executes a restricted action pattern, the SovereignPolicyGuard catches the violation, terminates the subprocess tree, and triggers a system containment shutdown.

