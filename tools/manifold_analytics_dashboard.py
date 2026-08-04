#!/usr/bin/env python3
import os
import sys
import json
import time

def clear_screen():
    print("\033[H\033[J", end="")

def parse_historical_ledger(proof_path):
    history = {"steps": [], "x": [], "y": [], "coherence": [], "mutations": [], "resonance_events": []}
    if not os.path.exists(proof_path):
        return history
        
    try:
        with open(proof_path, "r") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    block = json.loads(line)
                    payload = block.get("payload", {})
                    fallback = payload.get("fallback_raw_data", "")
                    
                    if "REGISTRY_MUTATION" in fallback:
                        history["mutations"].append(fallback)
                    elif "SEMANTIC_RESONANCE_EVENT" in fallback:
                        history["resonance_events"].append(fallback)
                    elif "STRUCTURED_MACRO_JSON" in fallback:
                        clean_json = fallback.replace("STRUCTURED_MACRO_JSON|", "")
                        data = json.loads(clean_json)
                        history["steps"].append(data.get("STEP", 0))
                        history["x"].append(data.get("GLOBAL_PHASE_X", 0.0))
                        history["y"].append(data.get("GLOBAL_PHASE_Y", 0.0))
                        history["coherence"].append(data.get("COHERENCE_INDEX", 0.0))
                except Exception:
                    continue
    except Exception:
        pass
    return history

def draw_historical_orbit(history, width=50, height=15):
    if not history["x"] or not history["y"]:
        return " [Insufficient historical trajectory coordinates to map phase plane]"
        
    grid = [[" " for _ in range(width)] for _ in range(height)]
    cx, cy = width // 2, height // 2
    
    # Render baseline orientation frames
    for x in range(width): grid[cy][x] = "·"
    for y in range(height): grid[y][cx] = "·"
    
    # Plot tracking steps to trace orbit geometry evolution
    max_points = min(len(history["x"]), 100)
    for i in range(-max_points, 0):
        mx = int(cx + (history["x"][i] * (width // 3.5)))
        my = int(cy - (history["y"][i] * (height // 2.5)))
        if 0 <= mx < width and 0 <= my < height:
            grid[my][mx] = "x"
            
    # Highlight current execution head coordinate positions
    mx_now = int(cx + (history["x"][-1] * (width // 3.5)))
    my_now = int(cy - (history["y"][-1] * (height // 2.5)))
    if 0 <= mx_now < width and 0 <= my_now < height:
        grid[my_now][mx_now] = "🪐"
        
    return "\n".join("".join(row) for row in grid)

def run_analytics_dashboard():
    live_path = os.path.expanduser("~/Tordial-GS-_Manifold/.manifold_live.json")
    proof_path = os.path.expanduser("~/Tordial-GS-_Manifold/ledger_proof.json")
    
    try:
        while True:
            if not os.path.exists(live_path):
                clear_screen()
                print("🌲 [ANALYTICS] Awaiting telemetry snapshot stream pipeline emission...")
                time.sleep(1.0)
                continue
                
            try:
                with open(live_path, "r") as f:
                    state = json.load(f)
            except Exception:
                time.sleep(0.2)
                continue
                
            history = parse_historical_ledger(proof_path)
            clear_screen()
            
            print("================================================================================")
            print(f"🦅 SOVEREIGN MANIFOLD HIGH-FIDELITY DIAGNOSTIC METRIC COCKPIT   |   BURST SPRINT")
            print("================================================================================")
            print(f"📦 STEP INDEX     : {state.get('step', 0):05d}  |  SIMULATION TIME: {state.get('simulated_time', 0.0):.4f}s")
            print(f"🧬 SYSTEM NODE CNT: {state.get('ensemble_count', 0)} active members running across execution space")
            print(f"🟩 PHASE POSITION : [X: {state.get('global_phase_x', 0.0):+.4f}, Y: {state.get('global_phase_y', 0.0):+.4f}]")
            print(f"📥 MEAN COHERENCE : {state.get('mean_coherence_index', 0.0):.4f}")
            print(f"📡 ACTIVE LOCKS   : {state.get('active_semantic_cluster_locks', [])}")
            print("--------------------------------------------------------------------------------")
            print("🎨 HISTORICAL PHASE ATTRACTOR TRAJECTORY SPIRAL MAP:")
            print(draw_historical_orbit(history))
            print("--------------------------------------------------------------------------------")
            print(f"⚡ INGRESS MUTATIONS LOGGED ON BUS : {len(history['mutations'])}")
            for mut in history["mutations"][-2:]:
                print(f"  -> {mut[:75]}...")
            print(f"📡 SEMANTIC LOCK TRANSITIONS LOGGED: {len(history['resonance_events'])}")
            for ev in history["resonance_events"][-2:]:
                print(f"  -> {ev[:75]}...")
            print("================================================================================")
            print("Dashboard auto-refresh pass active. Press Ctrl+C to disconnect tracking link.")
            
            time.sleep(1.5)
            
    except KeyboardInterrupt:
        print("\n🛑 Disconnecting advanced analytical visual monitor safely.")

if __name__ == "__main__":
    run_analytics_dashboard()
