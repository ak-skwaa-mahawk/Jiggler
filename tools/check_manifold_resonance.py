#!/usr/bin/env python3
import os
import sys
import json
import time

def clear_screen():
    print("\033[H\033[J", end="")

def generate_ascii_plot(x_val, y_val, actors_positions=None):
    # Establish a clean 40x15 coordinate viewport space
    width, height = 40, 15
    grid = [[" " for _ in range(width)] for _ in range(height)]
    
    # Render baseline orientation grid lines
    cx, cy = width // 2, height // 2
    for x in range(width):
        grid[cy][x] = "─"
    for y in range(height):
        grid[y][cx] = "│"
    grid[cy][cx] = "┼"
    
    # Map global macro phase coordinate marker
    mx = int(cx + (x_val * 10))
    my = int(cy - (y_val * 5))
    if 0 <= mx < width and 0 <= my < height:
        grid[my][mx] = "🪐"
        
    # Map local actor position dots if arrays pass through
    if actors_positions:
        for idx, pos in enumerate(actors_positions):
            ax = int(cx + (pos * 12))
            ay = cy
            if 0 <= ax < width and 0 <= ay < height:
                # Use string conversion to handle overlapping points clearly
                grid[ay][ax] = str(idx)

    return "\n".join("".join(row) for grid_row in grid for row in [grid_row])

def monitor_manifold_visuals():
    live_path = os.path.expanduser("~/Tordial-GS-_Manifold/.manifold_live.json")
    
    print("🛰️ Launching Sovereign Manifold Live ASCII Observability Pipeline...", file=sys.stderr)
    time.sleep(1.0)
    
    try:
        while True:
            if not os.path.exists(live_path):
                clear_screen()
                print("⚠️ [OBSERVER WARN]: Awaiting baseline snapshot emission from daemon loop...")
                time.sleep(1.0)
                continue
                
            try:
                with open(live_path, "r") as f:
                    state = json.load(f)
            except Exception:
                time.sleep(0.2)
                continue
                
            clear_screen()
            
            # Extract current execution states
            step = state.get("step", 0)
            sim_time = state.get("simulated_time", 0.0)
            coherence = state.get("mean_coherence_index", 0.0)
            mx = state.get("global_phase_x", 0.0)
            my = state.get("global_phase_y", 0.0)
            prov = state.get("reference_provenance_source", "UNKNOWN")
            locks = state.get("active_semantic_cluster_locks", [])
            
            # Form simulated placement trackers to represent localized kinematic spread
            mock_positions = [mx * 0.4, mx * 0.42] if locks else [mx * 0.1, my * -0.5]
            
            print("================================================================================")
            print(f"🦅 DINJJI ZHUU KWAA RES0NANCE OBSERVATION TRACKER  |  STEP: {step:04d} | TIME: {sim_time:.2f}s")
            print("================================================================================")
            print(f"🔒 CRYW-LINEAGE PROVENANCE: {prov}")
            print(f"🟩 GLOBAL PHASE ATTRACTOR : [X: {mx:+.4f}, Y: {my:+.4f}]")
            print(f"📥 MEAN SUBS-COHERENCE   : {coherence:.4f} (Balanced)")
            print(f"📡 ACTIVE SEMANTIC LOCKS  : {locks if locks else 'NONE (DRIFT PASS)'}")
            print("--------------------------------------------------------------------------------")
            
            # Print the geometric canvas field mapping layout
            print(generate_ascii_plot(mx, my, mock_positions))
            
            print("--------------------------------------------------------------------------------")
            if locks:
                print("⚡ STATUS: [RESONANCE LOCK ACHIEVED] -> Matching semantic lanes are boosting field weights.")
            else:
                print("🌲 STATUS: [DYNAMIC DRIFT ACTIVE] -> Monitoring structural boundary adjustments.")
            print("================================================================================")
            print("Press Ctrl+C to halt tracking visual pass.")
            
            time.sleep(1.0)
            
    except KeyboardInterrupt:
        print("\n🛑 Halting visual observability terminal mapping pass cleanly.")

if __name__ == "__main__":
    monitor_manifold_visuals()
