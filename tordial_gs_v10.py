import math
import yaml
import argparse
import numpy as np
import time
from typing import Dict, List, Set
from datetime import datetime

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

t = config["tordial"]
t["base_frequency_hz"] = 79.79   # Your preferred frequency

class GSSweep:
    # ... (same as v9)
    pass

class TordialNode:
    def __init__(self, d: int, r: int, node_id: int):
        self.node_id = node_id
        self.OMEGA_RADS = 2 * math.pi * t["base_frequency_hz"]
        self.TAU_3D = 2 * t["pi_3d"]
        self.CHASE_RATIO_TAU = self.TAU_3D / t["phi_op"]
        self.d = d
        self.r = r
        self.load = 0.0
        self.state_version = 0

    def run_step(self, t_seconds: float, external_load: float = 1.0) -> Dict:
        phase = (self.OMEGA_RADS * t_seconds) % self.TAU_3D
        coupling = GSSweep().compute_gs(self.d, self.r)
        self.load = external_load
        self.state_version += 1
        return {
            "node_id": self.node_id,
            "raw_phase_rads": phase,
            "chase_lock_status": "LOCKED" if phase < self.CHASE_RATIO_TAU else "DRIFTING",
            "coupling_telemetry": coupling,
            "load": external_load,
            "state_version": self.state_version
        }


class DualRingTordialMatrix:
    def __init__(self, node_count: int = 12):
        self.node_count = node_count
        self.BASE_FREQUENCY_HZ = t["base_frequency_hz"]
        self.MIN_FREQUENCY_FLOOR_HZ = config["governance"]["min_frequency_floor_hz"]
        self.current_filtered_frequency_hz = self.BASE_FREQUENCY_HZ
        self.current_tick = 0
        self.t_start = time.time()
        self.active_ring = "RING_A"

        self._seed_nodes()

        self.quarantined_a: Set[int] = set()
        self.quarantined_b: Set[int] = set()
        self.consec_drift = {"A": {i: 0 for i in range(node_count)}, "B": {i: 0 for i in range(node_count)}}

        # Ring Synchronization
        self.last_sync_tick = 0
        self.sync_interval = 8   # ticks

    def _seed_nodes(self):
        # Same GS sweep seeding as before...
        df = GSSweep().run_sweep()
        preferred = pd.concat([
            df[df["band"] == "GOLDILOCKS"].sample(n=self.node_count//2, replace=True),
            df[df["band"].isin(["DEEP_GS", "MARGINAL"])].sample(n=self.node_count - self.node_count//2, replace=True)
        ])
        self.nodes_a = [TordialNode(int(row["d"]), int(row["r"]), i) for i, row in enumerate(preferred.iterrows())]
        self.nodes_b = [TordialNode(int(row["d"]), int(row["r"]), i) for i, row in enumerate(preferred.iterrows())]
        self.node_bands = list(preferred["band"])

    def synchronize_rings(self):
        """Minimal-latency state mirroring between Ring A and B"""
        if self.current_tick - self.last_sync_tick < self.sync_interval:
            return
        self.last_sync_tick = self.current_tick
        # Mirror active quarantines and frequency state
        if self.active_ring == "RING_A":
            self.quarantined_b.update(self.quarantined_a)
        else:
            self.quarantined_a.update(self.quarantined_b)
        print(f"[SYNC] Rings synchronized at tick {self.current_tick}")

    def adaptive_load_shedding(self, snapshots: List[Dict], system_load: float) -> List[int]:
        """Dynamic node deactivation based on load + GS strength"""
        shed_list = []
        for s in snapshots:
            idx = s["node_index"]
            load = s["telemetry"]["load"]
            kappa = s["telemetry"]["coupling_telemetry"].get("kappa_GS_T", 0)

            # High load + weak GS = candidate for shedding
            if load > 2.4 and kappa < 5.5 and len(shed_list) < self.node_count // 3:
                shed_list.append(idx)
                if self.active_ring == "RING_A":
                    self.quarantined_a.add(idx)
                else:
                    self.quarantined_b.add(idx)
                print(f"[SHED] Node {idx} deactivated (load={load:.2f}, κ={kappa:.2f})")
        return shed_list

    def execute_heavy_load_cycle(self, system_load: float = 1.0):
        self.current_tick += 1
        t_now = time.time() - self.t_start

        load_factor = min(4.0, system_load)

        # Run both rings
        snapshots_a = [{"node_index": i, "telemetry": self.nodes_a[i].run_step(t_now, load_factor)} 
                      for i in range(self.node_count)]
        snapshots_b = [{"node_index": i, "telemetry": self.nodes_b[i].run_step(t_now, load_factor)} 
                      for i in range(self.node_count)]

        # Apply quarantines
        for s in snapshots_a:
            if s["node_index"] in self.quarantined_a:
                s["telemetry"]["chase_lock_status"] = "QUARANTINED"
        for s in snapshots_b:
            if s["node_index"] in self.quarantined_b:
                s["telemetry"]["chase_lock_status"] = "QUARANTINED"

        self._evaluate_health(snapshots_a, self.quarantined_a, "A")
        self._evaluate_health(snapshots_b, self.quarantined_b, "B")

        self.synchronize_rings()

        # Adaptive Load Shedding
        targeted = snapshots_a if self.active_ring == "RING_A" else snapshots_b
        self.adaptive_load_shedding(targeted, system_load)

        # Failover logic + frequency governance (same as v9, with stronger backpressure)
        if self.active_ring == "RING_A" and (self.node_count - len(self.quarantined_a)) < self.node_count // 2:
            self.active_ring = "RING_B"
            print(f"[FAILOVER] Heavy load triggered switch to RING_B")

        # ... frequency calculation (same logic) ...

        self.current_filtered_frequency_hz = max(45.0, min(98.0, self.current_filtered_frequency_hz))