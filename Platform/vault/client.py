"""
vault/client.py
HTTP bridge to SovereignVault.  Swap transport by subclassing VaultClient.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Optional

import requests

from vault.schemas import (
    ActionProposal,
    GateDecision,
    MetricSnapshot,
)

log = logging.getLogger(__name__)


class VaultClientError(Exception):
    """Raised when Vault returns a non-2xx response."""


class VaultClient:
    """
    Thin HTTP client for SovereignVault.

    Fail-closed by default: if Vault is unreachable, every action is DENY-ed.
    Set fail_open=True only in development/testing.
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 0.05,       # 50 ms — must fit inside 79 Hz tick (~12.6 ms headroom)
        context_window: int = 10,     # how many recent snapshots to send with each gate call
        fail_open: bool = False,      # True → ALLOW on Vault failure (dev only)
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._context_window = context_window
        self._fail_open = fail_open
        self._session = requests.Session()   # connection pooling across ticks

    # ── Factory ────────────────────────────────────────────────────────────────

    @classmethod
    def from_config(cls, path: str) -> "VaultClient":
        with open(path) as f:
            cfg = json.load(f)
        return cls(
            base_url=cfg["base_url"],
            timeout=cfg.get("timeout", 0.05),
            context_window=cfg.get("context_window", 10),
            fail_open=cfg.get("fail_open", False),
        )

    # ── Metrics push ───────────────────────────────────────────────────────────

    def push_metrics(self, snapshots: list[MetricSnapshot]) -> bool:
        """
        Push metrics to Vault.

        Returns True on success, False on failure.
        Failures are logged as warnings — caller decides whether to halt.
        """
        if not snapshots:
            log.debug("push_metrics called with empty list — skipped")
            return True

        payload = {"metrics": [s.to_dict() for s in snapshots]}
        try:
            r = self._session.post(
                f"{self._base_url}/metrics",
                json=payload,
                timeout=self._timeout,
            )
            r.raise_for_status()
            return True
        except requests.Timeout:
            log.warning("push_metrics: Vault timeout after %.3fs", self._timeout)
        except requests.HTTPError as e:
            log.warning("push_metrics: HTTP %s — %s", e.response.status_code, e)
        except Exception as e:
            log.warning("push_metrics: unexpected error — %s", e)
        return False

    # ── Gate action ────────────────────────────────────────────────────────────

    def gate_action(
        self,
        action: ActionProposal,
        recent_metrics: list[MetricSnapshot],
    ) -> GateDecision:
        """
        Ask Vault whether an action is permitted under current metrics + policy.

        Fail-closed by default (DENY on any error).
        """
        if not recent_metrics:
            log.warning(
                "gate_action: no metric context for action %s — denying",
                action.action_id,
            )
            return GateDecision.deny_empty_metrics(action.action_id)

        context = recent_metrics[-self._context_window:]
        payload = {
            "action": action.to_dict(),
            "context_metrics": [s.to_dict() for s in context],
        }

        try:
            r = self._session.post(
                f"{self._base_url}/gate",
                json=payload,
                timeout=self._timeout,
            )
            r.raise_for_status()
            return GateDecision.from_response(r.json())

        except requests.Timeout:
            log.error(
                "gate_action: Vault timeout (%.3fs) for action %s — %s",
                self._timeout,
                action.action_id,
                "ALLOW (fail-open)" if self._fail_open else "DENY (fail-closed)",
            )
        except requests.HTTPError as e:
            log.error(
                "gate_action: HTTP %s for action %s — %s",
                e.response.status_code,
                action.action_id,
                "ALLOW (fail-open)" if self._fail_open else "DENY (fail-closed)",
            )
        except Exception as e:
            log.error(
                "gate_action: unexpected error for action %s: %s — %s",
                action.action_id,
                e,
                "ALLOW (fail-open)" if self._fail_open else "DENY (fail-closed)",
            )

        if self._fail_open:
            return GateDecision(
                action_id=action.action_id,
                decision="ALLOW",
                reason="vault_unreachable__fail_open",
            )
        return GateDecision.deny_unreachable(action.action_id)

    # ── Cleanup ────────────────────────────────────────────────────────────────

    def close(self) -> None:
        self._session.close()

    def __enter__(self) -> "VaultClient":
        return self

    def __exit__(self, *_) -> None:
        self.close()
