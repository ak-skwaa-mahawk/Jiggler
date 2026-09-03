# Tordial Manifold: Autonomous XRPL Telemetry Settlement Pipeline

High-throughput ingestion and settlement framework linking dynamic network strain telemetry to the XRPL Testnet ledger via non-linear dynamical throttling.

## Pipeline Architecture

```text
[manifold-stream-emitter]
          │ (UDP:9999)
          ▼
 [tools/udp_listener.py] ────► [BurstEngine Invariant Evaluator]
                                         │
                         ┌───────────────┴───────────────┐
                         ▼                               ▼
                 [THROTTLED GATES]               [DISPATCH_BURST]
             (Strain > 75% | λ > 0.0)                    │ (WS:8765)
                         │                               ▼
                 (No Transaction)             [settlement_worker.py]
                                                         │ (JSON-RPC)
                                                         ▼
                                                [XRPL Testnet Ledger]
                                                         │
                                                         ▼
                                            ~/.manifold_xrpl_ledger.jsonl
                                            ~/.manifold_settlements.csv
```

## Core Modules

* **Telemetry Ingestion (`tools/udp_listener.py`)**: Binds to `127.0.0.1:9999` (UDP). Ingests stochastic strain packets and forwards state vectors to `BurstEngine`.
* **Settlement Daemon (`tools/settlement_worker.py`)**: Subscribes to `ws://127.0.0.1:8765`. Signs and submits transactions using `xrpl-py` against `s.altnet.rippletest.net:51234`.
* **Telemetry Generator (`tools/pipeline_scripts/manifold-stream-emitter`)**: Streams phase-drift telemetry vectors across simulated nodes.
* **Ledger Inspector (`tools/pipeline_scripts/manifold-ledger`)**: Formatted CLI visualizer displaying live on-chain balances, transaction hashes, explorer links, and `--csv` exports.

## Safety Assertions

1. **Overstrain Boundary:** Effective strain >= 75% triggers `THROTTLED_OVERSTRAINED` with 0 drops allocated.
2. **Lyapunov Stability:** Positive exponents (lambda > 0) indicate chaotic network divergence and trigger `THROTTLED_CHAOTIC`.
3. **Execution Invariant:** Non-reentrant sequence handling prevents ledger sequence number collision and ensures single-attempt settlement.

## Quickstart Controls

```bash
# Boot pipeline daemons
wake-all

# Start background telemetry stream
start-manifold-stream

# View on-chain settlements and wallet balances
manifold-ledger

# Dump persistent audit log to CSV
manifold-ledger --csv

# Shutdown pipeline daemons cleanly
sleep-all
```
