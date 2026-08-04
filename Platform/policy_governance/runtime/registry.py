# policy_governance/runtime/registry.py
from typing import Callable, Dict, Any, List
from .schema import PolicyRule, RuleEffect

EvaluatorFn = Callable[[PolicyRule, Dict[str, Any]], Dict[str, Any] | None]

class PolicyRegistry:
    def __init__(self):
        self.rules: List[PolicyRule] = []
        self.evaluators: Dict[str, EvaluatorFn] = {}

    def register_rule(self, rule: PolicyRule):
        self.rules.append(rule)

    def register_evaluator(self, rule_type: str, fn: EvaluatorFn):
        self.evaluators[rule_type] = fn

    def snapshot(self) -> List[PolicyRule]:
        return sorted(self.rules, key=lambda r: r.priority)