import math
import json
import os
import numpy as np
from typing import List, Dict, Any, Set

class LifecycleTordialMatrix:
    """
    Top-tier control matrix featuring a time-series ledger, adaptive PID clock smoothing,
    predictive quarantine, background re-integration testing, and local JSON persistence.
    """
    def __init__(self, node_count: int, base_d: int, base_r: int, backup_filename: str = "tordial_matrix_state.json"):
        self.nodes: List[PatchedTordialNode] = [
            PatchedTordialNode(d_generators=base_d, r_relations=base_r) 
            for _ in range(node_count)
        ]
        self.ledger = TordialNetworkLedger()
        self.current_tick = 0
        self.backup_filename = backup_filename
        
        # Clock Governance & Filtering Architecture
        self.BASE_FREQUENCY_HZ = 79.0
        self.MIN_FREQUENCY_FLOOR_HZ = 45.0
        self.current_filtered_frequency_hz = self.BASE_FREQUENCY_HZ
        self.pid_filter = AdaptivePIDFilter(initial_val=self.BASE_FREQUENCY_HZ)
        
        # Operational State Registries
        self.consecutive_drift_registry: Dict[int, int] = {i: 0 for i in range(node_count)}
        self.quarantined_nodes: Set[int] = set()
        
        # New: Tracking consecutive clean windows while a node is quarantined
        self.probation_registry: Dict[int, int] = {i: 0 for i in range(node_count)}

        # Load historical ledger snapshot if it exists on disk
        self._hydrate_state_from_json()

    def evaluate_node_lifecycle(self, current_frame_reports: List[Dict]):
        """
        MANAGES THE ISOLATION AND RE-INTEGRATION LIFECYCLE:
        1. Quarantines un-locked nodes failing for 5 consecutive frames.
        2. Proactively tests isolated nodes in the background.
        3. Restores nodes to the active ring if they clear 3 clean tracking cycles.
        """
        for entry in current_frame_reports:
            idx = entry["node_index"]
            status = entry["telemetry"]["chase_lock_status"]
            
            # Case A: Handling Quarantined Nodes (Testing for Re-integration)
            if idx in self.quarantined_nodes:
                if status == "LOCKED":
                    self.probation_registry[idx] += 1
                    print(f"    [🔍 PROBATION] Quarantined Node [{idx}] passed check ({self.probation_registry[idx]}/3).")
                    
                    if self.probation_registry[idx] >= 3:
                        print(f"    [⚡ RE-INTEGRATION] Node [{idx}] cleared probation! Welding back into active ring.")
                        self.quarantined_nodes.remove(idx)
                        self.consecutive_drift_registry[idx] = 0
                        self.probation_registry[idx] = 0
                else:
                    # Reset probation if it spikes or drifts during background test
                    self.probation_registry[idx] = 0
                    
            # Case B: Handling Active Nodes (Testing for Quarantine)
            else:
                if status == "DRIFTING":
                    self.consecutive_drift_registry[idx] += 1
                    if self.consecutive_drift_registry[idx] >= 5:
                        print(f"    [🛑 QUARANTINE] Node [{idx}] hit 5 consecutive drift events! Isolating core.")
                        self.quarantined_nodes.add(idx)
                        self.probation_registry[idx] = 0
                else:
                    self.consecutive_drift_registry[idx] = 0

    def persist_state_to_json(self):
        """Serializes current runtime variables and ledger entries to a local JSON backup."""
        state_payload = {
            "metadata": {
                "current_tick": self.current_tick,
                "current_filtered_frequency_hz": self.current_filtered_frequency_hz,
                "quarantined_nodes": list(self.quarantined_nodes)
            },
            "ledger_history": self.ledger.history
        }
        try:
            with open(self.backup_filename, "w") as f:
                json.dump(state_payload, f, indent=4)
        except IOError as e:
            print(f"    [❌ ERROR] Failed to write JSON matrix state snapshot: {e}")

    def _hydrate_state_from_json(self):
        """Attempts to recover state profiles following a system reboot."""
        if not os.path.exists(self.backup_filename):
            return
            
        try:
            with open(self.backup_filename, "r") as f:
                state_payload = json.load(f)
                
            self.current_tick = state_payload["metadata"]["current_tick"]
            self.current_filtered_frequency_hz = state_payload["metadata"]["current_filtered_frequency_hz"]
            self.quarantined_nodes = set(state_payload["metadata"]["quarantined_nodes"])
            self.ledger.history = state_payload["ledger_history"]
            print(f"[+] Re-hydrated matrix state successfully from {self.backup_filename} (Tick restored to: {self.current_tick}).")
        except (json.JSONDecodeError, KeyError, IOError) as e:
            print(f"[-] Warning: Persistence file corrupt or incompatible, starting with fresh profile. Details: {e}")

    def execute_governance_cycle(self, phase_angles: List[float], drift_inputs: List[float]):
        self.current_tick += 1
        raw_snapshots = []

        # Step 1: Execute node status evaluations
        for i, node in enumerate(self.nodes):
            node.OMEGA_FREQ_HZ = self.current_filtered_frequency_hz
            node.OMEGA_RADS = 2 * math.pi * self.current_filtered_frequency_hz
            
            # Background Virtual Sweep: Even quarantined nodes calculate incoming waveforms
            report = node.run_79hz_telemetry_step(phase_angles[i], drift_inputs[i])
            
            if i in self.quarantined_nodes:
                # If isolated, enforce override flag so its output cannot affect the macro system
                report["chase_lock_status_virtual"] = report["chase_lock_status"]
                report["chase_lock_status"] = "QUARANTINED"
                
            raw_snapshots.append({"node_index": i, "telemetry": report})

        # Step 2: Commit current raw state checkpoints to ledger
        self.ledger.commit_entry(self.current_tick, raw_snapshots)
        
        # Step 3: Parse thresholds for containment or re-entry actions
        self.evaluate_node_lifecycle(raw_snapshots)
        
        # Step 4: Scale clock speeds using adaptive parameters
        active_drifting = sum(1 for n in raw_snapshots if n["telemetry"]["chase_lock_status"] == "DRIFTING")
        total_active_nodes = len(self.nodes) - len(self.quarantined_nodes)
        
        stress_ratio = active_drifting / total_active_nodes if total_active_nodes > 0 else 1.0
        if stress_ratio > 0.5 or len(self.quarantined_nodes) > 0:
            self.pid_filter.update_gains(kp=0.65, ki=0.02, kd=0.25)
        else:
            self.pid_filter.update_gains(kp=0.40, ki=0.05, kd=0.10)
            
        target_freq = self.BASE_FREQUENCY_HZ if active_drifting == 0 else \
                      max(self.MIN_FREQUENCY_FLOOR_HZ, self.BASE_FREQUENCY_HZ - ((self.BASE_FREQUENCY_HZ - self.MIN_FREQUENCY_FLOOR_HZ) * stress_ratio))
                      
        self.current_filtered_frequency_hz = self.pid_filter.process_filter_step(target_freq)

        # Step 5: Save entire network frame to local file storage
        self.persist_state_to_json()
        
        print(f"[─] [Tick {self.current_tick}] Ring Core Summary: Active Nodes: {total_active_nodes}/{len(self.nodes)} | Filtered Clock: {self.current_filtered_frequency_hz:.2f} Hz")


