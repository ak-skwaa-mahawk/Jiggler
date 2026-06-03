class TordialAgentNode:
    """Base class — defined before any subclass."""
    def __init__(self, node_id: str, config: dict):
        self.node_id = node_id
        self.config = config
        self.curvature_pressure = 0.0
        self.energy = 100.0


class OpenTordialAgentNode(TordialAgentNode):
    """
    Open implementation of a Tordial Agent Node.
    Fission now triggers on high positive sigma_T (high stress/curvature load).
    """

    def __init__(self, node_id: str, config: dict):
        super().__init__(node_id, config)
        self.sigma_T = 1.0                    # Non-zero starting value
        self.curvature_pressure = 0.0

    def compute_and_update_gs(self, manifold_state: dict):
        pressure = manifold_state.get("curvature_pressure", 0.3)
        self.curvature_pressure = pressure

        # Always compute a meaningful, growing sigma_T
        self.sigma_T = pressure * 2.2

        # === FISSION TRIGGER (High Stress) ===
        # Triggers when the node is under significant curvature/load
        if self.sigma_T > 180:
            self._trigger_fission()

        # === GS Regime Logic (your existing code can go here) ===
        # Example placeholder:
        if pressure > 0.85:
            regime = "DEEP_GS"
        elif pressure > 0.6:
            regime = "GOLDILOCKS"
        elif pressure > 0.35:
            regime = "MARGINAL"
        else:
            regime = "SUBCRITICAL"

        return regime

    def _trigger_fission(self):
        print(f"[FISSION] Node {self.node_id} fissioning — sigma_T={self.sigma_T:.2f}")
        # Add your actual fission logic here (spawn children, split mass, etc.)