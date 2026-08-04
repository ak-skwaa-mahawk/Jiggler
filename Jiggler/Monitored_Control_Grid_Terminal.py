import math
import json
import os
import sys
import time
from typing import List, Dict, Any, Set

class MonitoredTordialMatrix:
    """
    Top-tier control matrix featuring a time-series ledger, adaptive PID clock smoothing,
    predictive quarantine, background re-integration, JSON persistence, and real-time CLI monitoring.
    """
    def __init__(self, node_count: int, base_d: int, base_r: int, 
                 backup_filename: str = "tordial_matrix_state.json",
                 max_storage_bytes: int = 100 * 1024): # 100 KB default threshold for safety alerts
        self.nodes: List[PatchedTordialNode] = [
            PatchedTordialNode(d_generators=base_d, r_relations=base_r) 
            for _ in range(node_count)
        ]
        self.ledger = TordialNetworkLedger()
        self.current_tick = 0
        self.backup_filename = backup_filename
        self.MAX_STORAGE_BYTES = max_storage_bytes
        self.storage_alarm_active = False
        
        # Clock Governance & Filtering Architecture
        self.BASE_FREQUENCY_HZ = 79.0
        self.MIN_FREQUENCY_FLOOR_HZ = 45.0
        self.current_filtered_frequency_hz = self.BASE_FREQUENCY_HZ
        self.pid_filter = AdaptivePIDFilter(initial_val=self.BASE_FREQUENCY_HZ)
        
        # Operational State Registries
        self.consecutive_drift_registry: Dict[int, int] = {i: 0 for i in range(node_count)}
        self.quarantined_nodes: Set[int] = set()
        self.probation_registry: Dict[int, int] = {i: 0 for i in range(node_count)}

        # Load historical ledger snapshot if it exists on disk
        self._hydrate_state_from_json()

    def evaluate_node_lifecycle(self, current_frame_reports: List[Dict]):
        """Manages quarantine boundaries and virtual background checks."""
        for entry in current_frame_reports:
            idx = entry["node_index"]
            status = entry["telemetry"]["chase_lock_status"]
            
            if idx in self.quarantined_nodes:
                if status == "LOCKED":
                    self.probation_registry[idx] += 1
                    if self.probation_registry[idx] >= 3:
                        self.quarantined_nodes.remove(idx)
                        self.consecutive_drift_registry[idx] = 0
                        self.probation_registry[idx] = 0
                else:
                    self.probation_registry[idx] = 0
            else:
                if status == "DRIFTING":
                    self.consecutive_drift_registry[idx] += 1
                    if self.consecutive_drift_registry[idx] >= 5:
                        self.quarantined_nodes.add(idx)
                        self.probation_registry[idx] = 0
                else:
                    self.consecutive_drift_registry[idx] = 0

    def check_storage_guardrails(self):
        """
        FILESIZE STORAGE MONITOR:
        Inspects the JSON ledger backup size. Triggers an alarm flag
        if the log payload breaches the allocated disk limits.
        """
        if not os.path.exists(self.backup_filename):
            return
            
        current_size = os.path.getsize(self.backup_filename)
        if current_size > self.MAX_STORAGE_BYTES:
            self.storage_alarm_active = True
        else:
            self.storage_alarm_active = False

    def persist_state_to_json(self):
        """Serializes current runtime variables and ledger entries to disk."""
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
            self.check_storage_guardrails()
        except IOError:
            pass

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
        except Exception:
            pass

    def render_cli_dashboard(self, current_snapshots: List[Dict]):
        """
        REAL-TIME COMMAND-LINE INTERFACE DASHBOARD:
        Clears the terminal workspace and paints a structured summary of core system health.
        """
        # Clear screen command for standard terminal windows
        os.system('cls' if os.name == 'nt' else 'clear')
        
        total_active_nodes = len(self.nodes) - len(self.quarantined_nodes)
        
        print("==========================================================================")
        print("                     TORDIAL GRID CONTROL ENGINE DASHBOARD                ")
        print("==========================================================================")
        print(f" Runtime Cycle: Tick #{self.current_tick:<6} | Network Structure: Ring Loop")
        print(f" Clock Cadence: {self.current_filtered_frequency_hz:.2f} Hz | Active Cores: {total_active_nodes}/{len(self.nodes)}")
        print(f" Current PID Tuning Parameters: Kp={self.pid_filter.kp:.2f}, Ki={self.pid_filter.ki:.2f}, Kd={self.pid_filter.kd:.2f}")
        print("--------------------------------------------------------------------------")
        
        # Print Storage Guard status bar
        if os.path.exists(self.backup_filename):
            file_kb = os.path.getsize(self.backup_filename) / 1024
            max_kb = self.MAX_STORAGE_BYTES / 1024
            alarm_str = "⚠️ [CRITICAL OVERFLOW RISK]" if self.storage_alarm_active else "🟢 [HEALTHY PROFILE]"
            print(f" Ledger Backup: {self.backup_filename} ({file_kb:.2f} KB / {max_kb:.2f} KB) -> {alarm_str}")
        print("--------------------------------------------------------------------------")
        print(f" {'NODE ID':<9} | {'OPERATIONAL STATUS':<20} | {'RAW PHASE (RADS)':<18} | {'DRIFT RESIDUE':<13}")
        print("--------------------------------------------------------------------------")
        
        for entry in current_snapshots:
            idx = entry["node_index"]
            tel = entry["telemetry"]
            status = tel["chase_lock_status"]
            
            # Map tracking phases correctly out of internal dictionaries
            phase_val = tel["raw_phase_rads"] if status != "QUARANTINED" else tel["chase_lock_status_virtual"]
            drift_val = tel["buffered_residue_drift"]
            
            # Stylize status strings
            status_display = status
            if status == "LOCKED":
                status_display = "🟢 LOCKED"
            elif status == "DRIFTING":
                status_display = "🟡 DRIFTING"
            elif status == "QUARANTINED":
                status_display = f"🔴 QUARANTINED ({self.probation_registry[idx]}/3)"
                phase_val = tel.get("chase_lock_status_virtual", 0.0)
                
            print(f" Node #{idx:<4} | {status_display:<20} | {phase_val:<18.4f} | {drift_val:<13.5f}")
        print("==========================================================================\n")
        sys.stdout.flush()

    def execute_governance_cycle(self, phase_angles: List[float], drift_inputs: List[float]):
        self.current_tick += 1
        raw_snapshots = []

        # Step 1: Process current telemetry ticks
        for i, node in enumerate(self.nodes):
            node.OMEGA_FREQ_HZ = self.current_filtered_frequency_hz
            node.OMEGA_RADS = 2 * math.pi * self.current_filtered_frequency_hz
            
            report = node.run_79hz_telemetry_step(phase_angles[i], drift_inputs[i])
            if i in self.quarantined_nodes:
                report["chase_lock_status_virtual"] = report["chase_lock_status"]
                report["chase_lock_status"] = "QUARANTINED"
                
            raw_snapshots.append({"node_index": i, "telemetry": report})

        # Step 2: Track structural limits and process life changes
        self.evaluate_node_lifecycle(raw_snapshots)
        
        # Step 3: Run filter speed controllers
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

        # Step 4: Save updates to ledger and disk
        self.ledger.commit_entry(self.current_tick, raw_snapshots)
        self.persist_state_to_json()
        
        # Step 5: Render current dashboard state to terminal interface
        self.render_cli_dashboard(raw_snapshots)


# =====================================================================
# REAL-TIME VISUALIZATION SIMULATION RUNTIME
# =====================================================================
if __name__ == "__main__":
# Configure matrix with a low 2 KB threshold to intentionally trip the storage alarm for testingmatrix_grid = MonitoredTordialMatrix(node_count=4, base_d=40, base_r=320, max_storage_bytes=2048)if os.path.exists("tordial_matrix_state.json"):os.remove("tordial_matrix_state.json")# Frame Sequence 1: System operates under standard, balanced tracking conditionsmatrix_grid.execute_governance_cycle([1.1, 1.3, 0.9, 2.0], [0.01, 0.01, 0.01, 0.01])time.sleep(1.5) # Pause to let you view the dashboard snapshot# Frame Sequence 2: Environmental turbulence causes Node 1 to enter a drifting statematrix_grid.execute_governance_cycle([1.1, 5.6, 0.9, 2.0], [0.01, 0.04, 0.01, 0.01])time.sleep(1.5)# Frame Sequence 3: Node 1 continues to drift, increasing the ledger file size on diskmatrix_grid.execute_governance_cycle([1.1, 5.9, 0.9, 2.0], [0.01, 0.05, 0.01, 0.01])time.sleep(1.5)
---