# policy_governance/runtime/schema.py
from enum import Enum
from typing import Any, Dict, List, Optional, Literal

class RuleEffect(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    MODIFY = "modify"
    FLAG = "flag"

RuleType = Literal["goal", "avoidance", "constraint", "transform", "telemetry"]

class PolicyRule(BaseException):
    def __init__(
        self,
        rule_id: str,
        rule_type: RuleType,
        effect: RuleEffect,
        priority: int,
        conditions: Dict[str, Any],
        metadata: Dict[str, Any] | None = None,
        source: str | None = None,
        version: str | None = None,
    ):
        self.rule_id = rule_id
        self.rule_type = rule_type
        self.effect = effect
        self.priority = priority
        self.conditions = conditions
        self.metadata = metadata or {}
        self.source = source
        self.version = version