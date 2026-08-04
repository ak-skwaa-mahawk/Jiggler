#!/usr/bin/env python3
import sys
import os
import tordial_gs_manifold

def run_export():
    out_path = os.path.expanduser("~/Tordial-GS-_Manifold/manifold_export.json")
    state = tordial_gs_manifold.TordialCoupledState()
    
    # Reconstruct the active runtime group signatures
    mock_ensemble = [
        tordial_gs_manifold.WaveActor(101),
        tordial_gs_manifold.WaveActor(102),
        tordial_gs_manifold.WaveActor(103)
    ]
    mock_ensemble[1].glyph_resonance_hz = 7.9583
    mock_ensemble[2].glyph_resonance_hz = 7.8583
    
    try:
        json_bundle = state.export_ensemble_bundle_string(4785, 7.9083, 0.5000, mock_ensemble)
        with open(out_path, "w") as f:
            f.write(json_bundle)
        print(f"📦 [PORTABILITY MATRIX]: Exported full ensemble bundle successfully to {out_path}")
    except Exception as e:
        print(f"❌ [EXPORT ERROR]: {e}", file=sys.stderr)

if __name__ == "__main__":
    run_export()
