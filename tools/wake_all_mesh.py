#!/usr/bin/env python3
import os
import sys
import json
import time
import tools.ledger_engine
import tordial_gs_manifold

def trigger_mesh_rehydration():
    proof_path = os.path.expanduser("~/Tordial-GS-_Manifold/ledger_proof.json")
    if not os.path.exists(proof_path):
        print(f"⚠️ [WAKE WARN]: Target ledger path not found at {proof_path}. Creating clean layout baseline.")
        
    try:
        # Fixed: Explicitly passing the proof ledger target path parameter
        ledger = tools.ledger_engine.LocalSovereignChain(ledger_file=proof_path)
        
        # Instantiate global coupled state plane to inspect rehydration
        field = tordial_gs_manifold.TordialCoupledState()
        recovered = field.rehydrate_from_proof_bus(ledger.native_bridge)
        
        if recovered:
            print(f"🟩 [MESH REHYDRATION]: Successfully recovered active macro field coordinates from ledger archive.")
            print(f"   -> Global Phase X: {field.global_phase_x:.6f}")
            print(f"   -> Global Phase Y: {field.global_phase_y:.6f}")
            print(f"   -> Effective Lyapunov Exponent: {field.effective_lyapunov_exponent:.6f}")
        else:
            print("🌲 [MESH REHYDRATION]: Connected to ledger container, but found no structural macro footprint blocks. Operating from structural base.")
            
    except Exception as e:
        print(f"❌ [CRITICAL REHYDRATION ERROR]: Failed to bind ledger sequence: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    trigger_mesh_rehydration()
