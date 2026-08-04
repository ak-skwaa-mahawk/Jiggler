# runtime/policy_api.py
from fastapi import APIRouter, HTTPException
from .runtime.loader import load_dynamic_rules
from .runtime.registry import PolicyRegistry

router = APIRouter()
registry = PolicyRegistry()

@router.post("/policy/reload")
def reload_policy():
    # keep hard rules always loaded
    from .runtime.loader import load_static_rules
    registry.rules.clear()
    for r in load_static_rules() + load_dynamic_rules():
        registry.register_rule(r)
    return {"status": "ok", "rules": len(registry.rules)}

@router.get("/policy/snapshot")
def policy_snapshot():
    return [
        {
            "rule_id": r.rule_id,
            "type": r.rule_type,
            "effect": r.effect.value,
            "priority": r.priority,
            "source": r.source,
            "version": r.version,
        }
        for r in registry.snapshot()
    ]