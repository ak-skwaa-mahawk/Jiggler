import math
import json
import os
import sys
import time
import csv
from typing import List, Dict, Any, Set

class SimulationTordialMatrix(EnterpriseTordialMatrix):
    """
    Top-tier control matrix featuring a time-series ledger, adaptive PID clock smoothing,
    predictive quarantine, dual-ring redundancy, an inline network latency simulator,
    and an automated CSV telemetry data exporter.
    """
    def __init__(self, node_count: int, base_d: int, base_r: int, 
                 csv_filename: str = "tordial_telemetry_export.csv", **kwargs):
        super().__init__(node_count=node_count, base_d=base_d, base_r=base_r, **kwargs)
        self.csv_filename = csv_filename
        
        # Latency Jitter Storage: tracks per-node delay constants in milliseconds
        self.node_latency_ms: Dict[int, float] = {i: 0.0 for i in range(node_count)}

    def configure_node_latency(self, node_idx: int, delay_ms: float):
        """Sets an artificial network communication delay on a target node transceiver."""
        if node_idx in self.node_latency_ms:
            self.node_latency_ms[node_idx] = delay_ms

    def _apply_latency_to_phases(self, raw_phases: List[float]) -> List[float]:
        """
        NETWORK LATENCY SIMULATOR:
        Transforms raw input waveforms by delaying phases according to individual node millisecond latency.
        """
        delayed_phases = []
        for i, phase in enumerate(raw_phases):
            # Translate millisecond packet delay into a proportional radian phase shift
            # Shift value ties directly back to our active governance frequency loop
            latency_radians = (self.node_latency_ms[i] / 1000.0) * self.current_filtered_frequency_hz * (2 * math.pi)
            delayed_phases.append(phase + latency_radians)
        return delayed_phases

    def export_ledger_to_csv(self):
        """
        AUTOMATED TELEMETRY EXPORT TOOL:
        Flattens multi-ring ledger snapshots and serializes current runtime 
        variables into a standardized, tabular .csv spreadsheet format.
        """
        if not self.ledger.history:
            return
            
        try:
            # Flatten the nested ledger structure into clean data table columns
            headers = ["tick", "active_frequency_hz", "drifting_nodes_count", "systemic_average_drift"]
            # Generate sub-headers dynamically for all nodes in the network grid
            for i in range(len(self.nodes)):
                headers.extend([f"node_{i}_lock_status", f"node_{i}_phase_rads"])
                
            with open(self.csv_filename, mode="w", newline="") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(headers)
                
                # Parse through memory logs and append lines sequentially
                for tick_entry in self.ledger.history:
                    # Capture historical metadata from that frame
                    row = [
                        tick_entry["tick"],
                        tick_entry.get("active_frequency_hz", self.BASE_FREQUENCY_HZ), # Fallback if key missing
                        tick_entry["drifting_nodes_count"],
                        tick_entry["systemic_average_drift"]
                    ]
                    # Map unique positional metrics into the row columns
                    for state in tick_entry["node_states"]:
                        row.extend([state["lock"], state["phase"]])
                        
                    writer.writerow(row)
        except IOError as e:
            print(f"    [❌ EXPORT ERROR] Failed to generate CSV spreadsheet: {e}")

    def execute_governance_cycle(self, phases_a: List[float], drifts_a: List[float], 
                                 phases_b: List[float], drifts_b: List[float]):
        """Runs governance cycles, applying real-time latency simulation and exporting to CSV."""
        # Intercept inputs and pass them through our inline network delay pipeline
        simulated_phases_a = self._apply_latency_to_phases(phases_a)
        simulated_phases_b = self._apply_latency_to_phases(phases_b)
        
        # Execute individual node telemetry evaluations using base class logic
        super().execute_governance_cycle(simulated_phases_a, drifts_a, simulated_phases_b, drifts_b)
        
        # Re-inject current actual clock speed metric directly into the latest ledger entry
        if self.ledger.history:
            self.ledger.history[-1]["active_frequency_hz"] = self.current_filtered_frequency_hz
            
        # Trigger the automated spreadsheet export
        self.export_ledger_to_csv()


# =====================================================================
# INTEGRATED PERFORMANCE STRESS RUNTIME
# =====================================================================
if __name__ == "__main__":
    print("[+] Launching High-Stress Tordial Simulation Node...")
    # Initialize a clean system matrix workspace
    matrix = SimulationTordialMatrix(node_count=4, base_d=40, base_r=320)

    if os.path.exists("tordial_telemetry_export.csv"):
        os.remove("tordial_telemetry_export.csv")

    # TEST SCENARIO 1: Clean, zero-latency network baseline
    print("\n--- TEST PHASE 1: NO LATENCY BALANCE RUN ---")
    matrix.execute_governance_cycle(
        phases_a=[1.2, 1.2, 0.9, 1.5], drifts_a=[0.01]*4,
        phases_b=[1.2, 1.2, 0.9, 1.5], drifts_b=[0.01]*4
    )
    time.sleep(1.5)

    # TEST SCENARIO 2: Inject extreme 65ms lag spike on Node 1 to simulate network jitter
    print("\n--- TEST PHASE 2: INJECTING 65MS PACKET DELAY ON NODE 1 ---")
    matrix.configure_node_latency(node_idx=1, delay_ms=65.0)
    
    # Run consecutive ticks to verify the latency engine drives Node 1 out of phase lock
    for stress_tick in range(3):
        matrix.execute_governance_cycle(
            phases_a=[1.2, 1.2, 0.9, 1.5], drifts_a=[0.01]*4,
            phases_b=[1.2, 1.2, 0.9, 1.5], drifts_b=[0.01]*4
        )
        time.sleep(0.5)
        
    print(f"\n[+] Simulation complete. Spreadsheet report compiled successfully at: '{matrix.csv_filename}'.")
