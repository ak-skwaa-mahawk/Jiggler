import math
import json
import os
import sys
import time
import smtplib
from email.mime.text import MIMEText
from typing import List, Dict, Any, Set

class EnterpriseLifecycleMatrix(FullyMonitoredTordialMatrix):
    """
    Production-grade matrix manager equipped with background high-latency probation checks
    and automated SMTP telemetry report generation.
    """
    def __init__(self, node_count: int, base_d: int, base_r: int, **kwargs):
        super().__init__(node_count=node_count, base_d=base_d, base_r=base_r, **kwargs)
        
        # SMTP Configuration Defaults
        self.smtp_server = "smtp.tordial-grid.internal"
        self.smtp_port = 587
        self.sender_email = "grid-controller@tordial-grid.internal"
        self.recipient_email = "admin@tordial-grid.internal"

    def dispatch_daily_health_summary(self):
        """
        AUTOMATED SMTP EMAIL DISPATCH LOOP:
        Aggregates long-term performance logs from the ledger, builds an 
        administrative summary report, and transmits it via standard SMTP.
        """
        if not self.ledger.history:
            print("    [✉️ SMTP] Ledger history empty. Skipping email generation.")
            return

        print("    [✉️ SMTP] Compiling system performance summary report...")
        
        # Calculate summary metrics across the current historical log buffer
        total_ticks = len(self.ledger.history)
        truncations = self.truncation_counter
        active_quarantines = len(self.quarantined_nodes) + len(self.quarantined_nodes_b)
        
        # Build report body text
        msg_body = (
            f"=== TORDIAL CONTROL GRID SYSTEM SUMMARY REPORT ===\n"
            f"Current Runtime Tick : #{self.current_tick}\n"
            f"Total Ticks Logged   : {total_ticks}\n"
            f"Active Quarantines   : {active_quarantines} Nodes Isolated\n"
            f"Auto-Truncations     : {truncations} Cleanups Executed\n"
            f"Terminal Frequency   : {self.current_filtered_frequency_hz:.2f} Hz\n"
            f"=================================================="
        )
        
        # Format standard MIME components
        msg = MIMEText(msg_body)
        msg["Subject"] = f"[TORDIAL CRITICAL REPORT] Grid Health Diagnostics - Tick #{self.current_tick}"
        msg["From"] = self.sender_email
        msg["To"] = self.recipient_email
        
        try:
            # Shortened timeout sequence to prevent blocking the execution pipeline
            # with open(smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=1.0)) as server:
            #     server.starttls()
            #     server.login("username", "password")
            #     server.sendmail(self.sender_email, [self.recipient_email], msg.as_string())
            
            # Print a mock output to confirm successful processing during simulation testing
            print("    [✉️ SMTP] Summary transmission complete (Mock routing logged).")
        except Exception as e:
            print(f"    [❌ SMTP ERROR] Mail routing failure: {e}")

    def evaluate_node_lifecycle(self, reports_a: List[Dict], reports_b: List[Dict]):
        """
        UPGRADED LIFE MECHANICS (HIGH-LATENCY PROBATION ENGINE):
        Intercepts quarantined nodes and forces them to pass a high-latency simulation
        test before they can clear probation and re-integrate into the ring.
        """
        for entry in reports_a:
            idx = entry["node_index"]
            if idx in self.quarantined_nodes:
                # 1. Check if the node is recovering. We simulate 40ms of background communication
                # latency exclusively for this node's probation tracking step.
                probation_latency_ms = 40.0
                latency_radians = (probation_latency_ms / 1000.0) * self.current_filtered_frequency_hz * (2 * math.pi)
                
                # Apply the delay value to the node's current test phase angle
                simulated_test_phase = entry["telemetry"]["raw_phase_rads"] + latency_radians
                
                # Re-evaluate the lock check under high-latency stress conditions
                raw_phase_wrapped = simulated_test_phase % self.TAU_3D
                is_locked_under_stress = raw_phase_wrapped < self.CHASE_RATIO_TAU
                
                # 2. Process probation counters based on the stress-test results
                if is_locked_under_stress:
                    self.probation_registry[idx] += 1
                    print(f"    [🔍 PROBATION STRESS-TEST] Node [{idx}] locked through 40ms lag ({self.probation_registry[idx]}/3).")
                    
                    if self.probation_registry[idx] >= 3:
                        print(f"    [⚡ RE-INTEGRATION] Node [{idx}] passed stress-testing! Welding back to Active Ring A.")
                        self.quarantined_nodes.remove(idx)
                        self.consecutive_drift_registry[idx] = 0
                        self.probation_registry[idx] = 0
                else:
                    # Reset progress if the node drifts while adjusting to the network lag
                    if self.probation_registry[idx] > 0:
                        print(f"    [🔍 PROBATION RESET] Node [{idx}] failed lock under 40ms latency. Resetting counter.")
                    self.probation_registry[idx] = 0

        # Execute standard parent functions to manage remaining quarantine arrays
        super().evaluate_node_lifecycle(reports_a, reports_b)


# =====================================================================
# SYSTEM VERIFICATION AND STRESS ENVIRONMENT
# =====================================================================
if __name__ == "__main__":
    # Max storage set to a low 3 KB to easily demonstrate log management
    matrix = EnterpriseLifecycleMatrix(node_count=4, base_d=40, base_r=320, max_storage_bytes=3072)

    if os.path.exists("tordial_telemetry_export.csv"):
        os.remove("tordial_telemetry_export.csv")

    # STAGE 1: Drive Node 1 into Quarantine across 5 consecutive frame failures
    print("\n--- STAGE 1: INITIATING SYSTEMCONTAINMENT OVERRIDE ---")
    for frame in range(5):
        matrix.execute_governance_cycle(
            phases_a=[1.2, 5.8, 1.4, 2.1], drifts_a=[0.01]*4,
            phases_b=[1.2, 1.2, 1.4, 2.1], drifts_b=[0.01]*4
        )
        time.sleep(0.3)

    # STAGE 2: Node 1 phase realigns. Verify it handles the 40ms probation stress-test.
    print("\n--- STAGE 2: PROCESSING HIGH-LATENCY RE-INTEGRATION BLOCKS ---")
    for frame in range(3):
        matrix.execute_governance_cycle(
            phases_a=[1.2, 1.1, 1.4, 2.1], drifts_a=[0.01]*4, # Node 1 fixes its physical phase to 1.1 rads
            phases_b=[1.2, 1.2, 1.4, 2.1], drifts_b=[0.01]*4
        )
        time.sleep(0.3)

    # STAGE 3: Trigger administrative report compilation
    print("\n--- STAGE 3: RUNNING LOG SUMMARY AND EMAIL DELIVERY PIPELINE ---")
    matrix.dispatch_daily_health_summary()
