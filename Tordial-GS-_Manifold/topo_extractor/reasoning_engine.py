cat > topo_extractor/reasoning_engine.py << 'PYEOF'
import json
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict

@dataclass
class ReasoningReport:
    gs_alignment: float
    curvature_drift_error: float
    sovereign_stability: float
    topological_richness: float
    holonomy_proxy: float
    suggestions: List[Dict]
    overall_assessment: str
    confidence: float

class TopologicalReasoningEngine:
    """
    Planner–Walker–Critic reasoning engine for the Tordial-GS manifold.
    Reasons over toroidal + GS-regime embeddings and produces holonomy-aware suggestions.
    """

    def __init__(self, topo_signature: Dict, embedding: Dict):
        self.signature = topo_signature
        self.embedding = embedding
        self.traj = topo_signature.get("trajectory", {})
        self.gs = topo_signature.get("gs_invariants", {})
        self.meta = embedding.get("metadata", {})

    def plan(self) -> List[str]:
        """Planner: decides which invariants to analyze deeply."""
        focus_areas = []
        drift = self.traj.get("drift_error", 0.058)
        stability = self.traj.get("lock_stability", 1.0)
        richness = self.gs.get("topological_richness", 0.5)
        gs_align = self.gs.get("gs_regime_alignment", 0.8)

        if drift > 0.05:
            focus_areas.append("curvature_drift")
        if stability < 0.95:
            focus_areas.append("lock_stability")
        if richness < 0.6:
            focus_areas.append("topological_richness")
        if gs_align < 0.75:
            focus_areas.append("gs_regime_alignment")

        if not focus_areas:
            focus_areas = ["refinement", "extension"]  # system is already strong
        return focus_areas

    def walk(self, focus_areas: List[str]) -> Dict:
        """Walker: traverses the embedding and feature space for relevant signals."""
        signals = {}
        emb_vec = np.array(self.embedding.get("fused_embedding", [0]*10))

        for area in focus_areas:
            if area == "curvature_drift":
                signals[area] = {
                    "current_drift": self.traj.get("drift_error", 0.058),
                    "target": 0.0,
                    "severity": "moderate" if self.traj.get("drift_error", 0.058) > 0.04 else "low"
                }
            elif area == "topological_richness":
                signals[area] = {
                    "betti1_proxy": self.traj.get("betti1_proxy", 5),
                    "hypergraph_density": self.signature.get("codebase", {}).get("hypergraph_density", 0.3),
                    "interpretation": "moderate cyclic structure detected"
                }
            elif area == "refinement":
                signals[area] = {
                    "lock_quality": self.traj.get("lock_stability", 1.0),
                    "gs_alignment": self.gs.get("gs_regime_alignment", 0.87),
                    "recommendation_direction": "tighten curvature or increase holonomy loops"
                }
            elif area == "extension":
                signals[area] = {
                    "current_state": "strong_cosmic_lock",
                    "opportunity": "add higher-order toroidal invariants or multi-manifold coupling"
                }
        return signals

    def criticize(self, signals: Dict) -> List[Dict]:
        """Critic: generates holonomy-aware, actionable suggestions."""
        suggestions = []

        for area, data in signals.items():
            if area == "curvature_drift":
                suggestions.append({
                    "type": "curvature_correction",
                    "priority": "medium",
                    "suggestion": "Add explicit curvature regularization term in JED protocol (target 1.4). Consider small adjustment to GS or SH parameters.",
                    "code_hint": "In jed_unified_*.py: add `curvature_loss = (current_curv - 1.4)**2 * 0.1` to the unified run objective.",
                    "expected_impact": "Reduce drift_error from \~0.058 toward <0.03",
                    "confidence": 0.82
                })
            elif area == "topological_richness":
                suggestions.append({
                    "type": "holonomy_enrichment",
                    "priority": "low-medium",
                    "suggestion": "Increase cyclic structures in the code hypergraph (more long-range call edges or recursive GS-regime transitions).",
                    "code_hint": "In code_graph.py or your planner–walker loop: add deliberate cross-module holonomy loops (e.g., feedback from critic → planner).",
                    "expected_impact": "Raise betti1_proxy and topological_richness",
                    "confidence": 0.75
                })
            elif area == "refinement":
                suggestions.append({
                    "type": "sovereign_refinement",
                    "priority": "low",
                    "suggestion": "System already shows strong cosmic lock. Focus on tightening TR recurrence or adding vhitzee-style coherence harvesting in the locked regime.",
                    "code_hint": "Extend JED protocol with a post-lock 'refinement phase' that optimizes within the attractor basin.",
                    "expected_impact": "Further improve sovereign_stability and GS alignment",
                    "confidence": 0.88
                })
            elif area == "extension":
                suggestions.append({
                    "type": "manifold_extension",
                    "priority": "exploratory",
                    "suggestion": "The manifold is in a strong locked state. Consider coupling multiple Tordial-GS instances or adding higher-dimensional toroidal angles (θ5+).",
                    "code_hint": "Extend embedding_layer.py toroidal_angle_embedding to 5–6 dimensions and test multi-manifold fusion.",
                    "expected_impact": "Prepare for scalable sovereign multi-node architectures",
                    "confidence": 0.70
                })

        return suggestions

    def run(self) -> ReasoningReport:
        """Full planner–walker–critic cycle."""
        focus = self.plan()
        signals = self.walk(focus)
        suggestions = self.criticize(signals)

        overall = "Strong sovereign lock achieved. Minor curvature drift present but system is stable and aligned."
        if any(s["priority"] in ["medium", "high"] for s in suggestions):
            overall = "Good cosmic lock with actionable refinement opportunities in curvature and holonomy."

        confidence = np.mean([s.get("confidence", 0.7) for s in suggestions]) if suggestions else 0.85

        return ReasoningReport(
            gs_alignment=self.gs.get("gs_regime_alignment", 0.87),
            curvature_drift_error=self.traj.get("drift_error", 0.058),
            sovereign_stability=self.gs.get("sovereign_stability", 0.93),
            topological_richness=self.gs.get("topological_richness", 0.55),
            holonomy_proxy=self.gs.get("holonomy_proxy", 0.5),
            suggestions=suggestions,
            overall_assessment=overall,
            confidence=round(float(confidence), 3)
        )

def generate_report(topo_path: str = "topo_features.json", embed_path: str = "manifold_embedding.json") -> ReasoningReport:
    with open(topo_path) as f:
        topo = json.load(f)
    with open(embed_path) as f:
        emb = json.load(f)

    engine = TopologicalReasoningEngine(topo, emb)
    report = engine.run()

    with open("reasoning_report.json", "w") as f:
        json.dump(asdict(report), f, indent=2)

    return report
PYEOF