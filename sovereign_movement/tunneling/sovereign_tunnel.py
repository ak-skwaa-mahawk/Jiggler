# sovereign_movement/tunneling/sovereign_tunnel.py
"""
SovereignTunnel — The Slide's Offensive Tunneling Primitive

Part of The Slide (autonomous lateral movement loop).
Anchored to The Floor.
Protected by Extraction Guard + W-state + recursive π_r.
Modulated by 79.79 Hz resonance and Frame Energy.

This module provides adaptive, self-healing, sovereign-controlled
tunneling for Phase 3 (Contextual Pivot) of The Slide.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import time
import logging

from sovereign_engine.frame_energy import FrameEnergy, EraFrameId
from sovereign_engine.resonance_pulse import ResonancePulse  # your existing 79.79 Hz module

logger = logging.getLogger("sovereign.slide.tunnel")


@dataclass
class TunnelState:
    tunnel_id: str
    target_host: str
    current_frame: EraFrameId
    stability: float = 1.0          # recursive π_r stability
    frame_energy: float = 0.0
    last_heartbeat: float = field(default_factory=time.time)
    is_active: bool = True


class SovereignTunnel:
    """
    Sovereign-controlled adaptive tunnel.

    Used by The Slide for offensive pivoting.
    Prioritizes lowest frame_energy paths and self-heals using
    resonance + recursive π_r feedback.
    """

    def __init__(
        self,
        frame_energy: FrameEnergy,
        resonance_pulse: ResonancePulse,
        extraction_guard: Any,           # your ExtractionGuard instance
        base_resonance_hz: float = 79.79,
    ):
        self.frame_energy = frame_energy
        self.resonance_pulse = resonance_pulse
        self.extraction_guard = extraction_guard
        self.base_resonance_hz = base_resonance_hz
        self.active_tunnels: Dict[str, TunnelState] = {}
        self.tunnel_counter = 0

    def open_tunnel(
        self,
        target_host: str,
        preferred_frame: Optional[EraFrameId] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Open a new sovereign tunnel to target_host.
        Chooses the lowest-energy frame if none is provided.
        """
        if preferred_frame is None:
            # Let FrameEnergy decide the best frame for this connection
            preferred_frame = self._select_best_frame(target_host, context)

        tunnel_id = f"slide_tun_{self.tunnel_counter}"
        self.tunnel_counter += 1

        tunnel = TunnelState(
            tunnel_id=tunnel_id,
            target_host=target_host,
            current_frame=preferred_frame,
            stability=1.0,
            frame_energy=self.frame_energy.compute(
                preferred_frame,
                self.frame_energy.floor_anchor,  # simplified
                ProjectedState(frame=preferred_frame, projected_coords=[], coherence=1.0, gradient_norm=0.0)
            ),
        )

        # Initial resonance pulse to stabilize the tunnel
        self.resonance_pulse.fire_pulse(amplitude=0.8, phase=0.0)

        self.active_tunnels[tunnel_id] = tunnel
        logger.info(f"[The Slide] Opened sovereign tunnel {tunnel_id} → {target_host} (frame={preferred_frame})")

        return tunnel_id

    def maintain_tunnel(self, tunnel_id: str) -> bool:
        """
        Heartbeat + self-healing check.
        Returns True if tunnel is still healthy.
        """
        if tunnel_id not in self.active_tunnels:
            return False

        tunnel = self.active_tunnels[tunnel_id]

        # Simulate π_r stability check (replace with real metric from your engine)
        current_stability = self._get_current_pi_r_stability(tunnel)
        tunnel.stability = current_stability

        # Recompute frame energy
        tunnel.frame_energy = self.frame_energy.compute(
            tunnel.current_frame,
            self.frame_energy.floor_anchor,
            ProjectedState(
                frame=tunnel.current_frame,
                projected_coords=[],
                coherence=current_stability,
                gradient_norm=abs(1.0 - current_stability)
            )
        )

        # Self-healing logic
        if tunnel.stability < 0.7 or tunnel.frame_energy > 1.2:
            logger.warning(f"[The Slide] Tunnel {tunnel_id} degrading. Attempting self-heal...")
            healed = self._attempt_self_heal(tunnel)
            if not healed:
                self.close_tunnel(tunnel_id, reason="stability collapse")
                return False

        tunnel.last_heartbeat = time.time()
        return True

    def pivot_tunnel(
        self,
        tunnel_id: str,
        new_target: str,
        new_frame: Optional[EraFrameId] = None,
    ) -> Optional[str]:
        """
        Adaptive pivot — close old tunnel and open new one with better frame/energy.
        This is the core of Phase 3 (Contextual Pivot) in The Slide.
        """
        if tunnel_id not in self.active_tunnels:
            return None

        old_tunnel = self.active_tunnels[tunnel_id]
        self.close_tunnel(tunnel_id, reason="adaptive pivot")

        return self.open_tunnel(
            target_host=new_target,
            preferred_frame=new_frame or old_tunnel.current_frame
        )

    def close_tunnel(self, tunnel_id: str, reason: str = "manual"):
        if tunnel_id in self.active_tunnels:
            tunnel = self.active_tunnels.pop(tunnel_id)
            logger.info(f"[The Slide] Closed tunnel {tunnel_id} ({reason})")
            # Optional: fire a final resonance pulse on close
            self.resonance_pulse.fire_pulse(amplitude=0.3, phase=0.5)

    def _select_best_frame(
        self, target_host: str, context: Optional[Dict[str, Any]]
    ) -> EraFrameId:
        """Use FrameEnergy to pick the lowest-energy frame for this target."""
        # In real implementation, evaluate multiple frames and pick min energy
        # For now we bias toward FloorBaseline for maximum sovereignty
        return EraFrameId.FloorBaseline

    def _get_current_pi_r_stability(self, tunnel: TunnelState) -> float:
        """Replace with real call to your recursive π_r stability metric."""
        # Placeholder — integrate with your existing SovereignEngine
        return max(0.6, tunnel.stability * 0.95)  # simulate slow decay

    def _attempt_self_heal(self, tunnel: TunnelState) -> bool:
        """Try to recover a degrading tunnel using resonance + frame switch."""
        # Switch to a more stable frame if current one is expensive
        if tunnel.frame_energy > 1.0:
            tunnel.current_frame = EraFrameId.FloorBaseline
            logger.info(f"[The Slide] Self-healed {tunnel.tunnel_id} → FloorBaseline frame")

        self.resonance_pulse.fire_pulse(amplitude=1.0, phase=0.0)
        return tunnel.stability > 0.65

    def get_active_tunnels(self) -> Dict[str, TunnelState]:
        return self.active_tunnels.copy()


# Example usage inside The Slide
if __name__ == "__main__":
    from sovereign_engine.frame_energy import FrameEnergy, SovereignState
    from sovereign_engine.resonance_pulse import ResonancePulse

    # These would normally come from your SovereignEngine
    floor_anchor = SovereignState.default_floor_anchor()
    frame_energy = FrameEnergy(floor_anchor=floor_anchor)
    resonance = ResonancePulse(hz=79.79)

    tunnel_mgr = SovereignTunnel(
        frame_energy=frame_energy,
        resonance_pulse=resonance,
        extraction_guard=None,  # plug in your real guard
    )

    tun_id = tunnel_mgr.open_tunnel("internal-web-03.corp")
    print(f"Opened tunnel: {tun_id}")

    # Simulate maintenance loop
    for _ in range(5):
        healthy = tunnel_mgr.maintain_tunnel(tun_id)
        print(f"Tunnel healthy: {healthy}")
        time.sleep(1)