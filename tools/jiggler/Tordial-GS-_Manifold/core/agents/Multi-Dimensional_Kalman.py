import numpy as np
import threading

class ThreadSafeKalmanFilter3D:
    """Vectorized 3D Kalman Filter for isolating true state metrics from noise."""
    def __init__(self, dt: float = 0.02, process_noise: float = 0.05, sensor_noise: float = 0.36):
        self.lock = threading.Lock()
        
        # State vector initialization: [x_vel, y_vel, z_vel]
        self.x = np.zeros((3, 1))
        
        # Identity and state transitions
        self.I = np.eye(3)
        self.A = np.eye(3)  # Velocity remains steady in predictor unless acted upon
        self.H = np.eye(3)  # Direct sensor mappings to velocity coordinates
        
        # Covariance Matrices
        self.P = np.eye(3) * 1.0       # Initial estimation uncertainty
        self.Q = np.eye(3) * process_noise  # Internal environment turbulence variance
        self.R = np.eye(3) * sensor_noise   # External sensor jitter variance

    def process_telemetry(self, raw_measurement: np.ndarray, control_input: np.ndarray) -> np.ndarray:
        """
        Executes a complete Predict-Update sequence for an incoming 3D sample vector.
        raw_measurement: 3-element array from sensors.
        control_input: 3-element current PID correction array (acts as vector B*u).
        """
        # Reshape vectors to 3x1 column matrices for standard linear algebra operations
        z = raw_measurement.reshape(3, 1)
        u = control_input.reshape(3, 1)
        
        with self.lock:
            # --- 1. PREDICT PHASE ---
            # Project state forward using state transition and active control inputs
            self.x = (self.A @ self.x) + u
            self.P = (self.A @ self.P @ self.A.T) + self.Q
            
            # --- 2. UPDATE PHASE ---
            # Calculate Innovation Covariance S
            S = (self.H @ self.P @ self.H.T) + self.R
            
            # Calculate optimal Kalman Gain matrix K
            K = self.P @ self.H.T @ np.linalg.inv(S)
            
            # Refine estimates using actual measurement divergence (residual)
            residual = z - (self.H @ self.x)
            self.x = self.x + (K @ residual)
            
            # Update state error uncertainty covariance
            self.P = (self.I - (K @ self.H)) @ self.P
            
            # Return flattened 3-element estimation array
            return self.x.flatten()
