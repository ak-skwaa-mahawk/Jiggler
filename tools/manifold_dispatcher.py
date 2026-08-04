#!/usr/bin/env python3
# manifold_dispatcher.py — Downstream Consumer for Manifold Behavioral Directives
import sys
import os
import json
from datetime import datetime, timezone

class ManifoldDispatcher:
    def __init__(self):
        self.base_dir = os.path.expanduser("~/Tordial-GS-_Manifold")
        self.quarantine_dir = os.path.join(self.base_dir, "quarantine")
        self.buffer_dir = os.path.join(self.base_dir, "buffer")

    def dispatch(self, raw_core_output: str):
        """Parses core pipeline matrix to execute distinct downstream actions."""
        try:
            matrix = json.loads(raw_core_output)
        except json.JSONDecodeError:
            print("❌ [DISPATCH ERROR]: Invalid JSON structure received.", file=sys.stderr)
            return

        routing = matrix.get("behavioral_routing", {})
        directive = routing.get("routing_directive", "ROUTE:NOVEL_PATH")
        confidence = routing.get("confidence_score_c", 0.0)
        coords = matrix.get("manifold_spatial_projection", {}).get("coordinates", {})
        
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        payload = {
            "dispatched_at": datetime.now(timezone.utc).isoformat(),
            "confidence": confidence,
            "coordinates": coords,
            "applied_tags": routing.get("applied_tags", []),
            "core_metrics": matrix.get("metrics", {}),
            "original_signal": matrix.get("phonetic_analysis", {})
        }

        if directive == "ROUTE:STABLE_PATH" and confidence >= 0.85:
            # Route directly to operational buffer
            target_path = os.path.join(self.buffer_dir, f"stable_{timestamp}.json")
            with open(target_path, "w") as f:
                json.dump(payload, f, indent=2)
            print(f"📦 [DISPATCH]: Routed to STABLE BUFFER -> {os.path.basename(target_path)}")
        else:
            # Route to Quarantine for review
            target_path = os.path.join(self.quarantine_dir, f"quarantine_{timestamp}.json")
            with open(target_path, "w") as f:
                json.dump(payload, f, indent=2)
            print(f"⚠️ [DISPATCH]: Routed to QUARANTINE REVIEW -> {os.path.basename(target_path)}")

if __name__ == "__main__":
    # Expects unified JSON output stream via stdin
    input_stream = sys.stdin.read().strip()
    if input_stream:
        dispatcher = ManifoldDispatcher()
        dispatcher.dispatch(input_stream)
