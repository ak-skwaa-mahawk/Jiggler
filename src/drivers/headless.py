import logging
from .base import BaseDriver

class HeadlessDriver(BaseDriver):
    """Cloud / Docker Headless Driver."""
    def __init__(self):
        self.platform_name = "cloud_headless"
        self.logger = logging.getLogger("HeadlessDriver")

    def emit_event(self, delta_x: float, delta_y: float) -> None:
        self.logger.debug(f"Virtual event applied: ({delta_x}, {delta_y})")
