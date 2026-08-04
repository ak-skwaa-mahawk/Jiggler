import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')

class TauDriftDetector:
    def __init__(self, py_combiner, threshold=0.085):
        self.combiner = py_combiner  # Reference to the compiled Rust PyCombiner instance
        self.threshold = threshold
        self.trajectory_history = []
        self.weights_locked = False
        self.window_size = 10

    def verify_trajectory(self, current_state: list, expected_baseline_state: list) -> bool:
        """
        Evaluates system stability using the native Riemannian metric tensor.
        """
        if self.weights_locked:
            return False

        if len(current_state) < 2 or len(expected_baseline_state) < 2:
            logging.error("🚨 State dimensions insufficient for toroidal geodesic tracking!")
            return False

        try:
            # Drop flat-space math. Compute the actual curved geodesic path length using Rust!
            drift = self.combiner.native_geodesic_distance(current_state, expected_baseline_state)
        except Exception as e:
            logging.error(f"Error computing native geodesic distance: {e}")
            # Fallback to standard Euclidean if shape mismatch occurs during mid-flight hot swaps
            drift = np.sqrt(np.mean((np.array(current_state) - np.array(expected_baseline_state)) ** 2))

        self.trajectory_history.append(drift)

        # Dynamic Window Strategy based on local position (Poloidal Angle theta = current_state[0])
        # If theta slips into the unstable inner tube (Endo-Tube), compress the sampling window
        theta = current_state[0]
        # Wrap angle locally to check bounds matching the specification sheet
        wrapped_theta = (theta + np.pi) % (2 * np.pi) - np.pi
        
        if np.pi/2 < abs(wrapped_theta):
            self.window_size = 3  # Aggressive monitoring in negative curvature zones
        else:
            self.window_size = 10 # Nominal monitoring in stable/flat zones

        # Enforce memory capacity bounds
        if len(self.trajectory_history) > self.window_size:
            self.trajectory_history.pop(0)

        # Evaluate trend constraints
        if len(self.trajectory_history) >= 3:
            recent_mean = np.mean(self.trajectory_history[-3:])
            if recent_mean > self.threshold:
                logging.critical(f"⚠️ [τ-DRIFT GEODESIC VIOLATION] Breach detected! Mean Metric: {recent_mean:.5f} > Max: {self.threshold}")
                logging.critical("🔒 MANIFOLD COGNITIVE WEIGHTS LOCKED. Halting parameter mutation cycles.")
                self.weights_locked = True
                return False

        return True

    def reset_lock(self):
        self.trajectory_history.clear()
        self.weights_locked = False
        logging.info("🔓 Telemetry monitor reset. Manifold learning parameters unlocked.")
