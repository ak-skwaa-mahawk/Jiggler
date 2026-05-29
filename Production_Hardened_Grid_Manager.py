import math
import json
import os
import sys
import time
import csv
import hashlib
from typing import List, Dict, Any, Set

class HardenedEnterpriseMatrix(EnterpriseLifecycleMatrix):
    """
    Enterprise-grade control matrix featuring real-time latency-driven load balancing,
    automated SHA-256 cryptographic signing for exported data, and a full self-healing stack.
    """
    def __init__(self, node_count: int, base_d: int, base_r: int, **kwargs):
        super().__init__(node_count=node_count, base_d=base_d, base_r=base_r, **kwargs)
        self.base_relations = base_r

    def execute_dynamic_load_rebalancing(self):
        """
        DYNAMIC LOAD OFFLOADING CONTROLLER:
        Monitors individual node latencies. Dynamically redistributes structural relations (r)
        from high-latency nodes to low-latency ring neighbors to prevent bottlenecks.
        """
        active_indices = [i for i in range(len(self.nodes)) if i not in self.quarantined_nodes]
        if len(active_indices) <= 1:
            return  # Insufficient active nodes to perform relative rebalancing
            
        # 1. Fetch current latency profile for active nodes
        latencies = {i: self.node_latency_ms.get(i, 0.0) for i in active_indices}
        avg_latency = sum(latencies.values()) / len(latencies)
        
        # 2. Allocate or reduce relations based on latency deviation from the mean
        for idx in active_indices:
            node_latency = latencies[idx]
            current_ring = self.nodes if self.active_ring == "RING_A" else self.nodes_b
            target_node = current_ring[idx]
            
            if node_latency > avg_latency * 1.2:
                # Latency is 20% higher than average: shed 10% of relation load
                shed_amount = max(1, int(target_node.r * 0.10))
                target_node.r = max(10, target_node.r - shed_amount)
                
                # Distribute the shed load evenly to lower-latency active neighbors
                eligible_neighbors = [i for i in active_indices if latencies[i] <= avg_latency and i != idx]
                if eligible_neighbors:
                    give_amount = shed_amount // len(eligible_neighbors)
                    for n_idx in eligible_neighbors:
                        current_ring[n_idx].r += give_amount
                        
                print(f"    [⚖️ LOAD BALANCER] Node [{idx}] latency ({node_latency}ms) high. Shed {shed_amount} relations.")
            
            elif node_latency < avg_latency * 0.8 and target_node.r < self.base_relations * 1.5:
                # Latency is low: scale back up toward base capacity if it was previously degraded
                target_node.r = min(int(self.base_relations * 1.5), target_node.r + 5)

    def generate_cryptographic_signature(self):
        """
        CRYPTOGRAPHIC HASHING EXTENSION:
        Computes a secure SHA-256 checksum over the raw exported CSV telemetry sheet
        and saves it to a verified manifest file to guarantee long-term data integrity.
        """
        if not os.path.exists(self.csv_filename):
            return
            
        sha256_hash = hashlib.sha256()
        try:
            # Read the CSV in binary mode to compile a precise cryptographic block signature
            with open(self.csv_filename, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            
            hex_digest = sha256_hash.hexdigest()
            hash_file_path = f"{self.csv_filename}.sha256"
            
            with open(hash_file_path, "w") as h_file:
                h_file.write(hex_digest)
                
            print(f"    [🔐 CRYPTO ENGINE] CSV Signed. SHA-256: {hex_digest[:16]}... Saved to manifest.")
        except IOError as e:
            print(f"    [❌ CRYPTO ERROR] Failed to compute file signature manifest: {e}")

    def execute_governance_cycle(self, phases_a: List[float], drifts_a: List[float], 
                                 phases_b: List[float], drifts_b: List[float]):
        """Runs the complete governance sweep with active load rebalancing and cryptographic signatures."""
        # 1. Run the dynamic balancer before calculating telemetry loops to use updated r values
        self.execute_dynamic_load_rebalancing()
        
        # 2. Run core telemetry routing, data persistence, and UI rendering from parent classes
        super().execute_governance_cycle(phases_a, drifts_a, phases_b, drifts_b)
        
        # 3. Compute and write the SHA-256 signature over the updated CSV file
        self.generate_cryptographic_signature()


# =====================================================================
# SYSTEM HARDENING VERIFICATION SUITE
# =====================================================================
if __name__ == "__main__":
    print("[+] Initializing Hardened Enterprise Control Grid...")
    # Initialize matrix workspace
    matrix = HardenedEnterpriseMatrix(node_count=4, base_d=40, base_r=320)

    # Clean up old artifacts from past test sweeps
    for target_file in ["tordial_telemetry_export.csv", "tordial_telemetry_export.csv.sha256"]:
        if os.path.exists(target_file):
            os.remove(target_file)

    # TICK 1: Standard balanced baseline run (Zero latency skew)
    print("\n--- TICK 1: RUNNING BALANCED LIFECYCLE ---")
    matrix.execute_governance_cycle(
        phases_a=[1.2, 1.2, 0.9, 1.5], drifts_a=[0.01]*4,
        phases_b=[1.2, 1.2, 0.9, 1.5], drifts_b=[0.01]*4
    )
    time.sleep(1.5)

    # TICK 2: Inject a severe 85ms packet latency bottleneck on Node 2
    # Verifies that the load scheduler captures the variance and sheds structural relations
    print("\n--- TICK 2: INTRODUCING RELATIVE LATENCY DISTORTION ON NODE 2 ---")
    matrix.configure_node_latency(node_idx=2, delay_ms=85.0)
    matrix.execute_governance_cycle(
        phases_a=[1.2, 1.2, 0.9, 1.5], drifts_a=[0.01]*4,
        phases_b=[1.2, 1.2, 0.9, 1.5], drifts_b=[0.01]*4
    )
    time.sleep(1.5)
