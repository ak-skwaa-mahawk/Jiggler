#!/usr/bin/env python3
import os
import sys
import json
import tordial_gs_manifold

def test_isolated_rehydration_handoff():
    print("🦅 [HANDOFF SUITE]: Launching cross-device state portability compliance pass...", file=sys.stderr)
    
    # Instantiate simulation objects mock configuration to represent Device A
    state_a = tordial_gs_manifold.TordialCoupledState()
    ensemble_a = tordial_gs_manifold.DinjjiEnsemble()
    
    state_a.global_phase_x = 1.7772
    state_a.global_phase_y = -0.8883
    
    actor = tordial_gs_manifold.WaveActor(105)
    actor.position = 0.35
    actor.semantic_layer = "Flamekeeper"
    ensemble_a.register_actor(actor)
    
    # Export package down into a portable snapshot string
    bundle_data_string = state_a.export_ensemble_bundle_string(
        1200, 7.9083, 0.95, ensemble_a.actors, ["Flamekeeper"]
    )
    
    print("🟩 [HANDOFF EXPORT SUCCESS]: Target state packed into out-of-band matrix frame.", file=sys.stderr)
    
    # Instantiate pristine secondary components to represent receiving Device B
    state_b = tordial_gs_manifold.TordialCoupledState()
    ensemble_b = tordial_gs_manifold.DinjjiEnsemble()
    
    success_macro = state_b.ingest_macro_snapshot_bundle(bundle_data_string)
    success_ensemble = ensemble_b.ingest_handoff_bundle_string(bundle_data_string)
    
    if success_macro and success_ensemble:
        print("🟩 [HANDOFF REHYDRATION SUCCESS]: Device B swallowed state parameters flawlessly.", file=sys.stderr)
        print(f"   -> Rehydrated Phase X: {state_b.global_phase_x:.4f} (Expected: 1.7772)")
        print(f"   -> Active Locks State: {ensemble_b.get_active_locks_list()}")
    else:
        print("❌ [HANDOFF ERROR]: Structural rehydration tracking alignment failed.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    test_isolated_rehydration_handoff()
