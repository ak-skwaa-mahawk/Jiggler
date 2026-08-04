#!/usr/bin/env python3
# manifold_gateway.py — Sovereign Perimeter Ingestion Pipeline (v1.2.2 Hardened)
import os
import sys
import json
import subprocess

# Force clean, absolute library insertion to prevent cached scope leakage
TARGET_DIR = os.path.expanduser("~/Tordial-GS-_Manifold/tools")
if TARGET_DIR not in sys.path:
    sys.path.insert(0, TARGET_DIR)

from signal_triage import SignalTriageUnit

def main():
    triage = SignalTriageUnit()
    
    # Capture payload from stdin or argument array
    raw_payload = ""
    if not sys.stdin.isatty():
        raw_payload = sys.stdin.read().strip()
    elif len(sys.argv) > 1:
        raw_payload = " ".join(sys.argv[1:]).strip()
        
    if not raw_payload:
        print("⚠️  [GATEWAY ERR]: Empty input stream.")
        sys.exit(1)
        
    print(f"🛰️  [INGRESS]: Evaluating raw stream boundary frame...")
    
    # Force call to authentic, patched regex matrix
    evaluation = triage.evaluate_signal(raw_payload)
    
    # Branch routing logic
    if evaluation["action_taken"] == "ISOLATE_AND_LOG":
        triage.log_quarantine(evaluation)
        print("🛑 [GATEWAY INTERCEPT]: Threats detected. Packet dropped and shunted to quarantine.")
        print(f"   ↳ Rule:   {evaluation.get('rule_triggered', 'UNKNOWN')}")
        print(f"   ↳ Reason: {evaluation.get('quarantine_reason', 'N/A')}")
        sys.exit(0)
        
    elif evaluation["action_taken"] == "PASS_TO_MANIFOLD":
        print("🟩 [GATEWAY PASS]: Stream verified clear. Enriching and routing to core...")
        
        enriched_data = {
            "raw_signal": raw_payload,
            "ingress_vector": "GATEWAY_v1.2.2",
            "triage_classification": evaluation["classification"]
        }
        
        core_script = os.path.expanduser("~/Tordial-GS-_Manifold/isst_toft_core.py")
        if not os.path.exists(core_script):
            core_script = "isst_toft_core.py"
            
        try:
            res = subprocess.run(
                [sys.executable, core_script],
                input=json.dumps(enriched_data),
                text=True,
                capture_output=True,
                check=True
            )
            print("📡 [CORE RESPONSE MATRIX]:")
            print(res.stdout.strip())
        except subprocess.CalledProcessError as err:
            print(f"❌ [GATEWAY CORE CRASH]: Pipeline breakdown: {err.stderr}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"❌ [GATEWAY ERR]: Execution engine error: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
