# ... (previous imports and classes remain)

class DualRingTordialMatrix:
    def __init__(self, node_count: int = 12):
        # ... existing init ...
        self.last_ring_states = {"A": {}, "B": {}}   # for diffing
        self.sync_interval = 6

    def synchronize_rings_diff(self):
        """Efficient ring synchronization - only changed nodes"""
        if self.current_tick - self.last_sync_tick < self.sync_interval:
            return

        self.last_sync_tick = self.current_tick
        changed = 0

        if self.active_ring == "RING_A":
            for i in self.quarantined_a:
                if i not in self.quarantined_b:
                    self.quarantined_b.add(i)
                    changed += 1
        else:
            for i in self.quarantined_b:
                if i not in self.quarantined_a:
                    self.quarantined_a.add(i)
                    changed += 1

        if changed > 0:
            print(f"[SYNC-DIFF] Synced {changed} changed nodes between rings")

    def execute_heavy_load_cycle(self, system_load: float = 1.0):
        self.current_tick += 1
        t_now = time.time() - self.t_start

        load_factor = min(4.5, system_load)

        snapshots_a = [{"node_index": i, "telemetry": self.nodes_a[i].run_step(t_now, load_factor * (1.3 if i in self.quarantined_a else 1.0))} 
                      for i in range(self.node_count)]
        snapshots_b = [{"node_index": i, "telemetry": self.nodes_b[i].run_step(t_now, load_factor * (1.3 if i in self.quarantined_b else 1.0))} 
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

        self.synchronize_rings_diff()   # ← New efficient sync

        targeted = snapshots_a if self.active_ring == "RING_A" else snapshots_b
        self.adaptive_load_shedding(targeted, system_load)

        # ... frequency governance logic (unchanged) ...