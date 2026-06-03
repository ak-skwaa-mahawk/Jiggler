class OpenTordialAgentNode(TordialAgentNode):
    def __init__(self, node_id: str, config: dict):
        super().__init__(node_id, config)
        self.sigma_T = 1.0
        self.curvature_pressure = 0.0

    def compute_and_update_gs(self, manifold_state: dict):
        pressure = manifold_state.get("curvature_pressure", 0.3)
        self.curvature_pressure = pressure

        # Always compute a meaningful sigma_T
        self.sigma_T = pressure * 2.2          # grows with pressure

        # Fission on high stress (most likely intended behavior)
        if self.sigma_T > 180:
            self._trigger_fission()

        # ... rest of GS regime logic