import numpy as np

class TGSController:
    def __init__(self, Kp: float, Ki: float, Kd: float, alpha: float = 0.05):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.alpha = alpha  # Curvature throttling constant
        
        # Persistent state memory across ticks
        self.integral_error = np.zeros(3)
        self.prev_error = np.zeros(3)

    def calculate_correction(self, v_drift: np.ndarray, kappa: float, dt: float) -> np.ndarray:
        """
        Calculates a 3D correction vector while ensuring structural GS bounds.
        v_drift: 3-element numpy array [x, y, z] representing velocity drift.
        kappa: current curvature scalar.
        dt: clock step time interval.
        """
        # 1. Calculate tracking error vector (Target SP is 0)
        error = 0.0 - v_drift
        
        # 2. Accumulate tracking error over time (Integral)
        self.integral_error += error * dt
        
        # 3. Measure current rate of change (Derivative)
        derivative_error = (error - self.prev_error) / dt if dt > 0 else np.zeros(3)
        
        # 4. Synthesize raw PID parallel signals
        u_raw = (self.Kp * error) + (self.Ki * self.integral_error) + (self.Kd * derivative_error)
        
        # 5. Compute the curvature dampening coupling multiplier (chi)
        chi = 1.0 / (1.0 + self.alpha * kappa)
        
        # 6. Cache state for the subsequent tick
        self.prev_error = error
        
        # Return throttled vector to safety envelope
        return u_raw * chi
