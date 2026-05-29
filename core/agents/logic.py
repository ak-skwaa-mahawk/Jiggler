class TGSAgent:
    def __init__(self, agent_id, manifold_connection):
        self.id = agent_id
        self.manifold = manifold_connection
        self.is_active = True

    def sense_environment(self):
        # Read the current geometric and algebraic states
        metrics = self.manifold.get_telemetry()
        return {
            "curvature": metrics.get("kappa"),
            "drift": metrics.get("v_drift"),
            "gs_headroom": metrics.get("gs_margin")
        }

    def evaluate_policy(self, telemetry):
        # Prevent actions if the system is approaching a GS structural collapse
        if telemetry["gs_headroom"] < 0.05:
            return "TRIGGER_FAILOVER"
        
        # If macro drift is high, calculate a stabilizing counter-injection
        if telemetry["drift"] > 1.5:
            return "STABILIZE_MACRO"
            
        return "IDLE_COMPUTE"

    def execute_action(self, decision):
        if decision == "TRIGGER_FAILOVER":
            self.manifold.initiate_dual_ring_migration(self.id)
            self.is_active = False
        elif decision == "STABILIZE_MACRO":
            # Inject micro algebraic pressure to counteract macro drift
            correction_vector = [-0.5 * telemetry["drift"]] 
            self.manifold.inject_coupling_pressure(self.id, correction_vector)
