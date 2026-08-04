import json
import os
import tordial_gs_manifold

class LocalSovereignChain:
    def __init__(self, ledger_file):
        self.ledger_file = os.path.expanduser(ledger_file)
        self.native_bridge = tordial_gs_manifold.PySubstrateMeshBus(1.0, self.ledger_file)
        self.load_and_rehydrate_ledger()

    def load_and_rehydrate_ledger(self):
        if not os.path.exists(self.ledger_file):
            return
            
        try:
            with open(self.ledger_file, "r") as f:
                blocks_data = json.load(f)
                
            for b in blocks_data:
                ts = b.get("timestamp", 0)
                sig = b.get("identity_signature", 0)
                payload = b.get("payload", {}) or b.get("PAYLOAD", {})
                
                record_type_str = payload.get("record_type") or payload.get("RECORD_TYPE", "")
                raw_fallback = payload.get("fallback_raw_data") or payload.get("FALLBACK_RAW_DATA", "")
                
                # Fixed: Variable correctly named raw_fallback to align with extracted token
                if "MACRO" in str(record_type_str) or "STRUCTURED_MACRO_JSON" in str(raw_fallback) or len(str(raw_fallback)) > 5:
                    if "GLOBAL_PHASE_X" in str(raw_fallback) or "global_phase_x" in str(raw_fallback):
                        self.native_bridge.append_macro_snapshot_block(ts, sig, str(raw_fallback))
                        continue
                
                raw_telemetry = payload.get("wave_telemetry_raw") or payload.get("WAVE_TELEMETRY_RAW", "")
                self.native_bridge.append_wave_telemetry_block(ts, sig, str(raw_telemetry))
                    
        except Exception as e:
            print(f"⚠️ [LEDGER ENGINE]: Error during line-item rehydration: {e}", flush=True)
