"""
core/loop_79hz.py
Main 79 Hz control loop with Vault gating.

Every action proposed by Platform passes through vault.gate_action before
being applied. Actions that are DENY-ed are logged and dropped. Actions that
are MODIFY-ed are patched and applied. Only ALLOW or patched-MODIFY actions
reach apply_action.
"""

from __future__ import annotations

import logging
import time
from typing import Callable

from vault.client import VaultClient
from vault.schemas import ActionProposal, GateDecision, MetricSnapshot

log = logging.getLogger(__name__)

# ── Tick interval ──────────────────────────────────────────────────────────────

TICK_HZ      = 79
TICK_INTERVAL = 1.0 / TICK_HZ          # ~12.658 ms


# ── Stub interfaces (replace with your real implementations) ───────────────────

class PlatformState:
    """Replace with your actual state object."""

    def collect_metrics(self) -> list[MetricSnapshot]:
        raise NotImplementedError

    def log_gate_denial(self, action: ActionProposal, reason: str) -> None:
        log.warning(
            "GATE DENIED  action_id=%s  actor=%s  type=%s  reason=%s",
            action.action_id,
            action.actor,
            action.action_type,
            reason,
        )

    def log_gate_modify(self, original: ActionProposal, patched: ActionProposal, reason: str) -> None:
        log.info(
            "GATE MODIFIED  action_id=%s  patch=%s  reason=%s",
            original.action_id,
            patched.params,
            reason,
        )


def propose_actions(state: PlatformState, metrics: list[MetricSnapshot]) -> list[ActionProposal]:
    """Return candidate actions for this tick. Replace with your real planner."""
    raise NotImplementedError


def apply_action(state: PlatformState, action: ActionProposal) -> None:
    """Apply a single gated action to hardware/sim. Replace with your real actuator."""
    raise NotImplementedError


# ── Core tick ──────────────────────────────────────────────────────────────────

def tick(state: PlatformState, vault: VaultClient, metric_buffer: list[MetricSnapshot]) -> PlatformState:
    """
    One 79 Hz tick.

    1. Collect metrics from all subsystems.
    2. Push metrics to Vault (non-blocking; failure is logged, not fatal).
    3. Propose candidate actions.
    4. Gate each action through Vault.
    5. Apply only ALLOW / MODIFY-patched actions.

    Returns the (mutated) state.
    """

    # 1. Collect
    snapshots = state.collect_metrics()
    if not snapshots:
        log.debug("tick: no metrics collected this cycle")

    # 2. Buffer + push
    metric_buffer.extend(snapshots)
    if not vault.push_metrics(snapshots):
        log.warning("tick: metric push failed — Vault operating on stale data")

    # 3. Propose
    proposed = propose_actions(state, snapshots)

    # 4. Gate + 5. Apply
    for action in proposed:
        decision: GateDecision = vault.gate_action(action, metric_buffer)

        if decision.decision == "ALLOW":
            apply_action(state, action)

        elif decision.decision == "MODIFY":
            patched = action.with_patch(decision.patch)
            state.log_gate_modify(action, patched, decision.reason)
            apply_action(state, patched)

        elif decision.decision == "DENY":
            state.log_gate_denial(action, decision.reason)

        else:
            # Unknown decision — treat as DENY
            log.error(
                "tick: unknown gate decision '%s' for action %s — denying",
                decision.decision,
                action.action_id,
            )

    return state


# ── Run loop ───────────────────────────────────────────────────────────────────

def run(
    state: PlatformState,
    vault: VaultClient,
    max_metric_buffer: int = 200,
    stop_fn: Callable[[], bool] | None = None,
) -> None:
    """
    Run the 79 Hz loop until stop_fn() returns True (or forever if None).

    Timing: uses monotonic deadline tracking so jitter in one tick doesn't
    accumulate across ticks.
    """
    metric_buffer: list[MetricSnapshot] = []
    deadline = time.monotonic()

    log.info("Starting 79 Hz loop (tick interval %.4f s)", TICK_INTERVAL)

    with vault:
        while True:
            if stop_fn and stop_fn():
                log.info("Stop signal received — exiting loop")
                break

            tick(state, vault, metric_buffer)

            # Trim buffer to prevent unbounded growth
            if len(metric_buffer) > max_metric_buffer:
                metric_buffer = metric_buffer[-max_metric_buffer:]

            # Deadline-based sleep: absorbs tick overruns without drift
            deadline += TICK_INTERVAL
            sleep_for = deadline - time.monotonic()
            if sleep_for > 0:
                time.sleep(sleep_for)
            else:
                log.warning(
                    "tick overrun: %.3f ms behind schedule",
                    abs(sleep_for) * 1000,
                )
                deadline = time.monotonic()   # re-anchor to avoid spiral
