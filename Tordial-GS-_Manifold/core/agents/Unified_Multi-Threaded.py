class TGSController:
    """Parallel PID logic module with dynamic curvature throttling."""
    def __init__(self, Kp: float, Ki: float, Kd: float, alpha: float = 0.05):
        self.Kp, self.Ki, self.Kd, self.alpha = Kp, ki, kd, alpha
        self.integral_error = np.zeros(3)
        self.prev_error = np.zeros(3)

    def calculate_correction(self, v_drift: np.ndarray, kappa: float, dt: float) -> np.ndarray:
        error = 0.0 - v_drift
        self.integral_error += error * dt
        derivative_error = (error - self.prev_error) / dt if dt > 0 else np.zeros(3)
        u_raw = (self.Kp * error) + (self.Ki * self.integral_error) + (self.Kd * derivative_error)
        chi = 1.0 / (1.0 + self.alpha * kappa)
        self.prev_error = error
        return u_raw * chi


class TordialManifoldEnvironment:
    """Simulates real physical drift, random environment noise, and edge-case faults."""
    def __init__(self):
        self.lock = threading.Lock()
        self.v_drift = np.array([0.2, -0.1, 0.4])
        self.kappa = 1.0
        self.gs_margin = 1.0
        self.is_running = True
        self.force_fault_type: Optional[str] = None

    def step_environment(self, dt: float, agent_correction: np.ndarray):
        with self.lock:
            # Inject extreme corruption spikes or lock states if an edge-case test is active
            if self.force_fault_type == "NAN_SPIKE":
                self.v_drift = np.array([np.nan, 0.0, 0.0])
                return
            elif self.force_fault_type == "STAGNATE":
                # Do not apply noise or updates; hold data completely static
                return

            # Normal Operation: Process random walk environmental noise
            noise = np.random.normal(0, 0.3, size=3)
            self.v_drift += (noise * dt) + (agent_correction * dt)
            drift_mag = np.linalg.norm(self.v_drift)
            self.kappa = 1.0 + (0.15 * (drift_mag ** 2))
            self.gs_margin = max(0.0, 1.0 - (0.08 * drift_mag))

    def get_telemetry(self) -> Dict[str, Any]:
        with self.lock:
            return {"v_drift": np.copy(self.v_drift), "kappa": self.kappa, "gs_margin": self.gs_margin}

    def trigger_simulated_fault(self, fault_type: str):
        with self.lock:
            self.force_fault_type = fault_type


def run_environment_loop(env: TordialManifoldEnvironment, dt: float, shared: dict):
    while env.is_running:
        start = time.time()
        env.step_environment(dt, shared.get("correction", np.zeros(3)))
        elapsed = time.time() - start
        if elapsed < dt: time.sleep(dt - elapsed)


def run_agent_loop(env: TordialManifoldEnvironment, pipeline: AdaptiveFaultTolerantFilter, controller: TGSController, dt: float, shared: dict):
    print("[AGENT] Active stabilization loop initialized.")
    tick = 0
    while env.is_running:
        start = time.time()
        try:
            # 1. Sense raw telemetry metrics
            telemetry = env.get_telemetry()
            
            # 2. Filter & Intercept Faults
            clean_drift = pipeline.process_sample(telemetry["v_drift"])
            
            # 3. Analyze & Act via PID Engine
            correction = controller.calculate_correction(clean_drift, telemetry["kappa"], dt)
            shared["correction"] = correction
            
            if tick % 15 == 0:
                print(f"[Tick {tick:02d}] Raw Drift Mag: {np.linalg.norm(telemetry['v_drift']):.3f} | Cleaned Mag: {np.linalg.norm(clean_drift):.3f} | GS Headroom: {telemetry['gs_margin']:.2f}")
            tick += 1
            
        except (ValueError, RuntimeError) as fault_exception:
            print(f"\n⚡ BREAK-ALERT: Pipeline intercepted sensor anomaly: {fault_exception}")
            print("[SHUTDOWN] Safely isolating agent workflow threads from contaminated manifold layer.")
            env.is_running = False
            break

        elapsed = time.time() - start
        if elapsed < dt: time.sleep(dt - elapsed)


if __name__ == "__main__":
    manifold_env = TordialManifoldEnvironment()
    shared_registers = {"correction": np.zeros(3)}
    
    # Instantiate the components
    adaptive_filter = AdaptiveFaultTolerantFilter(alpha_min=0.1, alpha_max=0.8)
    pid_stabilizer = TGSController(Kp=2.5, Ki=0.6, Kd=0.1)
    
    time_delta = 0.02
    
    env_thread = threading.Thread(target=run_environment_loop, args=(manifold_env, time_delta, shared_registers))
    agent_thread = threading.Thread(target=run_agent_loop, args=(manifold_env, adaptive_filter, pid_stabilizer, time_delta, shared_registers))
    
    env_thread.start()
    agent_thread.start()
    
    # Let the system stabilize normally under noise for 0.8 seconds
    time.sleep(0.8)
    
    # Inject a simulated sensor freeze to test the fault-detection system
    print("\n[SIMULATION MASTER] Injecting artificial flatline fault into the telemetry pipeline...")
    manifold_env.trigger_simulated_fault("STAGNATE")
    
    env_thread.join()
    agent_thread.join()
    print("[SIMULATION MASTER] Verification complete. System safely disengaged.")
