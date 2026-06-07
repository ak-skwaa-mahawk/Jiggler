cat > topo_extractor/gs_invariants.py << 'PYEOF'
from typing import Dict

def compute_gs_invariants(trajectory_features: Dict, code_features: Dict) -> Dict:
    """Maps extracted features to your Tordial-GS invariant language."""
    drift_error = trajectory_features.get("drift_error", 0.058)
    lock_stability = trajectory_features.get("lock_stability", 1.0)
    betti1 = trajectory_features.get("betti1_proxy", 0) + code_features.get("betti1_proxy", 0)

    # Alignment scores (0–1)
    curvature_alignment = max(0.0, 1.0 - (drift_error / 0.2))
    lock_quality = lock_stability
    topological_richness = min(1.0, betti1 / 12.0)

    gs_regime_score = (curvature_alignment * 0.5 + lock_quality * 0.3 + topological_richness * 0.2)

    return {
        "gs_regime_alignment": round(gs_regime_score, 4),
        "curvature_alignment": round(curvature_alignment, 4),
        "lock_quality": round(lock_quality, 4),
        "topological_richness": round(topological_richness, 4),
        "holonomy_proxy": round(betti1 / 10.0, 4),
        "sovereign_stability": round((lock_quality + curvature_alignment) / 2, 4),
        "interpretation": "Strong GS-regime lock with moderate topological complexity" if gs_regime_score > 0.75 else "Needs refinement in curvature or holonomy"
    }
PYEOF