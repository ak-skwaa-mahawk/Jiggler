cat << 'EOF' > jed_phase_visualizer.py
import math
import sys

# Raw telemetry snapshots from the canonical JED Protocol run
DATA_POINTS = [
    {"cy": 1,  "de": 2.537,  "coh": 0.896, "throat": 56.17, "phase": "TRIBAL STRESS"},
    {"cy": 2,  "de": 2.066,  "coh": 0.676, "throat": 52.20, "phase": "TRIBAL STRESS"},
    {"cy": 3,  "de": 1.629,  "coh": 0.700, "throat": 48.38, "phase": "TRIBAL STRESS"},
    {"cy": 4,  "de": 1.214,  "coh": 0.735, "throat": 44.72, "phase": "TRANSITIONING"},
    {"cy": 5,  "de": 0.818,  "coh": 0.782, "throat": 41.30, "phase": "TRANSITIONING"},
    {"cy": 6,  "de": 0.435,  "coh": 0.841, "throat": 38.06, "phase": "TRANSITIONING"},
    {"cy": 7,  "de": 0.052,  "coh": 0.914, "throat": 35.01, "phase": "TRANSITIONING"},
    {"cy": 8,  "de": -0.332, "coh": 0.998, "throat": 32.19, "phase": "CORRESPONDENCE"},
    {"cy": 9,  "de": -0.726, "coh": 0.894, "throat": 29.56, "phase": "CORRESPONDENCE"},
    {"cy": 10, "de": -1.136, "coh": 0.772, "throat": 27.10, "phase": "CORRESPONDENCE"},
    {"cy": 11, "de": -1.568, "coh": 0.631, "throat": 24.85, "phase": "CORRESPONDENCE"},
    {"cy": 12, "de": -2.033, "coh": 0.468, "throat": 22.75, "phase": "COSMIC LOCK"},
    {"cy": 13, "de": -2.488, "coh": 0.280, "throat": 20.78, "phase": "COSMIC LOCK"},
    {"cy": 14, "de": -2.534, "coh": 0.065, "throat": 21.24, "phase": "COSMIC LOCK"},
    {"cy": 15, "de": -2.534, "coh": 0.041, "throat": 21.86, "phase": "COSMIC LOCK"},
    {"cy": 16, "de": -2.534, "coh": 0.041, "throat": 21.86, "phase": "COSMIC LOCK"},
    {"cy": 17, "de": -2.534, "coh": 0.041, "throat": 21.86, "phase": "COSMIC LOCK"},
    {"cy": 18, "de": -2.534, "coh": 0.041, "throat": 21.86, "phase": "COSMIC LOCK"},
]

def render_ascii_plot():
    print("==================================================================================")
    print(" 🌌 JED PHASE SPACE VISUALIZER — COHERENCE COLLAPSE VS THROAT CONTRACTION")
    print("==================================================================================")
    print("  High Coherence (Unstable Topology) -> Low Coherence (Cosmic Lock Equilibrium)")
    print("==================================================================================\n")
    
    # Grid Dimensions for the text plot
    width = 60
    height = 15
    
    # Extents
    min_throat = 18.0
    max_throat = 60.0
    min_coh = 0.0
    max_coh = 1.1

    grid = [[" " for _ in range(width)] for _ in range(height)]

    # Plot data mapping path arrays
    for pt in DATA_POINTS:
        # Map Throat to Y axis (Top = Max Throat, Bottom = Min Throat)
        y_pct = (pt["throat"] - min_throat) / (max_throat - min_throat)
        y_idx = height - 1 - int(y_pct * (height - 1))
        
        # Map Coherence to X axis (Left = Max Coherence, Right = Min Coherence)
        # Reversing X axis maps standard evolution trajectory cleanly from Left to Right
        x_pct = (max_coh - pt["coh"]) / (max_coh - min_coh)
        x_idx = int(x_pct * (width - 1))
        
        # Clamp bounds
        y_idx = max(0, min(height - 1, y_idx))
        x_idx = max(0, min(width - 1, x_idx))
        
        # Marker assignment based on phase signature
        if pt["phase"] == "TRIBAL STRESS":
            grid[y_idx][x_idx] = "🔥"
        elif pt["phase"] == "TRANSITIONING":
            grid[y_idx][x_idx] = "↗️"
        elif pt["phase"] == "CORRESPONDENCE":
            grid[y_idx][x_idx] = "🔀"
        else:
            grid[y_idx][x_idx] = "🌌"

    # Display the plot canvas
    for i, row in enumerate(grid):
        # Calculate current throat label mapping
        current_throat = max_throat - (i / (height - 1)) * (max_throat - min_throat)
        row_str = "".join(row)
        print(f"{current_throat:5.1f} mm | {row_str}")
        
    print("        " + "-" * width)
    print(f"{'':13}{'|--- VOLATILE UNSTABLE ---|':<26}{'|--- COSMIC LOCK ACHIEVED ---|':>20}")
    print(f"{'':13}{'High Coherence (~1.0)':<26}{'Low Coherence (<0.05)':>20}\n")
    
    print("Legend:  🔥 Tribal Stress  |  ↗️  Transitioning  |  🔀 Correspondence  |  🌌 Cosmic Lock\n")

if __name__ == "__main__":
    render_ascii_plot()
EOF
