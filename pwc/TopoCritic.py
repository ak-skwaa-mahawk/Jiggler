"""
pwc/TopoCritic.py
Topological Reasoning Critic for the Tordial-GS Manifold

Integrates the topological cognition stack (extractor + embeddings + reasoning)
into the existing Planner–Walker–Critic overlay.

Provides holonomy-aware, GS-regime-aligned suggestions that the Planner
can use to adjust curvature, drift, GS parameters, or topological structure.
"""

import json
import numpy as np
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from pathlib import Path


@dataclass
class TopoFeedback:
    """Structured feedback the Planner can consume."""
    gs_alignment: float
    curvature_drift_error: float
    sovereign_stability: float
    topological_richness: float
    holonomy_proxy: float
    priority_actions: List[Dict]
    overall_assessment: str
    confidence: float
    recommended_gs_adjustments: Dict
    recommended_curvature_target: float


class TopoCritic:
    """
    Topological Critic component for the Tordial-GS Planner–Walker–Critic loop.

    Loads topological signatures and manifold-aligned embeddings,
    runs reasoning, and produces actionable feedback aligned with
    GS-regime invariants, toroidal geometry, and sovereign stability.
    """

    def __init__(self, 
                 topo_features_path: str = "topo_features.json",
                 embedding_path: str = "manifold_embedding.json",
                 repo_root: str = "."):
        self.topo_path = Path(topo_features_path)
        self.embed_path = Path(embedding_path)
        self.repo_root = Path(repo_root)
        self.signature: Dict = {}
        self.embedding: Dict = {}
        self._load_artifacts()

    def _load_artifacts(self):
        """Load outputs from the topological cognition stack."""
        if self.topo_path.exists():
            with open(self.topo_path) as f:
                self.signature = json.load(f)
        if self.embed_path.exists():
            with open(self.embed_path) as f:
                self.embedding = json.load(f)

    def analyze(self) -> TopoFeedback:
        """Run topological reasoning and return structured feedback for the Planner."""
        if not self.signature:
            return self._fallback_feedback("No topological signature found. Run topo_extractor first.")

        traj = self.signature.get("trajectory", {})
        gs_inv = self.signature.get("gs_invariants", {})

        drift_error = traj.get("drift_error", 0.058)
        stability = traj.get("lock_stability", 1.0)
        gs_align = gs_inv.get("gs_regime_alignment", 0.87)
        richness = gs_inv.get("topological_richness", 0.55)
        holonomy = gs_inv.get("holonomy_proxy", 0.5)

        # Generate priority actions (holonomy-aware)
        actions = self._generate_priority_actions(drift_error, stability, richness, gs_align)

        # Suggested GS / curvature adjustments
        gs_adjust = self._suggest_gs_adjustments(drift_error, gs_align)
        new_curv_target = self._suggest_curvature_target(drift_error)

        overall = self._assess_overall(stability, drift_error, gs_align)

        confidence = min(0.95, max(0.65, (stability + (1 - min(drift_error, 0.2)/0.2) + gs_align) / 3))

        return TopoFeedback(
            gs_alignment=round(gs_align, 4),
            curvature_drift_error=round(drift_error, 4),
            sovereign_stability=round(stability, 4),
            topological_richness=round(richness, 4),
            holonomy_proxy=round(holonomy, 4),
            priority_actions=actions,
            overall_assessment=overall,
            confidence=round(confidence, 3),
            recommended_gs_adjustments=gs_adjust,
            recommended_curvature_target=new_curv_target
        )

    def _generate_priority_actions(self, drift: float, stability: float, richness: float, gs_align: float) -> List[Dict]:
        actions = []

        if drift > 0.05:
            actions.append({
                "action": "curvature_regularization",
                "priority": "medium",
                "description": "Add curvature loss term targeting 1.4 in JED / simulation loop",
                "rationale": f"Current drift {drift:.4f} exceeds comfortable threshold",
                "suggested_code_change": "Introduce `curvature_penalty = 0.1 * (current_curv - 1.4)**2` in unified run objective"
            })

        if richness < 0.6:
            actions.append({
                "action": "holonomy_enrichment",
                "priority": "low-medium",
                "description": "Increase cyclic / feedback structures in code hypergraph and planner–walker loop",
                "rationale": "Moderate topological richness limits manifold expressivity",
                "suggested_code_change": "Add deliberate cross-module holonomy loops between Planner and Critic"
            })

        if stability > 0.98 and drift < 0.07:
            actions.append({
                "action": "sovereign_refinement",
                "priority": "low",
                "description": "System in strong cosmic lock. Consider post-lock refinement phase or multi-manifold coupling.",
                "rationale": "High stability + acceptable drift = opportunity for deeper invariants",
                "suggested_code_change": "Extend JED protocol with optional 'refinement attractor' stage after cycle 15"
            })

        if not actions:
            actions.append({
                "action": "maintain_current_trajectory",
                "priority": "low",
                "description": "Current topological + GS state is well-aligned. Continue monitoring.",
                "rationale": "Strong sovereign lock with good GS-regime behavior"
            })

        return actions

    def _suggest_gs_adjustments(self, drift: float, gs_align: float) -> Dict:
        """Suggest small, safe adjustments to GS / SH parameters."""
        if drift > 0.06:
            return {
                "recommendation": "slight_increase_gs_pressure",
                "current_gs": 1.02,
                "suggested_gs": 1.03,
                "rationale": "Increase GS slightly to tighten regime boundary and reduce drift"
            }
        elif gs_align < 0.8:
            return {
                "recommendation": "review_sh_parameter",
                "current_sh": 1.03,
                "suggested_sh": 1.025,
                "rationale": "Minor SH tuning may improve overall GS-regime alignment"
            }
        else:
            return {
                "recommendation": "no_change",
                "current_gs": 1.02,
                "suggested_gs": 1.02,
                "rationale": "GS parameters already well-tuned for current manifold state"
            }

    def _suggest_curvature_target(self, drift: float) -> float:
        """Suggest refined curvature target."""
        if drift > 0.05:
            return 1.38  # Slightly more conservative while tightening
        return 1.40

    def _assess_overall(self, stability: float, drift: float, gs_align: float) -> str:
        if stability > 0.98 and drift < 0.06 and gs_align > 0.82:
            return "Strong cosmic lock achieved. Topological state is sovereign-aligned with minor curvature refinement opportunity."
        elif stability > 0.9:
            return "Good manifold lock with actionable refinement in curvature or holonomy."
        else:
            return "Moderate alignment. Recommend focused work on drift and topological richness before deeper extension."

    def _fallback_feedback(self, reason: str) -> TopoFeedback:
        return TopoFeedback(
            gs_alignment=0.0,
            curvature_drift_error=0.0,
            sovereign_stability=0.0,
            topological_richness=0.0,
            holonomy_proxy=0.0,
            priority_actions=[{"action": "run_topo_extractor", "priority": "high", "description": reason}],
            overall_assessment=reason,
            confidence=0.3,
            recommended_gs_adjustments={},
            recommended_curvature_target=1.4
        )

    def to_dict(self, feedback: TopoFeedback) -> Dict:
        return asdict(feedback)


# Convenience function for existing PWC code
def get_topo_critic_feedback(
    topo_features_path: str = "topo_features.json",
    embedding_path: str = "manifold_embedding.json"
) -> Dict:
    """Drop-in function the existing Planner or Critic can call."""
    critic = TopoCritic(topo_features_path, embedding_path)
    feedback = critic.analyze()
    return critic.to_dict(feedback)