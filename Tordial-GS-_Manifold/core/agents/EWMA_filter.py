import numpy as np
import threading
from typing import Optional

class ThreadSafeEWMAFilter:
    """Memory-efficient recursive Exponentially Weighted Moving Average filter."""
    def __init__(self, alpha: float = 0.3, dimensions: int = 3):
        if not (0.0 < alpha <= 1.0):
            raise ValueError("Smoothing factor 'alpha' must be strictly between 0.0 and 1.0")
            
        self.alpha = alpha
        self.dimensions = dimensions
        self.lock = threading.Lock()
        
        # Persistent state memory holding the prior filtered vector
        self.prev_filtered: Optional[np.ndarray] = None

    def process_sample(self, raw_sample: np.ndarray) -> np.ndarray:
        """
        Processes a raw incoming vector and computes the updated EWMA estimate.
        Operates with absolute constant time and space efficiency O(1).
        """
        if raw_sample.shape != (self.dimensions,):
            raise ValueError(f"Sample dimensions must match initialization shape: ({self.dimensions},)")
            
        with self.lock:
            # Cold start logic: Initialize memory cache with the first raw sample
            if self.prev_filtered is None:
                self.prev_filtered = np.copy(raw_sample)
                return self.prev_filtered
            
            # Apply recursive EWMA formulation: α*X_raw + (1-α)*Y_prev
            filtered_output = (self.alpha * raw_sample) + ((1.0 - self.alpha) * self.prev_filtered)
            
            # Cache the newly calculated state for the next discrete iteration
            self.prev_filtered = filtered_output
            
            return filtered_output

    def reset(self):
        """Resets the persistent memory to handle environment reboots cleanly."""
        with self.lock:
            self.prev_filtered = None
