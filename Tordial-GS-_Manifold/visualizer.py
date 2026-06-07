def plot_kappa_over_time(session_data):
    """Plot κ (kappa) vs tick for each node."""
    import matplotlib.pyplot as plt

    if not session_data:
        print("[WARN] No session data to visualize.")
        return

    # Determine number of nodes
    max_nodes = max(len(s["snapshots"]) for s in session_data)

    # Build per-node time series
    kappa_series = {i: [] for i in range(max_nodes)}
    ticks = []

    for entry in session_data:
        ticks.append(entry["tick"])
        for snap in entry["snapshots"]:
            idx = snap["node_index"]
            kappa_series[idx].append(snap["telemetry"].get("kappa", 0.0))

    # Plot
    plt.figure(figsize=(12, 6))
    for idx, values in kappa_series.items():
        plt.plot(ticks, values, label=f"Node {idx}")

    plt.title("GS Field Evolution — κ vs Tick")
    plt.xlabel("Tick")
    plt.ylabel("κ (kappa_GS_T)")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.show()