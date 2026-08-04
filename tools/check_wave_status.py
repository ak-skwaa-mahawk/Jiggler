#!/usr/bin/env python3
import sys
import os
import json
import tools.ledger_engine
import tordial_gs_manifold

def main():
    live_state_path = os.path.expanduser("~/Tordial-GS-_Manifold/.manifold_live.json")
    
    if os.path.exists(live_state_path):
        try:
            with open(live_state_path, "r") as f:
                data = json.load(f)
            print("🟢 [LIVE COUPLED GLOBAL FIELD ACTIVE]")
            print(f"STEP:{data['step']:03d}|TIME:{data['simulated_time']:.2f}s|POSITION:{data['position']:+.6f}|VELOCITY:{data['velocity']:+.6f}")
            print(f"MACRO_FIELD_X:{data['global_phase_x']:+.4f}|MACRO_FIELD_Y:{data['global_phase_y']:+.4f}|LYAPUNOV_EXP:{data['effective_lyapunov']:+.4f}|COUPLING:{data['manifold_coupling_term']:.4f}")
            return
        except Exception:
            pass
            
    print("⚪ [OFFLINE ENGINE READ]")

if __name__ == "__main__":
    main()
