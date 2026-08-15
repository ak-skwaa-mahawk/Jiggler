from .base import BaseDriver
import ctypes
import sys

class WindowsDriver(BaseDriver):
    def emit_event(self, delta_x: float, delta_y: float) -> None:
        # Windows user32.dll mouse_event
        ctypes.windll.user32.mouse_event(0x0001, int(delta_x), int(delta_y), 0, 0)

class MacOSDriver(BaseDriver):
    def emit_event(self, delta_x: float, delta_y: float) -> None:
        pass

class LinuxDriver(BaseDriver):
    def emit_event(self, delta_x: float, delta_y: float) -> None:
        pass
