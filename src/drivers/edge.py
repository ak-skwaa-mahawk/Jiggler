import sys
from .base import BaseDriver

class TermuxDriver(BaseDriver):
    """Termux / Android Edge Driver using stdout/telemetry pipes."""
    def __init__(self):
        self.platform_name = "termux_arm64"

    def emit_event(self, delta_x: float, delta_y: float) -> None:
        # Pushes discrete micro-offset into standard output stream
        sys.stdout.write(f"\r[EDGE-TELEMETRY] dx: {delta_x:+.6f} | dy: {delta_y:+.6f}")
        sys.stdout.flush()
