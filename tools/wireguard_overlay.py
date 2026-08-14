#!/usr/bin/env python3
"""
wireguard_overlay.py: Dynamic policy routing controller based on Lie Holonomy Norm.
Switches default flow transit between direct WAN and WireGuard cloud relay.
"""

import subprocess
import shutil
from pathlib import Path

class WireGuardOverlayRouter:
    def __init__(self, wg_interface="wg0", direct_interface="wlan0", entropy_threshold=0.150):
        self.wg_interface = wg_interface
        self.direct_interface = direct_interface
        self.entropy_threshold = entropy_threshold
        self.active_route = "DIRECT"  # 'DIRECT' or 'WIREGUARD_RELAY'
        self.ip_available = shutil.which("ip") is not None
        self.wg_available = shutil.which("wg") is not None

    def evaluate_transit_route(self, h_norm, rollback):
        """
        Determines the optimal transit path based on the current Frobenius Holonomy Norm.
        """
        previous_route = self.active_route
        
        # If safety ceiling tripped or entropy exceeds basin threshold -> route via Cloud Relay
        if rollback or h_norm > self.entropy_threshold:
            self.active_route = "WIREGUARD_RELAY"
        else:
            self.active_route = "DIRECT"

        route_changed = (self.active_route != previous_route)
        if route_changed:
            self._apply_routing_policy()

        return self.active_route, route_changed

    def _apply_routing_policy(self):
        """
        Executes Linux policy routing (ip rule / ip route).
        """
        if not self.ip_available:
            return False

        try:
            if self.active_route == "WIREGUARD_RELAY":
                # Route table 51820 via WireGuard interface
                subprocess.run(
                    ["ip", "rule", "add", "fwmark", "0x51820", "table", "51820"],
                    capture_output=True, timeout=0.010
                )
                subprocess.run(
                    ["ip", "route", "replace", "default", "dev", self.wg_interface, "table", "51820"],
                    capture_output=True, timeout=0.010
                )
            else:
                # Flush or remove policy mark rule
                subprocess.run(
                    ["ip", "rule", "del", "fwmark", "0x51820", "table", "51820"],
                    capture_output=True, timeout=0.010
                )
            return True
        except Exception:
            return False
