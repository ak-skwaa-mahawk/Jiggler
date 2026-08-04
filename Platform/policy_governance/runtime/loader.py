# policy_governance/runtime/loader.py
import json
from pathlib import Path
from .schema import PolicyRule, RuleEffect

BASE_DIR = Path(__file__).resolve().parents[1]

def load_json_rules(path: Path, source: str, default_priority: int) -> list[PolicyRule]:
    data = json.loads(path.read_text())
    rules = data["rules"] if "rules" in data else data  # support both styles
    out = []
    for idx, r in enumerate(rules):
        out.append(
            PolicyRule(
                rule_id=r["rule_id"],
                rule_type=r["rule_type"],
                effect=RuleEffect(r["effect"]),
                priority=r.get("priority", default_priority + idx),
                conditions=r["conditions"],
                metadata=r.get("metadata", {}),
                source=source,
                version=data.get("version"),
            )
        )
    return out

def load_static_rules() -> list[PolicyRule]:
    hard = BASE_DIR / "hard_rules"
    rules: list[PolicyRule] = []
    # functional goals as "goal" rules
    rules += load_json_rules(hard / "functional_goals.json", "hard_functional", 100)
    # rigid avoidances as "avoidance" rules
    rules += load_json_rules(hard / "rigid_avoidances.json", "hard_avoidance", 0)
    return rules

def load_dynamic_rules() -> list[PolicyRule]:
    dyn_dir = BASE_DIR / "dynamic_rules"
    rules: list[PolicyRule] = []
    for f in dyn_dir.glob("*.json"):
        rules += load_json_rules(f, f"dynamic:{f.name}", 50)
    return rules