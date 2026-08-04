# policy_governance/runtime/evaluator.py
from typing import Dict, Any
from .registry import PolicyRegistry
from .schema import RuleEffect

def evaluate_action(registry: PolicyRegistry, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    context: {
      "host": {...},
      "action": {...},
      "planner_trace": {...},
      "walker_state": {...},
      "critic_scores": {...}
    }
    """
    decision = {
        "allowed": True,
        "modified_action": None,
        "flags": [],
        "matched_rules": [],
    }

    rules = registry.snapshot()

    for rule in rules:
        evaluator = registry.evaluators.get(rule.rule_type)
        if not evaluator:
            continue

        result = evaluator(rule, context)
        if result is None:
            continue

        decision["matched_rules"].append(rule.rule_id)

        if rule.effect == RuleEffect.DENY:
            decision["allowed"] = False
            decision["flags"].append({"rule": rule.rule_id, "reason": "deny"})
            break

        if rule.effect == RuleEffect.MODIFY:
            decision["modified_action"] = result.get("action", decision["modified_action"])

        if rule.effect == RuleEffect.FLAG:
            decision["flags"].append({"rule": rule.rule_id, **result})

    return decision