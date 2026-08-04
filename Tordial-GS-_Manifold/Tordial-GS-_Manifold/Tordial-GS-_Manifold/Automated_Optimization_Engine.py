import numpy as np
from typing import Tuple, List, Dict

class TGSSimulator:
    """Deterministic simulation model for offline PID parameter evaluation."""
    def __init__(self, initial_drift: np.ndarray, steps: int = 200, dt: float = 0.02):
        self.initial_drift = initial_drift
        self.steps = steps
        self.dt = dt
        # Generate a seed-locked noise profile to ensure fair evaluation across all runs
        np.random.seed(42)
        self.noise_profile = np.random.normal(0, 0.5, size=(steps, 3))

    def evaluate(self, Kp: float, Ki: float, Kd: float, alpha: float = 0.05) -> float:
        """
        Runs a simulation run for a single set of tuning parameters.
        Returns a total penalty score (Lower score = Better stability).
        """
        v_drift = np.copy(self.initial_drift)
        integral_error = np.zeros(3)
        prev_error = np.zeros(3)
        
        total_loss = 0.0
        collapsed = False

        for step in range(self.steps):
            # 1. Physical metrics calculation
            drift_magnitude = np.linalg.norm(v_drift)
            kappa = 1.0 + (0.15 * (drift_magnitude ** 2))
            gs_margin = max(0.0, 1.0 - (0.08 * drift_magnitude))

            # Hard constraint: Check for structural collapse
            if gs_margin < 0.15:
                collapsed = True
                break

            # 2. Accumulate MSE tracking loss (penalize drift deviations from zero)
            total_loss += (drift_magnitude ** 2)

            # 3. Process controller loop
            error = 0.0 - v_drift
            integral_error += error * self.dt
            derivative_error = (error - prev_error) / self.dt
            
            # Apply standard manifold formulas
            u_raw = (Kp * error) + (Ki * integral_error) + (Kd * derivative_error)
            chi = 1.0 / (1.0 + alpha * kappa)
            correction = u_raw * chi
            
            # 4. Step system physics state forward
            noise = self.noise_profile[step]
            v_drift += (noise * self.dt) + (correction * self.dt)
            prev_error = error

        # Return a maximized penalty score if the configuration caused a system collapse
        if collapsed:
            return float('inf')

        # Return the normalized average tracking error score
        return total_loss / self.steps


def run_grid_search(kp_range: List[float], ki_range: List[float], kd_range: List[float]) -> Dict[str, Any]:
    """Iterates systematically through parameter permutations to locate optimal performance."""
    # Start the test with an uncorrected geometric drift injection
    starting_shock = np.array([2.0, -1.5, 0.8])
    simulator = TGSSimulator(initial_drift=starting_shock, steps=250, dt=0.02)
    
    best_score = float('inf')
    best_params = {"Kp": 0.0, "Ki": 0.0, "Kd": 0.0}
    tested_count = 0

    print("=" * 60)
    print("STARTING TGS MANIFOLD TUNING OPTIMIZATION")
    print("=" * 60)

    for kp in kp_range:
        for ki in ki_range:
            for kd in kd_range:
                tested_count += 1
                score = simulator.evaluate(kp, ki, kd)
                
                if score < best_score:
                    best_score = score
                    best_params = {"Kp": kp, "Ki": ki, "Kd": kd}
                    print(f"[Match Found] Run {tested_count:03d} -> Score: {score:.4f} | Kp={kp:.1f}, Ki={ki:.1f}, Kd={kd:.2f}")

    print("=" * 60)
    print("OPTIMIZATION COMPLETE")
    print(f"Total Iterations Parsed: {tested_count}")
    print(f"Optimal Target Configuration: {best_params}")
    print(f"Minimum Baseline Drift Loss: {best_score:.4f}")
    print("=" * 60)
    
    return best_params

# --- Optimization Setup ---
if __name__ == "__main__":
    # Define discrete search parameters based on operational scaling envelopes
    kp_grid = [1.0, 1.5, 2.0, 2.5, 3.0]
    ki_grid = [0.2, 0.5, 0.8, 1.2]
    kd_grid = [0.05, 0.1, 0.2, 0.3]

    optimal_settings = run_grid_search(kp_grid, ki_grid, kd_grid)
