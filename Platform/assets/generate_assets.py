#!/usr/bin/env python3
# Platform/assets/generate_assets.py
import os
import numpy as np

def generate_stability_plot():
    """Generates the system floor stability chart mapping energy containment thresholds."""
    # Only import rendering libraries if explicitly called by asset pipelines
    import matplotlib.pyplot as plt

    # Generate synthetic phase convergence data fading to a zero floor baseline
    time_steps = np.linspace(0, 10, 100)
    variational_energy = 4.5 * np.exp(-0.7 * time_steps) + np.random.normal(0, 0.05, 100)
    variational_energy = np.maximum(variational_energy, 0.0) # Clamp to absolute zero floor
    
    plt.figure(figsize=(8, 4))
    plt.plot(time_steps, variational_energy, color="#00ffcc", label="Variational Energy ($E$)")
    plt.axhline(y=5.0, color="red", linestyle="--", label="Containment Ceiling (5.0)")
    plt.axhline(y=0.0, color="white", linestyle="-", alpha=0.3)
    
    plt.title("Sovereign Platform: State Space Trajectory Floor Stability", color="white")
    plt.xlabel("Execution Epochs", color="white")
    plt.ylabel("Energy Curve Metric", color="white")
    
    # Custom styling for dark-mode dashboard aesthetics
    fig = plt.gcf()
    fig.patch.set_facecolor("#121212")
    ax = plt.gca()
    ax.set_facecolor("#1a1a1a")
    ax.tick_params(colors="white")
    ax.spines['bottom'].set_color('white')
    ax.spines['left'].set_color('white')
    
    plt.legend(facecolor="#222222", labelcolor="white")
    plt.grid(True, color="#333333", linestyle=":")
    
    os.makedirs("assets", exist_ok=True)
    plt.savefig("assets/floor_stability.png", facecolor=fig.get_facecolor(), bbox_inches='tight', dpi=150)
    plt.close()
    print("[+] System stabilization artifact saved to assets/floor_stability.png")

if __name__ == "__main__":
    generate_stability_plot()
