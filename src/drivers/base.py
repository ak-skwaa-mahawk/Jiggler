from abc import ABC, abstractmethod
import time
import random

class BaseDriver(ABC):
    """
    Universal Driver Interface Specification for Cross-Platform Event Emission.
    """

    @abstractmethod
    def emit_event(self, delta_x: float, delta_y: float) -> None:
        """Apply a movement, packet pacing, or coordinate shift."""
        pass

    def sleep_jittered(self, base_seconds: float, variance: float = 0.05) -> None:
        """Apply random timing offset to avoid mechanical signatures."""
        spread = (base_seconds * variance) if variance < 1.0 else variance
        offset = random.uniform(-spread, spread)
        time.sleep(max(0.0, base_seconds + offset))
