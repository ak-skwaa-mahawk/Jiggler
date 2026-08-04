"""
tordial_simulation.py
Unified Reference Implementation for the Tordial-GS Substrate.
Features high-stress fission tracking, strict energy governing, and automatic stabilization loops.
"""

import time
import math
import random

# Global Governor Constants
MIN_ENERGY_FLOOR = 50.0
MAX_ENERGY_CAP   = 500.0

class TordialAgentNode:
    """Base class defining foundational state and metrics tracking structures."""
    def __init__(self, node_id: str, config: dict):
        self.node_id = node_id
        self.config = config
        self.curvature_pressure = 0.0
        self.energy = 100.0


class OpenTordialAgentNode(TordialAgentNode):
    """
    Open implementation of a Tordial Agent Node.
    Fission triggers on high positive sigma_T (high stress/curvature load).
    """
    def __init__(self, node_id: str, config: dict):
        super().__init__(node_id, config)
        self.sigma_T = 1.0                    # Non-zero starting value
        self.curvature_pressure = 0.0

    def compute_and_update_gs(self, manifold_state: dict):
        pressure = manifold_state.get("curvature_pressure", 0.3)
        self.curvature_pressure = pressure

        # Compute a meaningful, growing sigma_T based on manifold tension
        self.sigma_T = pressure * 220.0  # Scaled to predictably access fission ranges

        # === FISSION TRIGGER (High Stress) ===
        # Triggers when the node is under significant curvature/load
        if self.sigma_T > 180.0:
            self._trigger_fission()

        # === GS Regime Logic ===
        if pressure > 0.85:
            regime = "DEEP_GS"
        elif pressure > 0.6:
            regime = "GOLDILOCKS"
        elif pressure > 0.35:
            regime = "MARGINAL"
        else:
            regime = "SUBCRITICAL"

        return regime

    def _trigger_fission(self):
        print(f"   🧬 [FISSION EVENT] Node {self.node_id} fissioning — sigma_T={self.sigma_T:.2f}")


def update_global_energy(global_energy: float, avg_kappa: float, node_count: int) -> float:
    """
    Stronger per-node drain so the governor can actually suppress spawning.
    Breakeven occurs around ~15 nodes instead of ~150.
    """
    # Drain scales heavily with node population density
    energy_delta = 12.0 + 0.8 * avg_kappa - (node_count * 0.8)

    new_energy = global_energy + energy_delta
    new_energy = max(MIN_ENERGY_FLOOR, min(MAX_ENERGY_CAP, new_energy))

    # Surface when energy suppresses spawning
    if new_energy <= MIN_ENERGY_FLOOR and global_energy > MIN_ENERGY_FLOOR:
        print(f"⚠️  [GOVERNOR] Energy floor hit — spawn suppressed (nodes={node_count})")

    return new_energy


# --- Demonstration Execution Loop ---
if __name__ == "__main__":
    print("[+] Booting Reference Manifold...")
    
    # Initialize base cluster parameters
    global_energy = 150.0
    nodes = [OpenTordialAgentNode(f"node_{i}", {}) for i in range(5)]
    
    # Simulate a 15-tick operational run under load
    for tick in range(1, 16):
        print(f"\n--- Tick {tick} ---")
        
        # 1. Evaluate baseline cluster metrics
        node_count = len(nodes)
        simulated_pressure = 0.4 + (node_count * 0.04)  # Pressure scales with node density
        avg_kappa = 0.12 * node_count
        
        # 2. Update the Global Governor
        global_energy = update_global_energy(global_energy, avg_kappa, node_count)
        print(f"  [METRICS] Global Energy: {global_energy:.1f} | Active Nodes: {node_count} | Pressure: {simulated_pressure:.2f}")
        
        # 3. Step Node Internal Dynamics and evaluate regimes
        for node in nodes:
            regime = node.compute_and_update_gs({"curvature_pressure": simulated_pressure})
            
        # 4. Attempt Spawning/Injection along available energy budgets
        if global_energy > MIN_ENERGY_FLOOR:
            new_id = f"node_{random.randint(100, 999)}"
            nodes.append(OpenTordialAgentNode(new_id, {}))
            print(f"  [SPAWNER] Instantiated node {new_id} successfully.")
        else:
            print("  [SPAWNER] Injection BLOCKED by Energy Governor.")
            
        time.sleep(0.1)
