import threading
import time
import numpy as np
from typing import Dict, Any

class TordialManifoldEnvironment:
    """Simulates the physical macro/micro state of the TGS Manifold."""
    def __init__(self):
        self.lock = threading.Lock()
        # Initializing 3D state arrays: [x, y, z]
        self.v_drift = np.array([0.5, -0.2, 0.1])
        self.kappa = 1.0  # Initial curvature scalar
        self.gs_margin = 1.0  # Structural headroom matrix
        self.is_running = True

    def step_environment(self, dt: float, agent_correction: np.ndarray):
        """Updates internal environment equations with physics, noise, and correction forces."""
        with self.lock:
            # 1. Simulate an external system shock or macro noise spike (Random Walk)
            environmental_noise = np.random.normal(0, 0.4, size=3)
            
            # 2. Physics update: New drift = Current drift + Noise + Agent Stabilizing Counter-Force
            self.v_drift += (environmental_noise * dt) + (agent_correction * dt)
            
            # 3. Micro-scale interaction: High drift warps curvature space (kappa)
            drift_magnitude = np.linalg.norm(self.v_drift)
            self.kappa = 1.0 + (0.15 * (drift_magnitude ** 2))
            
            # 4. GS inequality checking: Safety margin degrades under raw stress
            self.gs_margin = max(0.0, 1.0 - (0.08 * drift_magnitude))

    def get_telemetry(self) -> Dict[str, Any]:
        """Provides thread-safe data reads for the monitoring agent."""
        with self.lock:
            return {
                "v_drift": np.copy(self.v_drift),
                "kappa": self.kappa,
                "gs_margin": self.gs_margin
            }

    def stop(self):
        self.is_running = False


def run_environment_loop(env: TordialManifoldEnvironment, dt: float, runtime_shared: dict):
    """Worker thread tasked with running the baseline environment physics loop."""
    print("[ENV] Toroidal physical environment engine online.")
    while env.is_running:
        start_time = time.time()
        
        # Pull correction vector calculated by the agent thread
        current_correction = runtime_shared.get("correction", np.zeros(3))
        
        # Tick the environment physics simulator forward
        env.step_environment(dt, current_correction)
        
        # Enforce constant physical sampling interval frequency
        elapsed = time.time() - start_time
        if elapsed < dt:
            time.sleep(dt - elapsed)


def run_agent_loop(env: TordialManifoldEnvironment, controller: Any, dt: float, runtime_shared: dict):
    """Worker thread executing the automated TGS control policy."""
    print("[AGENT] Autonomous stabilization agent loop initialized.")
    tick_count = 0
    
    while env.is_running:
        start_time = time.time()
        
        # 1. Sense: Read current environment telemetry metrics safely
        telemetry = env.get_telemetry()
        v_drift = telemetry["v_drift"]
        kappa = telemetry["kappa"]
        gs_margin = telemetry["gs_margin"]
        
        # 2. Safety Intercept: Detect structural collapse risks (Golod-Shafarevich limit)
        if gs_margin < 0.15:
            print(f"\n[CRITICAL ERROR] Tick {tick_count}: GS Margin Deficit ({gs_margin:.3f})! Initiating failover.")
            env.stop()
            break
            
        # 3. Analyze & Act: Execute tracking calculations via PID formulas
        correction = controller.calculate_correction(v_drift, kappa, dt)
        
        # Expose computed pressure vector back to the physics environment thread
        runtime_shared["correction"] = correction
        
        # Diagnostic logging profile reporting to stdout
        if tick_count % 10 == 0:
            drift_mag = np.linalg.norm(v_drift)
            print(f"[Agent T-{tick_count:03d}] Drift Mag: {drift_mag:.3f} | Curvature (κ): {kappa:.2f} | GS Headroom: {gs_margin:.2f}")
            
        tick_count += 1
        
        # Exact scheduling logic matching execution intervals
        elapsed = time.time() - start_time
        if elapsed < dt:
            time.sleep(dt - elapsed)


# --- Test Execution Harness ---
if __name__ == "__main__":
    from main_controller import TGSController  # Import the class designed in the previous block
    
    # 1. Initialize core system modules
    manifold_env = TordialManifoldEnvironment()
    shared_registers = {"correction": np.zeros(3)}
    
    # Tuning parameters: High Proportional and Integral gains to handle intense noise profiles
    pid_stabilizer = TGSController(Kp=2.5, Ki=0.8, Kd=0.2, alpha=0.05)
    
    # Configure operational execution step frequencies (50Hz / 20ms steps)
    time_delta = 0.02 
    
    # 2. Spawning decoupled operational threads
    env_thread = threading.Thread(target=run_environment_loop, args=(manifold_env, time_delta, shared_registers))
    agent_thread = threading.Thread(target=run_agent_loop, args=(manifold_env, pid_stabilizer, time_delta, shared_registers))
    
    # Begin concurrent processing engine threads
    env_thread.start()
    agent_thread.start()
    
    # Let the simulation run for a brief testing window
    try:
        time.sleep(1.5)
    except KeyboardInterrupt:
        pass
    finally:
        print("\n[SYSTEM] Terminating active test threads...")
        manifold_env.stop()
        env_thread.join()
        agent_thread.join()
        print("[SYSTEM] Simulation shutdown process complete.")