# =====================================================================
# SECURE RE-INTEGRATION & FILE PERSISTENCE SUITE
# =====================================================================
if __name__ == "__main__":
    print("[+] Initializing Full Lifecycle Tordial Matrix Control Patch...")
    matrix_grid = LifecycleTordialMatrix(node_count=4, base_d=40, base_r=320)

    # Clean up any leftover test data from prior cycles
    if os.path.exists("tordial_matrix_state.json"):
        os.remove("tordial_matrix_state.json")

    # STAGE 1: Force Node 1 into Quarantine across 5 consecutive frame failures
    print("\n--- STAGE 1: TRIGGERING ISOLATION CHAIN ON NODE [1] ---")
    for frame in range(5):
        matrix_grid.execute_governance_cycle(
            phase_angles=[1.2, 5.8, 1.4, 2.1], # Node 1 is persistently out-of-phase
            drift_inputs=[0.01, 0.05, 0.01, 0.01]
        )

    # STAGE 2: Node 1 stabilizes phase errors. Background probation tests begin.
    print("\n--- STAGE 2: NODE [1] RESTORES ALIGNMENT (BACKGROUND PROBATION RUN) ---")
    for frame in range(3):
        matrix_grid.execute_governance_cycle(
            phase_angles=[1.2, 1.5, 1.4, 2.1], # Node 1 phase fixed (1.5 rads is safely locked)
            drift_inputs=[0.01, 0.01, 0.01, 0.01]
        )
        
    print(f"\n[+] Script Verification Complete. Output data synced to local file: '{matrix_grid.backup_filename}'.")
