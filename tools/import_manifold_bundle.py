#!/usr/bin/env python3
import sys
import os
import tordial_gs_manifold

def run_import():
    in_path = os.path.expanduser("~/Tordial-GS-_Manifold/manifold_export.json")
    if not os.path.exists(in_path):
        print(f"❌ [IMPORT ERROR]: No source bundle found at {in_path}", file=sys.stderr)
        sys.exit(1)
        
    state = tordial_gs_manifold.TordialCoupledState()
    try:
        with open(in_path, "r") as f:
            bundle_content = f.read()
        
        success = state.import_bundle_string(bundle_content)
        if success:
            print("🟩 [PORTABILITY MATRIX]: Ingested bundle cleanly. State values mapped into active registers.")
            print(f"   Coordinates restored -> X: {state.global_phase_x:.4f} | Y: {state.global_phase_y:.4f}")
    except Exception as e:
        print(f"❌ [IMPORT ERROR]: {e}", file=sys.stderr)

if __name__ == "__main__":
    run_import()
