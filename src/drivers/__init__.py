import os
import sys

def get_driver():
    # 1. Cloud / Headless Container Detection
    if os.environ.get("HEADLESS") == "1" or (not os.environ.get("DISPLAY") and sys.platform.startswith("linux") and not os.path.exists("/data/data/com.termux")):
        from .headless import HeadlessDriver
        return HeadlessDriver()

    # 2. Termux / Android Edge
    if os.path.exists("/data/data/com.termux"):
        from .edge import TermuxDriver
        return TermuxDriver()

    # 3. Local Desktop OS Platforms
    if sys.platform == "win32":
        from .desktop import WindowsDriver
        return WindowsDriver()
    elif sys.platform == "darwin":
        from .desktop import MacOSDriver
        return MacOSDriver()
    else:
        from .desktop import LinuxDriver
        return LinuxDriver()
