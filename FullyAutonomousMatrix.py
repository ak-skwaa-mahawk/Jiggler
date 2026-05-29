import math
import json
import os
import sys
import time
from typing import List, Dict, Any, Set

class ProductionTordialMatrix(FullyAutonomousMatrix):
    """
    Finalized production matrix controller containing dynamic ASCII connection breaks
    and an integrated CLI log search engine.
    """
    
    def render_ascii_topology_map(self):
        """
        UPGRADED TOPOLOGY MAP GENERATOR:
        Dynamically severs the link lines (\ or /) if a neighboring node is quarantined.
        """
        n0 = self.get_node_status_glyph(0)
        n1 = self.get_node_status_glyph(1)
        n2 = self.get_node_status_glyph(2)
        n3 = self.get_node_status_glyph(3)
        
        # Determine link line status based on neighbor health
        link_0_1 = " " if (0 in self.quarantined_nodes or 1 in self.quarantined_nodes) else "\\"
        link_0_3 = " " if (0 in self.quarantined_nodes or 3 in self.quarantined_nodes) else "/"
        link_2_1 = " " if (2 in self.quarantined_nodes or 1 in self.quarantined_nodes) else "/"
        link_2_3 = " " if (2 in self.quarantined_nodes or 3 in self.quarantined_nodes) else "\\"
        
        print("               [ Ring Network Topology Map ]")
        print(f"                     {n0} (Node 0)")
        print(f"                     {link_0_3}   {link_0_1}")
        print(f"                    {link_0_3}     {link_0_1}")
        print(f"          (Node 3) {n3}     {n1} (Node 1)")
        print(f"                    {link_2_3}     {link_2_1}")
        print(f"                     {link_2_3}   {link_2_1}")
        print(f"                     {n2} (Node 2)")
        print("==========================================================================")

    def query_ledger_history(self, target_status: str) -> List[Dict]:
        """
        INTEGRATED LEDGER SEARCH ENGINE:
        Scans remaining post-truncation ledger snapshots for specific status anomalies.
        """
        matches = []
        for entry in self.ledger.history:
            for state in entry["node_states"]:
                if state["lock"] == target_status:
                    matches.append({
                        "tick": entry["tick"],
                        "node_idx": state["idx"],
                        "phase_at_event": state["phase"]
                    })
        return matches


# =====================================================================
# FINAL SYSTEM CHECK OUT
# =====================================================================
if __name__ == "__main__":
    # Initialize a 4-node ring with low storage to force immediate truncation cycles
    matrix = ProductionTordialMatrix(node_count=4, base_d=40, base_r=320, max_storage_bytes=2560)

    if os.path.exists("tordial_matrix_state.json"):
        os.remove("tordial_matrix_state.json")

    print("[+] Initializing final hardware emulation loop...")
    
    # Cycle 1: Balanced Operation (Full Ring Intact)
    matrix.execute_governance_cycle([1.1, 1.2, 0.9, 1.5], [0.01, 0.01, 0.01, 0.01])
    time.sleep(1.5)

    # Cycles 2-6: Drive Node 1 into a hard quarantine to test ASCII ring breaking
    for _ in range(5):
        matrix.execute_governance_cycle([1.1, 5.9, 0.9, 1.5], [0.01, 0.05, 0.01, 0.01])
        time.sleep(0.4)
        
    # Run a query on the ledger history database for audit verification
    drift_logs = matrix.query_ledger_history("DRIFTING")
    print(f"\n[+] Audit Engine: Found {len(drift_logs)} instances of historical DRIFTING status in ledger memory.")
    if drift_logs:
        print(f"    -> First recorded event on Tick #{drift_logs[0]['tick']} for Node [{drift_logs[0]['node_idx']}]")
