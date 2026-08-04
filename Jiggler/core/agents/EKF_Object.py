import threading
import time
import numpy as np
from typing import Dict, Any, Optional, List

class TGSExtendedKalmanFilter:
    """Vectorized Extended Kalman Filter handling non-linear curvature-drift dynamics."""
    def __init__(self, dt: float = 0.02, proc_noise: float = 0.01, meas_noise: float = 0.16, alpha: float = 0.05):
        self.dt = dt
        self.alpha = alpha
        self.lock = threading.Lock()
        
        # State vector [vx, vy, vz]^T
        self.x = np.zeros((3, 1))
        
        # Matrices
        self.I = np.eye(3)
        self.H = np.eye(3)  # Direct sensor observations
        self.P = np.eye(3) * 1.0
        self.Q = np.eye(3) * proc_noise
        self.R = np.eye(3) * meas_noise

    def process_step(self, raw_measurement: np.ndarray, control_input: np.ndarray) -> np.ndarray:
        """Executes a non-linear EKF step via explicit analytical Jacobian evaluation."""
        z = raw_measurement.reshape(3, 1)
        u = control_input.reshape(3, 1)
        
        with self.lock:
            # Current metrics before prediction
            vx, vy, vz = float(self.x[0,0]), float(self.x[1,0]), float(self.x[2,0])
            drift_mag_sq = vx**2 + vy**2 + vz**2
            kappa = 1.0 + 0.15 * drift_mag_sq
            denom = 1.0 + self.alpha * kappa
            
            # --- 1. NON-LINEAR PREDICT PHASE ---
            # Project state forward using the explicit system physics equations
            self.x = self.x * (1.0 / denom) + u * self.dt
            
            # Compute Analytical Jacobian Matrix (F) for error covariance propagation
            # Derivation accounts for d(denom)/dv = alpha * 0.15 * 2 * v = 0.3 * alpha * v
            F = np.zeros((3, 3))
            factor = 0.3 * self.alpha / (denom ** 2)
            
            for i, vi in enumerate([vx, vy, vz]):
                for j, vj in enumerate([vx, vy, vz]):
                    if i == j:
                        F[i, j] = (1.0 / denom) - (vi * factor * vj)
                    else:
                        F[i, j] = - (vi * factor * vj)
            
            # Propagate error covariance using the Jacobian
            self.P = (F @ self.P @ F.T) + self.Q
            
            # --- 2. UPDATE PHASE ---
            # Linear measurement mapping calculation
            S = (self.H @ self.P @ self.H.T) + self.R
            K = self.P @ self.H.T @ np.linalg.inv(S)
            
            residual = z - (self.H @ self.x)
            self.x = self.x + (K @ residual)
            self.P = (self.I - (K @ self.H)) @ self.P
            
            return self.x.flatten()


class StructuralTrendLogger:
    """Asynchronous telemetry logger mapping trends to intercept failures before containment breach."""
    def __init__(self, window_len: int = 10, dt: float = 0.02):
        self.window_len = window_len
        self.dt = dt
        self.history: List[float] = []
        self.lock = threading.Lock()

    def log_state(self, clean_drift: np.ndarray) -> Optional[float]:
        """Tracks the current drift velocity and estimates time-to-breach metrics."""
        drift_mag = float(np.linalg.norm(clean_drift))
        gs_margin = max(0.0, 1.0 - (0.08 * drift_mag))
        
        with self.lock:
            self.history.append(gs_margin)
            if len(self.history) > self.window_len:
                self.history.pop(0)
                
            if len(self.history) < 3:
                return None
                
            # Perform first-derivative linear regression slope calculation over window
            y = np.array(self.history)
            x = np.arange(len(y)) * self.dt
            slope, _ = np.polyfit(x, y, 1)
            
            # Critical Intercept logic: If margin is actively dropping, predict breach boundary
            if slope < 0:
                current_margin = y[-1]
                time_to_breach = (0.15 - current_margin) / slope  # Safety boundary is 0.15
                return max(0.0, time_to_breach)
                
            return float('inf')


