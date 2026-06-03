class KernelContractLog:
    def __init__(self, max_entries=500):
        self.max_entries = max_entries
        self.entries = []

    def push(self, violations):
        for v in violations:
            self.entries.append({
                "tick": v.tick,
                "node_id": v.node_id,
                "ring": v.ring,
                "field": v.field,
                "value": v.value,
                "bound": v.bound
            })
        self.entries = self.entries[-self.max_entries:]