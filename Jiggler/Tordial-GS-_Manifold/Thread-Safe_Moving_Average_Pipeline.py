import numpy as np
from collections import deque
import threading

class ThreadSafeMovingAverageFilter:
    """Efficient ring-buffer implementation of a multi-dimensional moving average filter."""
    def __init__(self, window_size: int = 5, dimensions: int = 3):
        if window_size < 1:
            raise ValueError("Window size must be at least 1.")
        
        self.window_size = window_size
        self.dimensions = dimensions
        self.lock = threading.Lock()
        
        # Instantiate rolling window structures
        self.history = deque(maxlen=window_size)
        
        # Pre-populate history with zeros to prevent empty-window division artifacts
        for _ in range(window_size):
            self.history.append(np.zeros(dimensions))
            
        # Running sum cache for fast updates
        self.running_sum = np.zeros(dimensions)

    def process_sample(self, raw_sample: np.ndarray) -> np.ndarray:
        """
        Incorporate a new raw measurement and return the smoothed vector.
        Operates with constant time complexity O(1).
        """
        if raw_sample.shape[0] != self.dimensions:
            raise ValueError(f"Sample dimension must be matching: {self.dimensions}")
            
        with self.lock:
            # Drop the oldest item from the sum cache before deque pops it
            oldest_sample = self.history[0]
            self.running_sum -= oldest_sample
            
            # Append new observation
            self.history.append(raw_sample)
            self.running_sum += raw_sample
            
            # Compute current smoothed output
            return self.running_sum / self.window_size
