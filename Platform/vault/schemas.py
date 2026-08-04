"""
vault/schemas.py
Canonical types for all Vault ↔ Platform communication.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


# ── Metric snapshot ────────────────────────────────────────────────────────────

@dataclass
class MetricSnapshot:
    timestamp: float
    source: str
    metrics: dict[str, float]

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "source": self.source,
            "metrics": self.metrics,
        }


# ── Action proposal ────────────────────────────────────────────────────────────

@dataclass
class ActionProposal:
    action_id: str
    actor: str
    action_type: str                        # renamed from "type" (reserved word)
    params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "action_id": self.action_id,
            "actor": self.actor,
            "type": self.action_type,
            "params": self.params,
        }

    def with_patch(self, patch: dict[str, Any]) -> "ActionProposal":
        """Return a new ActionProposal with params overridden by patch."""
        return ActionProposal(
            action_id=self.action_id,
            actor=self.actor,
            action_type=self.action_type,
            params={**self.params, **patch},
        )


# ── Gate decision ──────────────────────────────────────────────────────────────

ALLOW  = "ALLOW"
DENY   = "DENY"
MODIFY = "MODIFY"

@dataclass
class GateDecision:
    action_id: str
    decision: str           # ALLOW | DENY | MODIFY
    reason: str = ""
    patch: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def deny_unreachable(cls, action_id: str) -> "GateDecision":
        return cls(
            action_id=action_id,
            decision=DENY,
            reason="vault_unreachable",
        )

    @classmethod
    def deny_empty_metrics(cls, action_id: str) -> "GateDecision":
        return cls(
            action_id=action_id,
            decision=DENY,
            reason="empty_metric_context",
        )

    @classmethod
    def from_response(cls, data: dict) -> "GateDecision":
        return cls(
            action_id=data["action_id"],
            decision=data["decision"],
            reason=data.get("reason", ""),
            patch=data.get("patch", {}),
        )
