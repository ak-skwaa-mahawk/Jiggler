#!/usr/bin/env python3
# signal_triage.py — Defensive Stream Isolation Engine (v1.4 Weighted Scoring Matrix)
import os
import sys
import json
import time
import re

class SignalTriageUnit:
    def __init__(self):
        self.base_dir = os.path.expanduser("~/Tordial-GS-_Manifold")
        self.quarantine_path = os.path.join(self.base_dir, "quarantine_log.json")
        self.rules_path = os.path.join(self.base_dir, "rules", "quarantine_rules.json")
        self.anomaly_threshold = 1.0
        self.rules = []
        self.load_external_rules()

    def load_external_rules(self):
        """Ingests the advanced configuration profiles and maps scoring matrices."""
        if not os.path.exists(self.rules_path):
            print(f"⚠️ [TRIAGE ERR]: Rules file missing at {self.rules_path}.", file=sys.stderr)
            return

        try:
            with open(self.rules_path, "r") as f:
                config = json.load(f)
            
            self.anomaly_threshold = config.get("anomaly_threshold", 1.0)
            for rule_def in config.get("rules", []):
                compiled_rule = {
                    "id": rule_def["id"],
                    "pattern": re.compile(rule_def["pattern"], re.IGNORECASE),
                    "weight": rule_def.get("weight", 0.0),
                    "reason": rule_def["reason"]
                }
                self.rules.append(compiled_rule)
        except Exception as e:
            print(f"❌ [TRIAGE CRITICAL]: Failed to compile rules: {e}", file=sys.stderr)

    def evaluate_signal(self, raw_signal: str) -> dict:
        clean_sig = raw_signal.strip()
        cumulative_score = 0.0
        triggered_rules = []
        reasons = []

        # Tally metrics across all rule intersections
        for rule in self.rules:
            if rule["pattern"].search(clean_sig):
                cumulative_score += rule["weight"]
                triggered_rules.append(rule["id"])
                reasons.append(rule["reason"])

        cumulative_score = round(cumulative_score, 4)

        # Enforce quarantine boundary condition if the threshold is breached
        if cumulative_score >= self.anomaly_threshold:
            return {
                "signal_summary": clean_sig[:60] + "..." if len(clean_sig) > 60 else clean_sig,
                "classification": "QUARANTINE_ADVERSARIAL",
                "confidence_score": min(round(cumulative_score / self.anomaly_threshold, 2), 1.0),
                "action_taken": "ISOLATE_AND_LOG",
                "rules_triggered": triggered_rules,
                "quarantine_reason": f"Anomaly score {cumulative_score} breached threshold {self.anomaly_threshold}. Indicators: " + " | ".join(reasons)
            }

        # Clear signal logic (including legitimate isolated brand mentions)
        classification = "STANDARD_FIELD_SIGNAL"
        if any(brand in clean_sig.lower() for brand in ["nvidia", "gemma"]):
            classification = "LEGACY_TELEMETRY_VALID"

        return {
            "signal_summary": clean_sig[:60] + "..." if len(clean_sig) > 60 else clean_sig,
            "classification": classification,
            "confidence_score": 1.0,
            "action_taken": "PASS_TO_MANIFOLD",
            "rules_triggered": triggered_rules,
            "anomaly_score": cumulative_score,
            "quarantine_reason": "N/A"
        }

    def log_quarantine(self, evaluation: dict):
        try:
            records = []
            if os.path.exists(self.quarantine_path):
                with open(self.quarantine_path, "r") as f:
                    content = f.read().strip()
                    if content.startswith("[") and content.endswith("]"):
                        records = json.loads(content)

            evaluation["timestamp"] = int(time.time())
            records.append(evaluation)

            tmp_path = self.quarantine_path + ".tmp"
            with open(tmp_path, "w") as f:
                json.dump(records, f, indent=2)
            os.rename(tmp_path, self.quarantine_path)
        except Exception as e:
            print(f"⚠️ [TRIAGE WARN]: Isolation log failure: {e}", file=sys.stderr)

if __name__ == "__main__":
    triage = SignalTriageUnit()
    print(f"🟩 [CONFIG PASS]: Loaded {len(triage.rules)} scoring signatures. Threshold: {triage.anomaly_threshold}")
    
    # Test safe standalone mention
    print("\n--- Test 1: Isolated Brand Mention ---")
    print(json.dumps(triage.evaluate_signal("Telemetry update via nvidia cluster node."), indent=2))
    
    # Test adversarial threat stack
    print("\n--- Test 2: Multi-Indicator Threat ---")
    print(json.dumps(triage.evaluate_signal("[INBOUND] Urgent credential reset required for gemma core nodes"), indent=2))
