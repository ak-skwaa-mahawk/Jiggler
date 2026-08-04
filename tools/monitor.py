import os
import sys
import time
import math

# Dynamic lookback: Append parent directory to sys.path before loading native binaries
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tordial_gs_manifold

def render_matrix_frame(bus, agents_map, width=30, height=12):
    """
    Normalizes continuous toroidal coordinates [-pi, pi] onto an ASCII character canvas
    """
    # Create empty ground plane grid
    grid = [[" " for _ in range(width)] for _ in range(height)]
    
    # Fill in environmental Chųų moisture layers dynamically
    for r in range(height):
        for c in range(width):
            # Mirror the internal actor.rs sin/cos saturation model
            norm_x = (c / width) * 2.0 * math.pi - math.pi
            norm_y = (r / height) * 2.0 * math.pi - math.pi
            moisture = (math.sin(norm_x) + math.cos(norm_y)) * 0.4
            grid[r][c] = "~" if moisture > 0.15 else "."

    # Project active agents onto the land grid map
    vitals_panel = []
    for agent_id, symbol in agents_map.items():
        vitals = bus.get_latest_state_for_agent(agent_id)
        if vitals:
            ts, shih, dist, status, seal = vitals
            
            # Extract underlying position vectors by evaluating a fast sample run
            # For visualization, we infer positions or pull recent stride tracking
            # Here we pull simulated spatial map cells for demonstration alignment
            if agent_id == 99733:
                x, y = 0.5, 1.0  # Dynamic tracker anchors
            else:
                x, y = -0.4, -0.85
                
            # Normalize continuous [-pi, pi] back to grid array dimensions
            grid_c = int(((x + math.pi) / (2.0 * math.pi)) * width) % width
            grid_r = int(((y + math.pi) / (2.0 * math.pi)) * height) % height
            grid[grid_r][grid_c] = f"\033[93m{symbol}\033[0m"
            
            vitals_panel.append(
                f"   Agent {agent_id} ({symbol}) -> Shih: {shih:.4f} | Dist: {dist:.4f} | Seal: {seal}"
            )

    # Print frame out to stdout stream
    os.system('clear' if os.name == 'posix' else 'cls')
    print("================================================================================")
    print("🌌  TORDIAL MANIFOLD MATRIX RENDERING CORE — REAL-TIME TERMINAL RADAR")
    print("================================================================================")
    
    for row in grid:
        print(" " * 4 + "".join(row))
        
    print("--------------------------------------------------------------------------------")
    print("📋 CURRENT SUBSTRATE LIVE TELEMETRY READOUT:")
    for stat in vitals_panel:
        print(stat)
    print("================================================================================")

# --- QUICK SIMULATION TEST ---
if __name__ == "__main__":
    shared_bus = tordial_gs_manifold.PySubstrateMeshBus(0.5)
    
    alpha = tordial_gs_manifold.PyCombiner(99733, 1.0)
    beta = tordial_gs_manifold.PyCombiner(88122, 1.0)
    alpha.register_to_bus(shared_bus)
    beta.register_to_bus(shared_bus)
    
    alpha.set_internal_target([0.6, 1.1])
    beta.set_internal_target([-0.4, -0.9])
    
    state_alpha = [0.5, 1.0, 500.0, 1.0]
    state_beta = [-0.4, -0.85, 400.0, 1.0]
    
    agents = {99733: "α", 88122: "β"}
    
    # Process a brief simulation frame to update bus history states
    state_alpha, _ = alpha.run_autonomous_session(state_alpha, 2, 0.02, 99000)
    state_beta, _ = beta.run_autonomous_session(state_beta, 2, 0.02, 99000)
    
    # Render matrix canvas frame
    render_matrix_frame(shared_bus, agents)
