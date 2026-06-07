import math
import json
import os
import sys
import time
from typing import List, Dict, Set

class EnterpriseTordialMatrix(DualRingTordialMatrix):
    """
    Enterprise-grade dual-loop matrix controller equipped with automated 
    cross-ring parameter synchronization and manual override console triggers.
    """
    def __init__(self, node_count: int, base_d: int, base_r: int, **kwargs):
        super().__init__(node_count=node_count, base_d=base_d, base_r=base_r, **kwargs)
        self.manual_override_locked = False  # If True, automated failover logic is suspended

    def sync_active_structural_parameters(self):
        """
        AUTOMATED CROSS-RING SYNC MODULE:
        Synchronizes the micro-algebraic structural parameters (d, r) from the 
        currently active ring over to the idle backup ring to ensure operational parity.
        """
        source_ring = self.nodes if self.active_ring == "RING_A" else self.nodes_b
        target_ring = self.nodes_b if self.active_ring == "RING_A" else self.nodes
        
        for i in range(len(source_ring)):
            # Mirror generators and relations to ensure identical field tower boundaries
            target_ring[i].d = source_ring[i].d
            target_ring[i].r = source_ring[i].r

    def force_manual_failover(self, target_ring_designation: str):
        """
        CONSOLE MANUAL OVERRIDE SWITCH:
        Bypasses automated capacity checking routines and instantly commands 
        the routing engine to swap the active system trajectory path.
        """
        if target_ring_designation not in ["RING_A", "RING_B"]:
            print(f"    [❌ MANUAL OVERRIDE ERROR] Invalid target designation: {target_ring_designation}")
            return
            
        if self.active_ring == target_ring_designation:
            print(f"    [ℹ️ MANUAL OVERRIDE LOG] System already routed through {target_ring_designation}. No change.")
            return

        print(f"\n[⚡ OPERATOR COMMAND] Executing Manual Switch Override to: {target_ring_designation}...")
        self.active_ring = target_ring_designation
        self.manual_override_locked = True  # Lock out automated failover routines to respect manual choice
        print("    [-->] Automated failover state machine SUSPENDED. Manual tracking engaged.")

    def release_manual_override_lock(self):
        """Restores the autonomous telemetry failover guardrails."""
        self.manual_override_locked = False
        print("\n[⚡ OPERATOR COMMAND] Released Manual Override Lock. Autonomous guardrails restored.")

    def execute_governance_cycle(self, phases_a: List[float], drifts_a: List[float], 
                                 phases_b: List[float], drifts_b: List[float]):
        """Runs the complete dual-loop cycle with cross-ring sync and override hooks."""
        # Increments ticks and runs individual node telemetry via the dual-ring layer
        self.current_tick += 1
        snapshots_a, snapshots_b = [], []

        for i in range(len(self.nodes)):
            # Process Ring A
            self.nodes[i].OMEGA_FREQ_HZ = self.current_filtered_frequency_hz
            rep_a = self.nodes[i].run_79hz_telemetry_step(phases_a[i], drifts_a[i])
            if i in self.quarantined_nodes:
                rep_a["chase_lock_status_virtual"] = rep_a["chase_lock_status"]
                rep_a["chase_lock_status"] = "QUARANTINED"
            snapshots_a.append({"node_index": i, "telemetry": rep_a})

            # Process Ring B
            self.nodes_b[i].OMEGA_FREQ_HZ = self.current_filtered_frequency_hz
            rep_b = self.nodes_b[i].run_79hz_telemetry_step(phases_b[i], drifts_b[i])
            if i in self.quarantined_nodes_b:
                rep_b["chase_lock_status_virtual"] = rep_b["chase_lock_status"]
                rep_b["chase_lock_status"] = "QUARANTINED"
            snapshots_b.append({"node_index": i, "telemetry": rep_b})

        # Process lifecycle statuses
        self.evaluate_node_lifecycle(snapshots_a, snapshots_b)
        
        # Check Failover Conditions ONLY if the operator hasn't locked the system manually
        if not self.manual_override_locked:
            active_on_primary = len(self.nodes) - len(self.quarantined_nodes)
            if self.active_ring == "RING_A" and active_on_primary < 2:
                active_on_secondary = len(self.nodes_b) - len(self.quarantined_nodes_b)
                if active_on_secondary >= 2:
                    print("\n[🚨 CRITICAL EMERGENCY] Autonomous Failover Triggered due to low capacity!")
                    self.active_ring = "RING_B"
                    
        # RUN THE CROSS-RING SYNC: Sync from the active track to the backup track
        self.sync_active_structural_parameters()

        # Scale clock speeds based on active ring telemetry profiles
        targeted_snapshots = snapshots_a if self.active_ring == "RING_A" else snapshots_b
        active_drifting = sum(1 for n in targeted_snapshots if n["telemetry"]["chase_lock_status"] == "DRIFTING")
        total_active_nodes = len(self.nodes) - len(self.quarantined_nodes) if self.active_ring == "RING_A" else len(self.nodes_b) - len(self.quarantined_nodes_b)
        
        stress_ratio = active_drifting / total_active_nodes if total_active_nodes > 0 else 1.0
        target_freq = self.BASE_FREQUENCY_HZ if active_drifting == 0 else \
                      max(self.MIN_FREQUENCY_FLOOR_HZ, self.BASE_FREQUENCY_HZ - ((self.BASE_FREQUENCY_HZ - self.MIN_FREQUENCY_FLOOR_HZ) * stress_ratio))
        self.current_filtered_frequency_hz = self.pid_filter.process_filter_step(target_freq)

        # Draw the updated system dashboard
        self.render_dual_ring_dashboard(snapshots_a, snapshots_b)


# =====================================================================
# SYSTEM OPERATOR VERIFICATION LIFECYCLE
# =====================================================================
if __name__ == "__main__":
    matrix = EnterpriseTordialMatrix(node_count=4, base_d=40, base_r=320)

    # FRAME 1: Run standard operational baseline
    print("\n--- FRAME 1: DUAL LOOP BALANCE RUN ---")
    matrix.execute_governance_cycle(
        phases_a=[1.2, 1.2, 0.9, 1.5], drifts_a=[0.01]*4,
        phases_b=[1.2, 1.2, 0.9, 1.5], drifts_b=[0.01]*4
    )
    time.sleep(1.5)

    # FRAME 2: Simulating structural changes via an active load-shed event on Node 0
    print("\n--- FRAME 2: INITIATING LOCAL LOAD-SHED EVENT ---")
    matrix.nodes[0].r = 250  # Simulating a relation reduction on active Ring A Node 0
    # Run the cycle to verify the sync engine copies this change to Ring B Node 0 automatically
    matrix.execute_governance_cycle(
        phases_a=[1.2, 1.2, 0.9, 1.5], drifts_a=[0.01]*4,
        phases_b=[1.2, 1.2, 0.9, 1.5], drifts_b=[0.01]*4
    )
    print(f"    [✔ SYNC VERIFICATION] Ring B Node 0 Relations mirrored to: {matrix.nodes_b[0].r} (Expected: 250)")
    time.sleep(2.0)

    # FRAME 3: Operator issues manual switch command from console terminal
    print("\n--- FRAME 3: EXECUTING MANUAL CONSOLE FAILOVER ---")
    matrix.force_manual_failover("RING_B")
    matrix.execute_governance_cycle(
        phases_a=[1.2, 1.2, 0.9, 1.5], drifts_a=[0.01]*4,
        phases_b=[1.2, 1.2, 0.9, 1.5], drifts_b=[0.01]*4
    )
    time.sleep(1.5)
