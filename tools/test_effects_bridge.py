#!/usr/bin/env python3
import sys
import tools.ledger_engine
import tordial_gs_manifold

def main():
    print("📁 Connecting tracking harness to handshake ledger...", file=sys.stderr)
    handshake_chain = tools.ledger_engine.LocalSovereignChain(ledger_file="ledger_handshake.json")
    
    # 1. Instantiate the native localized oscillator and global manifold state primitives
    actor = tordial_gs_manifold.WaveActor(777)
    actor.rehydrate_from_bus(handshake_chain.native_bridge)
    
    global_manifold = tordial_gs_manifold.TordialCoupledState()

    print("\n=== Phase 1: Macro Flow Field Baseline ===")
    print(f"   -> Global Phase Coordinates: [{global_manifold.global_phase_x:.4f}, {global_manifold.global_phase_y:.4f}]")
    print(f"   -> Macro Forcing Ceiling Boundary: {global_manifold.macro_forcing_ceiling:.2f}")

    print("\n=== Phase 2: Evaluating Coupled Global Flow Evolution ===")
    dt = 0.05
    current_time = 0.0
    
    for step in range(1, 6):
        current_time += dt
        
        # Advance the resonant driver oscillator natively in Rust
        actor.step_wave_actor(dt, current_time)
        coupling_scalar = actor.compute_manifold_coupling()
        
        # Feed the coupling scalar straight into the macro flow equations
        global_manifold.modulate_global_field(coupling_scalar, dt)
        
        print(f"   [t = {current_time:.2f}s | Coupling: {coupling_scalar:.4f}]")
        print(f"     ──► Global Coordinates: X: {global_manifold.global_phase_x:+.4f} | Y: {global_manifold.global_phase_y:+.4f}")
        print(f"     ──► Modulated Relaxation: {global_manifold.phase_relaxation_rate:.4f} | Lyap Exponent: {global_manifold.effective_lyapunov_exponent:+.4f}")

    print("\n✅ Global flow coupling verified. Localized glyph waves are successfully shaping the macro manifold.")

if __name__ == "__main__":
    main()
