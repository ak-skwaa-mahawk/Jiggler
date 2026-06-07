import math
import numpy as np
from typing import List, Dict, Any

class TordialNetworkLedger:
    """
    A time-series telemetry ledger tracking systemic drift variations 
    and operational constants across the entire ring network.
    """
    def __init__(self):
        self.history: List[Dict[str, Any]] = []

    def commit_entry(self, timestamp_tick: int, matrix_snapshot: List[Dict]):
        """Logs a single-cycle snapshot of all matrix node telemetry frames."""
        drifting_count = sum(
            1 for node in matrix_snapshot 
            if node["telemetry"]["chase_lock_status"] == "DRIFTING"
        )
        
        # Calculate systemic averages for tracking drift acceleration
        total_drift = sum(node["telemetry"]["buffered_residue_drift"] for node in matrix_snapshot)
        avg_drift = total_drift / len(matrix_snapshot) if matrix_snapshot else 0.0

        entry = {
            "tick": timestamp_tick,
            "active_nodes": len(matrix_snapshot),
            "drifting_nodes_count": drifting_count,
            "systemic_average_drift": avg_drift,
            "node_states": [
                {
                    "idx": n["node_index"],
                    "lock": n["telemetry"]["chase_lock_status"],
                    "phase": n["telemetry"]["raw_phase_rads"]
                } for n in matrix_snapshot
            ]
        }
        self.history.append(entry)

    def get_last_entry(self) -> Dict[str, Any]:
        """Returns the most recent system snapshot."""
        return self.history[-1] if self.history else {}


class ManagedTordialMatrix:
    """
    An advanced multi-node matrix integrated with a centralized 
    telemetry ledger and active clock speed modulation.
    """
    def __init__(self, node_count: int, base_d: int, base_r: int):
        self.nodes: List[PatchedTordialNode] = [
            PatchedTordialNode(d_generators=base_d, r_relations=base_r) 
            for _ in range(node_count)
        ]
        self.ledger = TordialNetworkLedger()
        self.current_tick = 0
        
        # Clock Governance Parameters
        self.BASE_FREQUENCY_HZ = 79.0
        self.MIN_FREQUENCY_FLOOR_HZ = 45.0  # Absolute safety floor to prevent loop collapse
        self.current_frequency_hz = self.BASE_FREQUENCY_HZ

    def calculate_dampened_frequency(self, drifting_count: int) -> float:
        """
        DYNAMIC CLOCK SPEED DAMPENER:
        Down-modulates frequency based on the number of concurrently drifting nodes.
        Safe restoration scales step-by-step as nodes re-lock.
        """
        total_nodes = len(self.nodes)
        if drifting_count == 0:
            # No stress: step the frequency back toward the nominal 79 Hz target
            return min(self.BASE_FREQUENCY_HZ, self.current_frequency_hz + 2.0)
        
        # Calculate stress factor as a direct ratio of compromised nodes
        stress_ratio = drifting_count / total_nodes
        frequency_drop = (self.BASE_FREQUENCY_HZ - self.MIN_FREQUENCY_FLOOR_HZ) * stress_ratio
        
        # Compute targeted dampened frequency
        target_freq = self.BASE_FREQUENCY_HZ - frequency_drop
        return max(self.MIN_FREQUENCY_FLOOR_HZ, target_freq)

    def execute_governance_cycle(self, phase_angles: List[float], drift_inputs: List[float]):
        """
        Executes a complete 79 Hz (or dampened) system governance sweep.
        Runs telemetry checkpoints, fires local ECPs, logs data, and dampens clock speed.
        """
        self.current_tick += 1
        raw_snapshots = []

        # Step 1: Individual Node Telemetry Checkpoints
        for i, node in enumerate(self.nodes):
            # Update node internal frequency value matching current matrix clock speed
            node.OMEGA_FREQ_HZ = self.current_frequency_hz
            node.OMEGA_RADS = 2 * math.pi * self.current_frequency_hz
            
            report = node.run_79hz_telemetry_step(phase_angles[i], drift_inputs[i])
            raw_snapshots.append({"node_index": i, "telemetry": report})

        # Step 2: Commit Status to Centralized Ledger
        self.ledger.commit_entry(self.current_tick, raw_snapshots)
        ledger_insights = self.ledger.get_last_entry()
        
        # Step 3: Evaluate Dynamic Clock Dampening Trigger
        compromised_nodes = ledger_insights["drifting_nodes_count"]
        old_freq = self.current_frequency_hz
        self.current_frequency_hz = self.calculate_dampened_frequency(compromised_nodes)

        print(f"\n[─] [Tick {self.current_tick}] Governance Sync Matrix Status:")
        print(f"    -> Active Core Frequency:  {self.current_frequency_hz:.2f} Hz (Was: {old_freq:.2f} Hz)")
        print(f"    -> Systemic Avg Drift:     {ledger_insights['systemic_average_drift']:.5f}")
        print(f"    -> Nodes in Breach/Drift:  {compromised_nodes} / {ledger_insights['active_nodes']}")

        # Step 4: Intercept and Execute Post-Ledger Error-Correction Protocols
        for snapshot in raw_snapshots:
            idx = snapshot["node_index"]
            if snapshot["telemetry"]["chase_lock_status"] == "DRIFTING":
                print(f"    [!] Initializing local ring isolation loop for Node [{idx}]")
                # Execute the ECP sequence developed in our previous update
                self._execute_matrix_level_ecp(idx, snapshot["telemetry"])

    def _execute_matrix_level_ecp(self, target_idx: int, report: dict):
        """Executes adjacent ring load balancing to alleviate localized node stress."""
        drifting_node = self.nodes[target_idx]
        left_neighbor = (target_idx - 1) % len(self.nodes)
        right_neighbor = (target_idx + 1) % len(self.nodes)
        
        offload = max(1, int(drifting_node.r * 0.15))
        drifting_node.adjust_relations(-offload)
        self.nodes[left_neighbor].adjust_relations(offload // 2)
        self.nodes[right_neighbor].adjust_relations(offload // 2)


# =====================================================================
# LIVE SIMULATION TEST FRAMEWORK
# =====================================================================
if __name__ == "__main__":
    print("[+] Initializing Advanced Tordial Matrix Control Grid...")
    # Initialize a 4-node ring system configuration
    matrix_grid = ManagedTordialMatrix(node_count=4, base_d=40, base_r=320)

    # FRAME 1: Stable system operational profile
    print("\n=== STAGE 1: BALANCED OPERATIONS ===")
    matrix_grid.execute_governance_cycle(
        phase_angles=[1.1, 2.3, 0.9, 1.8], 
        drift_inputs=[0.01, 0.01, 0.01, 0.01]
    )

    # FRAME 2: Environmental surge causes multiple nodes to drift simultaneously
    print("\n=== STAGE 2: SYSTEMIC SHOCK DETECTED (MULTI-NODE DRIFT) ===")
    matrix_grid.execute_governance_cycle(
        phase_angles=[1.1, 5.2, 4.9, 1.8], # Nodes 1 and 2 cross the 3.8833 threshold window
        drift_inputs=[0.01, 0.04, 0.05, 0.01]
    )

    # FRAME 3: Evaluating recovery behavior down-modulated speed
    print("\n=== STAGE 3: RUNTIME EVALUATION UNDER DAMPENED CLOCK SPEED ===")
    matrix_grid.execute_governance_cycle(
        phase_angles=[1.1, 2.1, 2.2, 1.8], # Nodes stabilized, phase overshoots resolved
        drift_inputs=[0.01, 0.01, 0.01, 0.01]
    )
