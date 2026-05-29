import math
import numpy as np
from typing import List, Dict, Any

class AdaptivePIDFilter:
    """
    PID filter with runtime-adjustable proportional, integral, 
    and derivative gains managed by the system scheduler.
    """
    def __init__(self, initial_val: float):
        self.kp = 0.4
        self.ki = 0.05
        self.kd = 0.1
        
        self.current_value = initial_val
        self.integral_error = 0.0
        self.prev_error = 0.0

    def update_gains(self, kp: float, ki: float, kd: float):
        """Allows the scheduler to inject new operational gains dynamically."""
        self.kp = kp
        self.ki = ki
        self.kd = kd

    def process_filter_step(self, target_value: float, dt: float = 1.0) -> float:
        error = target_value - self.current_value
        self.integral_error += error * dt
        derivative = (error - self.prev_error) / dt
        
        adjustment = (self.kp * error) + (self.ki * self.integral_error) + (self.kd * derivative)
        self.current_value += adjustment
        
        self.prev_error = error
        return self.current_value


class AutonomousTordialMatrix:
    """
    Top-tier control engine managing a self-healing node array via 
    automated isolation loops and real-time gain scheduling.
    """
    def __init__(self, node_count: int, base_d: int, base_r: int):
        self.nodes: List[PatchedTordialNode] = [
            PatchedTordialNode(d_generators=base_d, r_relations=base_r) 
            for _ in range(node_count)
        ]
        self.ledger = TordialNetworkLedger()
        self.current_tick = 0
        
        # Clock Governance & Filtering Architecture
        self.BASE_FREQUENCY_HZ = 79.0
        self.MIN_FREQUENCY_FLOOR_HZ = 45.0
        self.current_filtered_frequency_hz = self.BASE_FREQUENCY_HZ
        self.pid_filter = AdaptivePIDFilter(initial_val=self.BASE_FREQUENCY_HZ)
        
        # Operational State Registries
        self.consecutive_drift_registry: Dict[int, int] = {i: 0 for i in range(node_count)}
        self.quarantined_nodes: Set = set()  # Set of node indexes extracted from active loop

    def execute_adaptive_gain_scheduling(self, active_drifting_count: int):
        """
        ADAPTIVE GAIN SCHEDULER:
        Modulates PID tracking speed based on real-time matrix topology changes.
        """
        total_active_nodes = len(self.nodes) - len(self.quarantined_nodes)
        if total_active_nodes == 0:
            return

        stress_ratio = active_drifting_count / total_active_nodes

        if stress_ratio > 0.5 or len(self.quarantined_nodes) > 0:
            # Aggressive Mode: Crank up responsiveness to damp frequency swiftly
            self.pid_filter.update_gains(kp=0.65, ki=0.02, kd=0.25)
        else:
            # Nominal Mode: Balanced tracking performance
            self.pid_filter.update_gains(kp=0.40, ki=0.05, kd=0.10)

    def evaluate_node_health(self, matrix_snapshot: List[Dict]):
        """
        AUTOMATED NODE-QUARANTINE LOOP:
        Monitors drift thresholds. Completely disconnects a node if it logs 
        5 consecutive failures, preserving ring baseline calculations.
        """
        for entry in matrix_snapshot:
            idx = entry["node_index"]
            if idx in self.quarantined_nodes:
                continue
                
            status = entry["telemetry"]["chase_lock_status"]
            if status == "DRIFTING":
                self.consecutive_drift_registry[idx] += 1
                consecutive_count = self.consecutive_drift_registry[idx]
                
                if consecutive_count >= 5:
                    print(f"    [🛑 QUARANTINE CRITICAL] Node [{idx}] hit 5 consecutive drift events!")
                    self.quarantined_nodes.add(idx)
                    print(f"    [-->] Node [{idx}] completely uncoupled from the active ring network.")
                elif consecutive_count >= 2:
                    print(f"    [⚠️ WARNING] Node [{idx}] persistent drift count: {consecutive_count}/5")
            else:
                self.consecutive_drift_registry[idx] = 0

    def calculate_dampened_target(self, active_drifting_count: int) -> float:
        total_active_nodes = len(self.nodes) - len(self.quarantined_nodes)
        if total_active_nodes <= 0 or active_drifting_count == 0:
            return self.BASE_FREQUENCY_HZ
            
        stress_ratio = active_drifting_count / total_active_nodes
        frequency_drop = (self.BASE_FREQUENCY_HZ - self.MIN_FREQUENCY_FLOOR_HZ) * stress_ratio
        return max(self.MIN_FREQUENCY_FLOOR_HZ, self.BASE_FREQUENCY_HZ - frequency_drop)

    def execute_governance_cycle(self, phase_angles: List[float], drift_inputs: List[float]):
        self.current_tick += 1
        raw_snapshots = []

        # Step 1: Run telemetry across surviving (non-quarantined) nodes
        for i, node in enumerate(self.nodes):
            if i in self.quarantined_nodes:
                # Keep reporting structure intact but zero out active metrics
                dummy_report = {"chase_lock_status": "QUARANTINED", "buffered_residue_drift": 0.0, "raw_phase_rads": 0.0}
                raw_snapshots.append({"node_index": i, "telemetry": dummy_report})
                continue
                
            node.OMEGA_FREQ_HZ = self.current_filtered_frequency_hz
            node.OMEGA_RADS = 2 * math.pi * self.current_filtered_frequency_hz
            
            report = node.run_79hz_telemetry_step(phase_angles[i], drift_inputs[i])
            raw_snapshots.append({"node_index": i, "telemetry": report})

        # Step 2: Track health and handle potential node containment isolation
        self.evaluate_node_health(raw_snapshots)
        
        # Step 3: Recalculate operational matrix stress levels
        active_drifting_nodes = sum(
            1 for entry in raw_snapshots 
            if entry["telemetry"]["chase_lock_status"] == "DRIFTING"
        )
        
        # Step 4: Run gain scheduler and process clock filter update
        self.execute_adaptive_gain_scheduling(active_drifting_nodes)
        raw_target = self.calculate_dampened_target(active_drifting_nodes)
        
        old_freq = self.current_filtered_frequency_hz
        self.current_filtered_frequency_hz = self.pid_filter.process_filter_step(raw_target)

        # Step 5: Commit cycle logs to ledger
        self.ledger.commit_entry(self.current_tick, raw_snapshots)

        print(f"\n[─] [Tick {self.current_tick}] Autonomous System Diagnostics:")
        print(f"    -> Active Active Nodes:    {len(self.nodes) - len(self.quarantined_nodes)} / {len(self.nodes)}")
        print(f"    -> Active PID Gains:      Kp={self.pid_filter.kp}, Kd={self.pid_filter.kd}")
        print(f"    -> Filtered Core Clock:   {self.current_filtered_frequency_hz:.2f} Hz (Target: {raw_target:.2f} Hz)")


# =====================================================================
# STRESS & CONTAINMENT TEST SUITE
# =====================================================================
if __name__ == "__main__":
    print("[+] Initializing Autonomous Grid Control Patch...")
    matrix_grid = AutonomousTordialMatrix(node_count=4, base_d=40, base_r=320)

    # Simulating 6 continuous execution steps where Node 1 is broken and drifts constantly
    static_phases = [1.2, 5.8, 1.4, 2.1]  # Node 1 is locked in a high overshoot loop
    static_drifts = [0.01, 0.05, 0.01, 0.01]

    for tick in range(6):
        print(f"\n=== CLOCK EXECUTION FRAME {tick + 1} ===")
        matrix_grid.execute_governance_cycle(static_phases, static_drifts)
