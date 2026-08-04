import math
import numpy as np
from typing import List, Dict, Any

class TordialPIDFilter:
    """
    Proportional-Integral-Derivative (PID) filter engine 
    designed to smooth out frequency steps within the clock dampener.
    """
    def __init__(self, kp: float, ki: float, kd: float, initial_val: float):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        
        self.current_value = initial_val
        self.integral_error = 0.0
        self.prev_error = 0.0

    def process_filter_step(self, target_value: float, dt: float = 1.0) -> float:
        """Computes the smoothed frequency output toward the target value."""
        error = target_value - self.current_value
        self.integral_error += error * dt
        derivative = (error - self.prev_error) / dt
        
        # Calculate control signal adjustment
        adjustment = (self.kp * error) + (self.ki * self.integral_error) + (self.kd * derivative)
        self.current_value += adjustment
        
        self.prev_error = error
        return self.current_value


class SystemicTordialMatrix:
    """
    Top-tier control matrix featuring a time-series ledger, continuous 
    PID clock smoothing, and predictive consecutive-drift alerting.
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
        self.MIN_FREQUENCY_FLOOR_HZ = 45.0
        self.raw_target_frequency_hz = self.BASE_FREQUENCY_HZ
        self.current_filtered_frequency_hz = self.BASE_FREQUENCY_HZ
        
        # Initialize PID Filter (tuned for steady, non-oscillatory damping)
        self.pid_filter = TordialPIDFilter(kp=0.4, ki=0.05, kd=0.1, initial_val=self.BASE_FREQUENCY_HZ)
        
        # Track persistent node drift history across execution frames
        self.consecutive_drift_registry: Dict[int, int] = {i: 0 for i in range(node_count)}

    def evaluate_consecutive_drift(self, matrix_snapshot: List[Dict]):
        """
        LEDGER ANALYSIS ENGINE:
        Increments or resets consecutive drift counters per node. 
        Raises warning flags for chronic structural issues.
        """
        for entry in matrix_snapshot:
            idx = entry["node_index"]
            status = entry["telemetry"]["chase_lock_status"]
            
            if status == "DRIFTING":
                self.consecutive_drift_registry[idx] += 1
                if self.consecutive_drift_registry[idx] >= 2:
                    print(f"    [⚠️ WARNING] Node [{idx}] has logged persistent drift across "
                          f"{self.consecutive_drift_registry[idx]} consecutive cycles! Isolation recommended.")
            else:
                self.consecutive_drift_registry[idx] = 0

    def calculate_dampened_target(self, drifting_count: int) -> float:
        """Computes the un-smoothed raw target frequency boundary based on node stress."""
        total_nodes = len(self.nodes)
        if drifting_count == 0:
            return self.BASE_FREQUENCY_HZ
            
        stress_ratio = drifting_count / total_nodes
        frequency_drop = (self.BASE_FREQUENCY_HZ - self.MIN_FREQUENCY_FLOOR_HZ) * stress_ratio
        return max(self.MIN_FREQUENCY_FLOOR_HZ, self.BASE_FREQUENCY_HZ - frequency_drop)

    def execute_governance_cycle(self, phase_angles: List[float], drift_inputs: List[float]):
        """Executes a comprehensive system governance sweep across all nodes."""
        self.current_tick += 1
        raw_snapshots = []

        # Step 1: Telemetry Loop Checkpoints using current filtered clock frequency
        for i, node in enumerate(self.nodes):
            node.OMEGA_FREQ_HZ = self.current_filtered_frequency_hz
            node.OMEGA_RADS = 2 * math.pi * self.current_filtered_frequency_hz
            
            report = node.run_79hz_telemetry_step(phase_angles[i], drift_inputs[i])
            raw_snapshots.append({"node_index": i, "telemetry": report})

        # Step 2: Commit Status to Centralized Ledger
        self.ledger.commit_entry(self.current_tick, raw_snapshots)
        ledger_insights = self.ledger.get_last_entry()
        
        # Step 3: Run Predictive Analysis for Consecutive Failures
        self.evaluate_consecutive_drift(raw_snapshots)
        
        # Step 4: Calculate Target and Apply PID Smoothing Filter
        compromised_nodes = ledger_insights["drifting_nodes_count"]
        self.raw_target_frequency_hz = self.calculate_dampened_target(compromised_nodes)
        
        old_filtered_freq = self.current_filtered_frequency_hz
        self.current_filtered_frequency_hz = self.pid_filter.process_filter_step(self.raw_target_frequency_hz)

        print(f"\n[─] [Tick {self.current_tick}] Grid Governance Diagnostics:")
        print(f"    -> Raw Stress Target:     {self.raw_target_frequency_hz:.2f} Hz")
        print(f"    -> PID Filtered Clock:    {self.current_filtered_frequency_hz:.2f} Hz (Shifted from: {old_filtered_freq:.2f} Hz)")
        print(f"    -> Systemic Avg Drift:    {ledger_insights['systemic_average_drift']:.5f}")

        # Step 5: Execute Load Balancing protocols for anomalous nodes
        for snapshot in raw_snapshots:
            if snapshot["telemetry"]["chase_lock_status"] == "DRIFTING":
                self._execute_ring_load_shed(snapshot["node_index"])

    def _execute_ring_load_shed(self, target_idx: int):
        drifting_node = self.nodes[target_idx]
        left_neighbor = (target_idx - 1) % len(self.nodes)
        right_neighbor = (target_idx + 1) % len(self.nodes)
        
        offload = max(1, int(drifting_node.r * 0.15))
        drifting_node.adjust_relations(-offload)
        self.nodes[left_neighbor].adjust_relations(offload // 2)
        self.nodes[right_neighbor].adjust_relations(offload // 2)


# =====================================================================
# SYSTEMIC LOOP TESTING SUITE
# =====================================================================
if __name__ == "__main__":
    print("[+] Launching Systemic Control Grid Simulation...")
    matrix_grid = SystemicTordialMatrix(node_count=4, base_d=40, base_r=320)

    # LOOP TICK 1: Standard Balanced Run
    print("\n=== RUN CHECK 1 ===")
    matrix_grid.execute_governance_cycle([1.1, 2.3, 0.9, 1.8], [0.01, 0.01, 0.01, 0.01])

    # LOOP TICK 2: Initial Stress Event (Nodes 1 & 2 cross threshold)
    print("\n=== RUN CHECK 2: INITIAL WAVE SURGE ===")
    matrix_grid.execute_governance_cycle([1.1, 5.2, 4.9, 1.8], [0.01, 0.04, 0.05, 0.01])

    # LOOP TICK 3: Stress Persists (Verifying warning flags & PID curve smoothing)
    print("\n=== RUN CHECK 3: PERSISTENT WAVE SURGE ===")
    matrix_grid.execute_governance_cycle([1.1, 5.5, 5.1, 1.8], [0.01, 0.04, 0.05, 0.01])