class TordialManifoldEnvironment:
    """Simulates physical drift vectors subject to dynamic extreme-load noise."""
    def __init__(self):
        self.lock = threading.Lock()
        self.v_drift = np.array([1.5, -1.0, 0.5])  # Extreme initial load vector
        self.kappa = 1.0
        self.is_running = True

    def step_environment(self, dt: float, correction_force: np.ndarray):
        with self.lock:
            # Simulate extreme continuous physical noise spikes (Simulating structural turbulence)
            turbulence_noise = np.random.normal(0, 0.8, size=3)
            
            drift_mag = np.linalg.norm(self.v_drift)
            self.kappa = 1.0 + (0.15 * (drift_mag ** 2))
            
            # System physics simulation incorporating non-linear damping limits
            damping = 1.0 / (1.0 + 0.05 * self.kappa)
            self.v_drift = self.v_drift * damping + (turbulence_noise * dt) + (correction_force * dt)

    def get_telemetry(self) -> np.ndarray:
        with self.lock:
            return np.copy(self.v_drift)


class TGSController:
    """PID node targeting baseline equilibrium vectors."""
    def __init__(self, Kp: float, Ki: float, Kd: float):
        self.Kp, self.Ki, self.Kd = Kp, Ki, Kd
        self.integral = np.zeros(3)
        self.prev_error = np.zeros(3)

    def calculate_force(self, clean_drift: np.ndarray, dt: float) -> np.ndarray:
        error = 0.0 - clean_drift
        self.integral += error * dt
        derivative = (error - self.prev_error) / dt if dt > 0 else np.zeros(3)
        self.prev_error = error
        return (self.Kp * error) + (self.Ki * self.integral) + (self.Kd * derivative)


# --- Concurrent Test Runner Engine ---
def run_env_loop(env: TordialManifoldEnvironment, dt: float, shared: dict):
    while env.is_running:
        start = time.time()
        env.step_environment(dt, shared.get("force", np.zeros(3)))
        elapsed = time.time() - start
        if elapsed < dt: time.sleep(dt - elapsed)

def run_agent_loop(env: TordialManifoldEnvironment, ekf: TGSExtendedKalmanFilter, logger: StructuralTrendLogger, pid: TGSController, dt: float, shared: dict):
    print("[AGENT] EKF Control System actively tracking manifold coordinates.")
    tick = 0
    while env.is_running:
        start = time.time()
        
        # 1. Sense: Read highly corrupted raw sensor telemetry
        raw_telemetry = env.get_telemetry()
        
        # 2. Filter: Extract clean state estimation vector using non-linear EKF matrices
        current_correction = shared.get("force", np.zeros(3))
        clean_drift = ekf.process_step(raw_telemetry, current_correction)
        
        # 3. Analyze Trend: Evaluate time-to-breach structural trends
        eta_breach = logger.log_state(clean_drift)
        
        # Early-warning intercept trigger
        if eta_breach is not None and eta_breach < 0.5:
            print(f"\n⚠️ [PREDICTIVE WARNING] High-load collapse imminent! Estimated ETA: {eta_breach:.3f}s. Triggering node migration.")
            env.is_running = False
            break
            
        # 4. Act: Generate precise stabilization feedback forces
        shared["force"] = pid.calculate_force(clean_drift, dt)
        
        if tick % 15 == 0:
            gs_margin = 1.0 - (0.08 * np.linalg.norm(clean_drift))
            print(f"[Tick {tick:02d}] Raw Mag: {np.linalg.norm(raw_telemetry):.2f} | Est Mag: {np.linalg.norm(clean_drift):.2f} | GS Headroom: {gs_margin:.2f} | ETA Breach: {f'{eta_breach:.2f}s' if eta_breach != float('inf') else 'Stable'}")
        
        tick += 1
        elapsed = time.time() - start
        if elapsed < dt: time.sleep(dt - elapsed)


if __name__ == "__main__":
    # Initialize extreme load test scenario components
    manifold = TordialManifoldEnvironment()
    registers = {"force": np.zeros(3)}
    
    tgs_ekf = TGSExtendedKalmanFilter(dt=0.02, proc_noise=0.02, meas_noise=0.25)
    trend_logger = StructuralTrendLogger(window_len=12, dt=0.02)
    controller = TGSController(Kp=3.5, Ki=1.2, Kd=0.4)
    
    time_step = 0.02
    
    # Spawn concurrent tracking worker threads
    t_env = threading.Thread(target=run_env_loop, args=(manifold, time_step, registers))
    t_agent = threading.Thread(target=run_agent_loop, args=(manifold, tgs_ekf, trend_logger, controller, time_step, registers))
    
    t_env.start()
    t_agent.start()
    
    try:
        time.sleep(2.0)
    except KeyboardInterrupt:
        pass
    finally:
        manifold.is_running = False
        t_env.join()
        t_agent.join()
        print("[TEST HARNESS] Structural test run terminated.")
