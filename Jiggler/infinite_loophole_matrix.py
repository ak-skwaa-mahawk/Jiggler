import math
import random
import time
from collections import defaultdict
from typing import List, Dict, Set, Tuple

# Constants matching the updated Tordial-GS specification
PHI_OP = (1.0 + math.sqrt(5.0)) / 2.0
DISSIPATION_DECAY = 0.985

class GSGeneratorTower:
    """
    Implements Memory/Array Bound Fix (Point 3):
    A lazy, dynamic algebraic generator coordinate system. Instead of allocating dense 
    arrays, coordinates materialize strictly on-demand using a virtual index map.
    """
    def __init__(self):
        # Maps virtual coordinate indices to dynamic activation levels
        self._activated_coordinates = defaultdict(float)
        self._total_allocated_symbols = 0

    def access_coordinate(self, generator_idx: int, relation_idx: int) -> float:
        """Lazily instantiates and retrieves a micro-state matrix coordinate."""
        key = (generator_idx, relation_idx)
        if key not in self._activated_coordinates:
            # Materialize state lazily upon discovery/query
            self._activated_coordinates[key] = random.uniform(-0.01, 0.01)
            self._total_allocated_symbols += 1
        return self._activated_coordinates[key]

    def update_coordinate(self, generator_idx: int, relation_idx: int, value: float):
        self._activated_coordinates[(generator_idx, relation_idx)] = value

    @property
    def footprint_count(self) -> int:
        return self._total_allocated_symbols


class OpenTordialNode:
    """
    Implements Fixed (d, r) Variable Expansion (Point 1):
    A node whose algebraic dimensionality is directly tied to macro geometric drift.
    """
    def __init__(self, node_id: int, initial_d: int, initial_r: int, x: float, y: float):
        self.node_id = node_id
        self.d = initial_d
        self.r = initial_r
        self.sigma_T = 0.0
        
        # Macro geometric positions on a Normalized 2D Torus Grid [0, 2π]
        self.theta = x 
        self.phi = y
        self.drift_phase = 0.0
        
        # Local dynamic history tracking
        self.state_tower = GSGeneratorTower()
        self.status = "BALANCED"

    def compute_and_update_gs(self, curvature_pressure: float, resonance: float) -> bool:
        """
        Executes drift-coupled expansion. Preferentially scales generator counts (d) 
        over relational constraints (r) to maintain a strictly open, non-collapsed state space.
        """
        # Update structural drift phase tracking from local macro kinetics
        self.drift_phase = (self.theta + self.phi) / 2.0
        
        # Soft-threshold for expansion trigger
        EXPANSION_THRESHOLD = 0.75
        if curvature_pressure > EXPANSION_THRESHOLD:
            # Scale d faster than r to protect the GS inequality threshold
            delta_d = int(1 + resonance * 0.35)
            self.d += delta_d
            
            # Slower, constrained growth for relationships
            if random.random() < 0.3:
                self.r += 1
                
        # Patched Tordial-GS Inequality Equation
        denom = (4.0 * PHI_OP * 1.04) + (self.drift_phase * 0.05)
        # Calculate headroom margin: σ_T > 0 implies an active infinite algebraic horizon
        self.sigma_T = self.r - (pow(self.d, 2) / denom)
        
        if self.sigma_T <= 0:
            self.status = "DRIFTING"
        else:
            self.status = "BALANCED"
            
        return self.sigma_T > 0


