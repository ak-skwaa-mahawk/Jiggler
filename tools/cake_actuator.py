#!/usr/bin/env python3
"""
cake_actuator.py: Real-time dynamic CAKE bandwidth modulator for Linux tc.
Translates damped Lie-subspace commutators into kernel qdisc adjustments.
"""

import subprocess
import shutil

class CakeActuator:
    def __init__(self, interface="wlan0", base_rate_mbps=100.0, min_mbps=10.0, max_mbps=300.0):
        self.interface = interface
        self.base_rate = base_rate_mbps
        self.min_rate = min_mbps
        self.max_rate = max_mbps
        self.current_rate = base_rate_mbps
        self.tc_available = shutil.which("tc") is not None

    def apply_control_action(self, comm1, comm2, h_norm, rollback):
        """
        Calculates target bandwidth and updates the kernel qdisc via tc.
        """
        if rollback:
            # Fallback safe rate on safety floor trip
            self.current_rate = self.min_rate * 1.5
        else:
            # Comm1 = Queue rate, Comm2 = Latency jitter
            # Negative feedback: positive commutator reduces bandwidth to clear bottleneck
            modulation = -(comm1 * 2.5 + comm2 * 1.5)
            target = self.base_rate * (1.0 + modulation)
            self.current_rate = float(min(self.max_rate, max(self.min_rate, target)))

        return self._push_to_kernel()

    def _push_to_kernel(self):
        cmd = [
            "tc", "qdisc", "change", "dev", self.interface,
            "root", "cake", "bandwidth", f"{self.current_rate:.1f}mbit"
        ]
        
        if self.tc_available:
            try:
                subprocess.run(cmd, capture_output=True, timeout=0.010)
                return True, self.current_rate
            except Exception:
                pass
        
        # Returns simulated state if running unprivileged/mock mode
        return False, self.current_rate
