import math
import json
import os
import sys
import time
from typing import List, Dict, Set

class DualRingTordialMatrix(ProductionTordialMatrix):
    """
    Advanced multi-ring controller managing a Primary Ring A and an automatic 
    failover Secondary Ring B to prevent system collapse during multi-node failures.
    """
    def __init__(self, node_count: int, base_d: int, base_r: int, **kwargs):
        # Initialize Primary Ring A via the base class architecture
        super().__init__(node_count=node_count, base_d=base_d, base_r=base_r, **kwargs)
        
        # Instantiate Secondary Physical Ring B
        self.nodes_b: List[PatchedTordialNode] = [
            PatchedTordialNode(d_generators=base_d, r_relations=base_r) 
            for _ in range(node_count)
        ]
        
        # Ring Operational States
        self.active_ring = "RING_A"  # Active choices: "RING_A" or "RING_B"
        self.quarantined_nodes_b: Set[int] = set()
        self.consecutive_drift_registry_b: Dict[int, int] = {i: 0 for i in range(node_count)}
        self.probation_registry_b: Dict[int, int] = {i: 0 for i in range(node_count)}

    def evaluate_node_lifecycle(self, reports_a: List[Dict], reports_b: List[Dict]):
        """Evaluates lifecycle boundaries and quarantine rules independently for both rings."""
        # 1. Update Primary Ring A States (using base class logic logic via inheritance)
        super().evaluate_node_lifecycle(reports_a)
        
        # 2. Update Secondary Ring B States
        for entry in reports_b:
            idx = entry["node_index"]
            status = entry["telemetry"]["chase_lock_status"]
            
            if idx in self.quarantined_nodes_b:
                if status == "LOCKED":
                    self.probation_registry_b[idx] += 1
                    if self.probation_registry_b[idx] >= 3:
                        self.quarantined_nodes_b.remove(idx)
                        self.consecutive_drift_registry_b[idx] = 0
                else:
                    self.probation_registry_b[idx] = 0
            else:
                if status == "DRIFTING":
                    self.consecutive_drift_registry_b[idx] += 1
                    if self.consecutive_drift_registry_b[idx] >= 5:
                        print(f"    [🛑 QUARANTINE - RING B] Node [{idx}] isolated on backup line.")
                        self.quarantined_nodes_b.add(idx)
                else:
                    self.consecutive_drift_registry_b[idx] = 0

    def get_node_glyph_by_ring(self, ring_name: str, idx: int, current_snapshots: List[Dict]) -> str:
        """Returns visual health status markers for specific ring arrays."""
        q_set = self.quarantined_nodes if ring_name == "RING_A" else self.quarantined_nodes_b
        if idx in q_set:
            return "🔴"
        for entry in current_snapshots:
            if entry["node_index"] == idx:
                return "🟢" if entry["telemetry"]["chase_lock_status"] == "LOCKED" else "🟡"
        return "⚪"

    def render_ascii_topology_map(self):
        """Disables traditional map to use dual-ring visualization block instead."""
        pass

    def render_dual_ring_dashboard(self, snapshots_a: List[Dict], snapshots_b: List[Dict]):
        """Draws a side-by-side visualization pane mapping both physical loop paths."""
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Calculate active node capacities
        active_a = len(self.nodes) - len(self.quarantined_nodes)
        active_b = len(self.nodes_b) - len(self.quarantined_nodes_b)
        
        print("==========================================================================")
        print("                 TORDIAL DUAL-RING DYNAMIC ROUTING CONTROLLER             ")
        print("==========================================================================")
        print(f" Cycle Tick: #{self.current_tick:<5} | Target Frequency: {self.current_filtered_frequency_hz:.2f} Hz")
        print(f" ACTIVE PATH:  ▶▶▶ {self.active_ring} ◀◀◀ (Ring A Core: {active_a}/4 | Ring B Core: {active_b}/4)")
        print("--------------------------------------------------------------------------")
        
        # Get glyph positions for cross-ring mapping
        a0, a1, a2, a3 = [self.get_node_glyph_by_ring("RING_A", i, snapshots_a) for i in range(4)]
        b0, b1, b2, b3 = [self.get_node_glyph_by_ring("RING_B", i, snapshots_b) for i in range(4)]
        
        # Compute link lines based on active quarantine overrides
        la = " " if (0 in self.quarantined_nodes or 1 in self.quarantined_nodes) else "\\"
        lb = " " if (0 in self.quarantined_nodes_b or 1 in self.quarantined_nodes_b) else "\\"
        
        print("       [ PRIMARY PHYSICAL RING A ]           [ SECONDARY BACKUP RING B ] ")
        print(f"               {a0} (Node 0)                         {b0} (Node 0)      ")
        print(f"               /   {la}                              /   {lb}           ")
        print(f"     (Node 3) {a3}     {a1} (Node 1)        (Node 3) {b3}     {b1} (Node 1)")
        print("               \\   /                             \\   /           ")
        print(f"               {a2} (Node 2)                         {b2} (Node 2)      ")
        print("==========================================================================")
        sys.stdout.flush()

    def execute_governance_cycle(self, phases_a: List[float], drifts_a: List[float], 
                                 phases_b: List[float], drifts_b: List[float]):
        self.current_tick += 1
        snapshots_a, snapshots_b = [], []

        # Step 1: Sweep both physical loops simultaneously
        for i in range(len(self.nodes)):
            # Process Ring A Telemetry
            self.nodes[i].OMEGA_FREQ_HZ = self.current_filtered_frequency_hz
            rep_a = self.nodes[i].run_79hz_telemetry_step(phases_a[i], drifts_a[i])
            if i in self.quarantined_nodes:
                rep_a["chase_lock_status_virtual"] = rep_a["chase_lock_status"]
                rep_a["chase_lock_status"] = "QUARANTINED"
            snapshots_a.append({"node_index": i, "telemetry": rep_a})

            # Process Ring B Telemetry
            self.nodes_b[i].OMEGA_FREQ_HZ = self.current_filtered_frequency_hz
            rep_b = self.nodes_b[i].run_79hz_telemetry_step(phases_b[i], drifts_b[i])
            if i in self.quarantined_nodes_b:
                rep_b["chase_lock_status_virtual"] = rep_b["chase_lock_status"]
                rep_b["chase_lock_status"] = "QUARANTINED"
            snapshots_b.append({"node_index": i, "telemetry": rep_b})

        # Step 2: Track health matrix updates
        self.evaluate_node_lifecycle(snapshots_a, snapshots_b)
        
        # Step 3: Check Failover Criteria (< 50% capacity on the working ring triggers switch)
        active_on_primary = len(self.nodes) - len(self.quarantined_nodes)
        if self.active_ring == "RING_A" and active_on_primary < 2:
            active_on_secondary = len(self.nodes_b) - len(self.quarantined_nodes_b)
            if active_on_secondary >= 2:
                print("\n[🚨 CRITICAL EMERGENCY] Primary Ring A Capacity Blown! Initiating Failover...")
                self.active_ring = "RING_B"

        # Step 4: Scale clock adjustments based on the active tracking ring's performance
        targeted_snapshots = snapshots_a if self.active_ring == "RING_A" else snapshots_b
        active_drifting = sum(1 for n in targeted_snapshots if n["telemetry"]["chase_lock_status"] == "DRIFTING")
        total_active_nodes = len(self.nodes) - len(self.quarantined_nodes) if self.active_ring == "RING_A" else len(self.nodes_b) - len(self.quarantined_nodes_b)
        
        stress_ratio = active_drifting / total_active_nodes if total_active_nodes > 0 else 1.0
        target_freq = self.BASE_FREQUENCY_HZ if active_drifting == 0 else \
                      max(self.MIN_FREQUENCY_FLOOR_HZ, self.BASE_FREQUENCY_HZ - ((self.BASE_FREQUENCY_HZ - self.MIN_FREQUENCY_FLOOR_HZ) * stress_ratio))
        self.current_filtered_frequency_hz = self.pid_filter.process_filter_step(target_freq)

        # Step 5: Render dual dashboard status lines
        self.render_dual_ring_dashboard(snapshots_a, snapshots_b)


# =====================================================================
# DUAL-LOOP FAILOVER TESTING SUITE
# =====================================================================
if __name__ == "__main__":
    matrix = DualRingTordialMatrix(node_count=4, base_d=40, base_r=320)

    # FRAME 1: Standard operating state. Primary Ring A handles system routing.
    print("\n--- FRAME 1: STABLE DUAL RUN ---")
    matrix.execute_governance_cycle(
        phases_a=[1.2, 1.2, 0.9, 1.5], drifts_a=[0.01]*4,
        phases_b=[1.2, 1.2, 0.9, 1.5], drifts_b=[0.01]*4
    )
    time.sleep(1.5)

    # FRAMES 2-6: Induce massive errors to drop multiple nodes on Ring A into Quarantine
    print("\n--- FRAMES 2-6: INTERFERENCE ON RING A (FAILOVER INITIATION) ---")
    for _ in range(5):
        matrix.execute_governance_cycle(
            phases_a=[1.2, 5.9, 5.9, 1.5], drifts_a=[0.05]*4,  # Nodes 1 & 2 are broken on Ring A
            phases_b=[1.2, 1.2, 0.9, 1.5], drifts_b=[0.01]*4   # Ring B remains perfectly stable
        )
        time.sleep(0.4)
