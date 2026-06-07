import threading
import time
import numpy as np
from typing import Dict, Any, Optional

class AdaptiveFaultTolerantFilter:
    """
    Advanced TGS pipeline combining an adaptive tracking window 
    with real-time sensor failure interceptors.
    """
    def __init__(self, alpha_min: float = 0.1, alpha_max: float = 0.8, dimensions: int = 3):
        self.alpha_min = alpha_min
        self.alpha_max = alpha_max
        self.dimensions = dimensions
        self.lock = threading.Lock()
        
        # State tracking registers
        self.prev_filtered: Optional[np.ndarray] = None
        self.prev_raw: Optional[np.ndarray] = None
        self.flatline_counter = 0

    def process_sample(self, raw_sample: np.ndarray) -> np.ndarray:
        """
        Validates, checks for faults, and filters raw multi-dimensional vectors.
        """
        with self.lock:
            # --- 1. FAULT DETECTION LAYER ---
            # Check A: Numerical corruption detection (NaN or Infinities)
            if not np.isfinite(raw_sample).all():
                raise ValueError("[CRITICAL FAULT] Telemetry contains corrupted non-finite numbers (NaN/Inf)!")
            
            # Check B: Flatline stagnation detection
            if self.prev_raw is not None:
                if np.allclose(raw_sample, self.prev_raw, atol=1e-6):
                    self.flatline_counter += 1
                else:
                    self.flatline_counter = 0
                    
            if self.flatline_counter > 15:  # Trigger if data stays identical for 15 frames
                raise RuntimeError(f"[CRITICAL FAULT] Sensor flatline detected! Data frozen for {self.flatline_counter} frames.")
            
            self.prev_raw = np.copy(raw_sample)

            # --- 2. COLD START INITIALIZATION ---
            if self.prev_filtered is None:
                self.prev_filtered = np.copy(raw_sample)
                return self.prev_filtered

            # --- 3. ADAPTIVE SMOOTHING CALCULATION ---
            # Calculate how far the system shifted compared to the last filtered step
            innovation = np.linalg.norm(raw_sample - self.prev_filtered)
            
            # Dynamically scale alpha: bigger shifts produce higher alphas (less lag)
            # Scaling sensitivity is mapped using an exponential expansion
            dynamic_alpha = self.alpha_min + (self.alpha_max - self.alpha_min) * (1.0 - np.exp(-0.7 * innovation))
            dynamic_alpha = np.clip(dynamic_alpha, self.alpha_min, self.alpha_max)

            # Apply the recursive EWMA calculation
            filtered_output = (dynamic_alpha * raw_sample) + ((1.0 - dynamic_alpha) * self.prev_filtered)
            self.prev_filtered = filtered_output
            
            return filtered_output
