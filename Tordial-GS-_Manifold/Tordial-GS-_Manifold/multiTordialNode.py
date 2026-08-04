import math
from typing import List, Dict

# Assumes the TordialNode class from the previous control patch is available
class PatchedTordialNode(TordialNode):
    """Extension of TordialNode to support dynamic runtime adjustments."""
    def adjust_relations(self, delta: int):
        self.r = max(1, self.r + delta)

class TordialNodeMatrix:
    """
    Manages an array of TordialNode instances arranged in a ring network.
    Coordinates load balancing and executes real-time error correction for drifting nodes.
    """
    def __init__(self, node_count: int, base_d: int, base_r: int):
        self.nodes: List[PatchedTordialNode] = [
            PatchedTordialNode(d_generators=base_d, r_relations=base_r) 
            for _ in range(node_count)
        ]
        print(f"[+] Initialized Tordial Matrix with {node_count} nodes in a ring topology.")

    def execute_matrix_sweep(self, phase_angles: List[float], global_drift_inputs: List[float]) -> List[Dict]:
        """
        Executes a simultaneous telemetry sweep across all nodes.
        Automatically intercepts 'DRIFTING' telemetry to fire the recovery protocol.
        """
        matrix_telemetry = []
        
        for i, node in enumerate(self.nodes):
            # Run the 79 Hz telemetry cycle for the node
            node_report = node.run_79hz_telemetry_step(phase_angles[i], global_drift_inputs[i])
            
            # Catch anomalies immediately before they cause an overflow
            if node_report["chase_lock_status"] == "DRIFTING":
                print(f"[!] ALERT: Node [{i}] is drifting (Phase: {node_report['raw_phase_rads']:.4f} rads).")
                node_report = self._execute_error_correction_protocol(i, node_report)
                
            matrix_telemetry.append({"node_index": i, "telemetry": node_report})
            
        return matrix_telemetry

    def _execute_error_correction_protocol(self, target_idx: int, faulty_report: dict) -> dict:
        """
        ERROR-CORRECTION PROTOCOL (ECP):
        1. Calculates an inverse phase-shift injection to counter structural drift.
        2. Offloads 15% of the relation load to neighboring ring nodes.
        3. Recalculates parameters to verify real-time stabilization.
        """
        print(f"    [-->] Initializing ECP for Node [{target_idx}]...")
        drifting_node = self.nodes[target_idx]
        
        # Step 1: Inverse Phase Injection Calculation
        # Computes the angular distance required to snap the phase back under the Chase Threshold
        overshoot = faulty_report["raw_phase_rads"] - drifting_node.CHASE_RATIO_TAU
        inverse_injection = -1.0 * (overshoot + 0.05) # Adds a minor 0.05 radian safety clearing buffer
        
        # Step 2: Neighbor Network Load-Shedding
        # Find index locations within the ring topology
        left_neighbor_idx = (target_idx - 1) % len(self.nodes)
        right_neighbor_idx = (target_idx + 1) % len(self.nodes)
        
        offload_amount = max(1, int(drifting_node.r * 0.15))
        
        # Shed load from target, append to ring neighbors
        drifting_node.adjust_relations(-offload_amount)
        self.nodes[left_neighbor_idx].adjust_relations(offload_amount // 2)
        self.nodes[right_neighbor_idx].adjust_relations(offload_amount // 2)
        print(f"    [-->] Shed {offload_amount} structural relations to neighboring nodes [{left_neighbor_idx}] and [{right_neighbor_idx}].")
        
        # Step 3: Recalculate Telemetry with Adjusted Waveforms
        corrected_phase = faulty_report["raw_phase_rads"] + inverse_injection
        corrected_report = drifting_node.run_79hz_telemetry_step(corrected_phase, faulty_report["buffered_residue_drift"])
        
        # Log successful recovery metrics
        corrected_report["ecp_applied"] = True
        corrected_report["phase_correction_injected"] = inverse_injection
        print(f"    [+] ECP Complete. Node [{target_idx}] Recovery Status: {corrected_report['chase_lock_status']}.")
        
        return corrected_report

# =====================================================================
# SIMULATED LIVE NETWORK VERIFICATION
# =====================================================================
if __name__ == "__main__":
    # Build an active 3-node system loop
    network_matrix = TordialNodeMatrix(node_count=3, base_d=40, base_r=320)
    
    # Simulate data frames: Node 0 and 2 are aligned; Node 1 has high phase distortion (4.95 rads)
    simulated_phases = [1.20, 4.95, 2.50]
    simulated_drift  = [0.01, 0.03, 0.01]
    
    print("\n--- Starting Master Network Telemetry Loop Sweep ---")
    runtime_snapshots = network_matrix.execute_matrix_sweep(simulated_phases, simulated_drift)
    print("\n--- Sweep Completed Successfully ---")
