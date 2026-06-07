MIN_ENERGY_FLOOR = 50.0
MAX_ENERGY_CAP   = 500.0

def update_global_energy(global_energy: float, avg_kappa: float, node_count: int) -> float:
    """
    Stronger per-node drain so the governor can actually suppress spawning.
    Breakeven now occurs around \~15 nodes instead of \~150.
    """
    energy_delta = 12.0 + 0.8 * avg_kappa - (node_count * 0.8)

    new_energy = global_energy + energy_delta
    new_energy = max(MIN_ENERGY_FLOOR, min(MAX_ENERGY_CAP, new_energy))

    # Surface when energy actually suppresses spawning
    if new_energy <= MIN_ENERGY_FLOOR and global_energy > MIN_ENERGY_FLOOR:
        print(f"[GOVERNOR] Energy floor hit — spawn suppressed "
              f"(energy={new_energy:.1f}, nodes={node_count})")

    return new_energy