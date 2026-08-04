#!/usr/bin/env python3
import sys
import time
import os
import json
import tools.ledger_engine
import tordial_gs_manifold

def main():
    handshake_path = os.path.expanduser("~/Tordial-GS-_Manifold/ledger_handshake.json")
    proof_path = os.path.expanduser("~/Tordial-GS-_Manifold/ledger_proof.json")
    live_state_path = os.path.expanduser("~/Tordial-GS-_Manifold/.manifold_live.json")
    
    print("🌌 Starting Sovereign Manifold Continuous Bidirectional Simulation Daemon...", file=sys.stderr)
    print("🦅 [ENSEMBLE INITIALIZATION]: Deploying Energy Conservation Monitor Layer...", file=sys.stderr)

    handshake_chain = tools.ledger_engine.LocalSovereignChain(ledger_file=handshake_path)
    proof_chain = tools.ledger_engine.LocalSovereignChain(ledger_file=proof_path)

    ensemble = tordial_gs_manifold.DinjjiEnsemble()
    ensemble.sync_authorized_nodes(handshake_path)

    node_alpha = tordial_gs_manifold.WaveActor(101)
    node_beta = tordial_gs_manifold.WaveActor(102)
    node_gamma = tordial_gs_manifold.WaveActor(103)

    node_alpha.rehydrate_from_bus(handshake_chain.native_bridge)
    node_beta.rehydrate_from_bus(handshake_chain.native_bridge)
    node_gamma.rehydrate_from_bus(handshake_chain.native_bridge)

    node_beta.glyph_resonance_hz = 7.9083 + 0.05
    node_gamma.glyph_resonance_hz = 7.9083 - 0.05

    node_alpha.semantic_layer = "Dinjji Zhuu Kwaa"
    node_beta.semantic_layer = "Dinjji Zhuu Kwaa"

    ensemble.register_actor(node_alpha)
    ensemble.register_actor(node_beta)
    ensemble.register_actor(node_gamma)

    global_field = tordial_gs_manifold.TordialCoupledState()
    global_field.rehydrate_from_proof_bus(proof_chain.native_bridge)

    dt = 0.01
    simulated_time = 0.0
    step_index = 0

    try:
        while True:
            time.sleep(1.0)
            
            mutations = ensemble.sync_registry_and_detect_mutations(handshake_path)
            for mutation_string in mutations:
                proof_chain.native_bridge.append_wave_telemetry_block(int(time.time()), 99733, mutation_string)
            
            semantic_event_objects = ensemble.monitor_semantic_cluster_guard_rails(step_index)
            for ev in semantic_event_objects:
                payload_string = f"SEMANTIC_RESONANCE_EVENT|step={ev.step}|timestamp={ev.timestamp}|lane={ev.lane}|variance={ev.variance:.6f}|status={ev.status}|boost={ev.coupling_boost_applied:.2f}|locked_nodes={ev.locked_actor_ids}"
                proof_chain.native_bridge.append_wave_telemetry_block(int(time.time()), 99733, payload_string)
            
            # Fixed: Fire Native Stability Tracker and append structural blocks to ledger
            report = ensemble.execute_energy_conservation_audit(step_index)
            report_msg = f"RESONANCE_STABILITY_REPORT|step={report.step}|timestamp={report.timestamp}|total_energy={report.total_system_energy:.6f}|variance={report.rolling_energy_variance:.6f}|status={report.status_code}"
            proof_chain.native_bridge.append_wave_telemetry_block(int(time.time()), 99733, report_msg)
            print(f"🛡️ [STABILITY SUITE]: {report_msg}", file=sys.stderr)

            live_locks = ensemble.get_active_locks_list()

            for _ in range(5):
                step_index += 1
                simulated_time += dt
                
                mean_coupling_term, mean_coherence = ensemble.step_ensemble(
                    dt, simulated_time, global_field.global_phase_x, global_field.global_phase_y
                )
                
                primary_resonance_hz = 7.9083
                global_field.apply_parametric_coupling(mean_coupling_term, primary_resonance_hz)
                global_field.evolve_coupled_geometry(dt)
                
                telemetry_string = ensemble.export_actor_telemetry_string(0, step_index, simulated_time)
                proof_chain.native_bridge.append_wave_telemetry_block(int(time.time()), 99733, telemetry_string)
                
                snapshot_obj = global_field.to_snapshot(step_index, simulated_time, mean_coupling_term, primary_resonance_hz, mean_coherence, live_locks)
                json_payload = json.dumps({
                    "STEP": snapshot_obj.step,
                    "SIMULATED_TIME": snapshot_obj.simulated_time,
                    "GLOBAL_PHASE_X": snapshot_obj.global_phase_x,
                    "GLOBAL_PHASE_Y": snapshot_obj.global_phase_y,
                    "MACRO_FORCING_CEILING": snapshot_obj.macro_forcing_ceiling,
                    "PHASE_RELAXATION_RATE": snapshot_obj.phase_relaxation_rate,
                    "ATTRACTOR_STRENGTH": snapshot_obj.attractor_strength,
                    "EFFECTIVE_LYAPUNOV_EXPONENT": snapshot_obj.effective_lyapunov_exponent,
                    "MANIFOLD_COUPLING_TERM": snapshot_obj.manifold_coupling_term,
                    "RESONANCE_HZ": snapshot_obj.resonance_hz,
                    "COHERENCE_INDEX": snapshot_obj.coherence_index,
                    "ACTIVE_SEMANTIC_LOCKS": snapshot_obj.active_semantic_locks
                })
                proof_chain.native_bridge.append_macro_snapshot_block(int(time.time()), 99733, json_payload)

            proof_chain.native_bridge.flush_to_disk()
            prov_hash = ensemble.get_actor_provenance_hash(0)
            
            state_data = {
                "step": step_index,
                "simulated_time": simulated_time,
                "ensemble_count": ensemble.get_actor_count(),
                "mean_coherence_index": mean_coherence,
                "global_phase_x": global_field.global_phase_x,
                "global_phase_y": global_field.global_phase_y,
                "reference_provenance_source": prov_hash,
                "active_semantic_cluster_locks": live_locks
            }
            
            tmp_path = live_state_path + ".tmp"
            with open(tmp_path, "w") as f:
                json.dump(state_data, f, indent=2)
            os.replace(tmp_path, live_state_path)
            
            print(f"📥 [LIVE SYNC]: Step {step_index:03d} | Field Coherence: {mean_coherence:.4f}", file=sys.stderr)

    except KeyboardInterrupt:
        print("\n🛑 Halting background native ensemble simulation cleanly.", file=sys.stderr)
        sys.exit(0)

if __name__ == "__main__":
    main()