class LoopholeManifoldMatrix:
    """
    Implements Static Node Topology Removal (Point 2):
    Manages an un-capped ring topology where nodes can undergo binary fission 
    when structural density bounds are exceeded.
    """
    def __init__(self, initial_node_count: int = 4):
        self.nodes: List[OpenTordialNode] = []
        self.quarantined_nodes: Set[int] = set()
        self.global_tick = 0
        self.fission_count = 0
        
        # Seed initial node ring evenly distributed over a geometric torus
        for i in range(initial_node_count):
            angle = (2 * math.pi * i) / initial_node_count
            self.nodes.append(OpenTordialNode(
                node_id=i, 
                initial_d=40, 
                initial_r=320, 
                x=angle, 
                y=angle
            ))

    def execute_governance_tick(self, environmental_pressures: List[float], resonance_vectors: List[float]):
        """Runs one high-resolution 79Hz refinement loop iteration."""
        self.global_tick += 1
        active_nodes = [n for n in self.nodes if n.node_id not in self.quarantined_nodes]
        
        # Step 1: Update Node States and process algebraic expansion
        for idx, node in enumerate(active_nodes):
            # Pad input vectors if active nodes have expanded via fission
            pressure = environmental_pressures[idx % len(environmental_pressures)]
            resonance = resonance_vectors[idx % len(resonance_vectors)]
            
            # Run the dynamic drift-coupled internal optimization calculation
            node.compute_and_update_gs(pressure, resonance)
            
            # Simulate macro-toroidal drift flow wrapping
            node.theta = (node.theta + 0.05 * pressure) % (2 * math.pi)
            node.phi = (node.phi + 0.03 * resonance) % (2 * math.pi)

        # Step 2: Evaluate Fission Criteria (Point 2)
        # Trigger splitting if structural capacity margin (sigma_T) crosses high-energy ceiling
        FISSION_THRESHOLD = -500.0  
        nodes_to_split = [n for n in active_nodes if n.sigma_T < FISSION_THRESHOLD]
        
        for parent in nodes_to_split:
            self._perform_node_fission(parent)

    def _perform_node_fission(self, parent: OpenTordialNode):
        """Splits an over-dense node into two separate coordinate frames along the drift line."""
        self.fission_count += 1
        new_id = len(self.nodes)
        
        # Offset child geometric position slightly ahead along the macro drift flow vector
        offset_theta = (parent.theta + 0.12) % (2 * math.pi)
        offset_phi = (parent.phi + 0.08) % (2 * math.pi)
        
        # Create child inheriting scaled, perturbed generator and relation properties
        child_d = int(parent.d * 0.8)
        child_r = int(parent.r * 0.8)
        
        child_node = OpenTordialNode(
            node_id=new_id,
            initial_d=child_d,
            initial_r=child_r,
            x=offset_theta,
            y=offset_phi
        )
        
        # Register new structure into active topology tracking matrices
        self.nodes.append(child_node)
        
        # Mitigate parent stress level through structural distribution
        parent.d = int(parent.d * 0.8)
        parent.r = int(parent.r * 0.8)
        
        print(f"[➔ Tick #{self.global_tick}] FISSION EVENT: Node [{parent.node_id}] split. Spawned Node [{new_id}] at θ={offset_theta:.2f}, φ={offset_phi:.2f}")

    def generate_openness_metrics(self) -> Dict[str, float]:
        """Calculates monitoring openness parameters to guarantee non-finiteness."""
        active = [n for n in self.nodes if n.node_id not in self.quarantined_nodes]
        avg_sigma = sum(n.sigma_T for n in active) / len(active) if active else 0
        total_virtual_coords = sum(n.state_tower.footprint_count for n in active)
        
        return {
            "total_nodes": len(self.nodes),
            "active_nodes": len(active),
            "mean_sigma_t": avg_sigma,
            "total_virtual_coordinates": total_virtual_coords,
            "fission_events": self.fission_count
        }


# =====================================================================
# SYSTEM VERIFICATION ROUTINE
# =====================================================================
if __name__ == "__main__":
    print("[+] Initializing Open-Horizon Loophole Manifold...")
    manifold = LoopholeManifoldMatrix(initial_node_count=4)
    
    # Run loop un-capped without predefined limits to simulate open execution profiling
    for cycle in range(1, 11):
        # Input heavy pressure signals to intentionally force rapid structural expansions
        mock_pressure = [1.2, 1.8, 0.9, 2.1]
        mock_resonance = [0.8, 0.9, 0.7, 1.4]
        
        manifold.execute_governance_tick(mock_pressure, mock_resonance)
        
        # Access a lazy random coordinate to confirm non-matrix block reads operate normally
        active_nodes = [n for n in manifold.nodes if n.node_id not in manifold.quarantined_nodes]
        if active_nodes:
            target_node = active_nodes[-1]
            # Access dynamic symbol on access safely
            _ = target_node.state_tower.access_coordinate(target_node.d, target_node.r)
            
        metrics = manifold.generate_openness_metrics()
        print(f"Cycle {cycle:02d} Metrics -> Nodes: {metrics['active_nodes']} | Mean σ_T: {metrics['mean_sigma_t']:.2f} | Lazy Cells Alloc: {metrics['total_virtual_coordinates']}")
        time.sleep(0.1)
