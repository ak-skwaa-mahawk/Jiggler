cat > topo_extractor/embedding_layer.py << 'PYEOF'
import json
import numpy as np
from typing import Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class ManifoldEmbedding:
    """Aligned embedding for the Tordial-GS manifold."""
    toroidal_angles: np.ndarray      # shape (4,) — θ1, θ2, θ3, θ4 style
    gs_regime_vector: np.ndarray     # shape (6,) — TR, GS, curvature, drift, stability, richness
    fused_embedding: np.ndarray      # shape (10,) — combined interpretable vector
    metadata: Dict

def toroidal_angle_embedding(features: Dict) -> np.ndarray:
    """
    Maps key manifold quantities to toroidal angles.
    Uses normalized throat/belt duality + coherence/relax + spin as angular coordinates.
    This respects the periodic / circular nature of your toroidal geometry.
    """
    # Normalize key quantities to [0, 2π]
    throat_norm = (features.get("curvature_drift", 1.342) - 0.0) / 90.0  # rough scale from your belt range
    belt_norm = (features.get("curvature_drift", 1.342) + 34.0) / 90.0   # mirror of throat
    coh_peak = features.get("phase_transitions", {}).get("correspondence_entered_cycle", 8) / 18.0
    lock_stab = features.get("lock_stability", 1.0)

    theta1 = 2 * np.pi * throat_norm                    # throat contraction angle
    theta2 = 2 * np.pi * belt_norm                      # belt expansion angle (dual)
    theta3 = 2 * np.pi * coh_peak                       # correspondence → lock transition
    theta4 = 2 * np.pi * lock_stab                      # final sovereign lock stability

    return np.array([theta1, theta2, theta3, theta4])

def gs_regime_embedding(features: Dict) -> np.ndarray:
    """
    Embeds your GS-regime parameters and invariants.
    Order: [TR, GS, curvature_drift, drift_error, sovereign_stability, topological_richness]
    """
    tr = features.get("tr_value", 3.1730059)
    gs = features.get("gs_regime", 1.02)
    curv = features.get("curvature_drift", 1.342)
    drift_err = features.get("drift_error", 0.058)
    stability = features.get("lock_stability", 1.0)
    richness = features.get("topological_richness", 0.5)  # from gs_invariants if present

    # Simple normalization for embedding stability
    vec = np.array([
        (tr - 3.14) / 0.05,           # centered around π
        (gs - 1.0) / 0.05,
        (curv - 1.0) / 1.0,
        drift_err / 0.2,
        stability,
        richness
    ])
    return vec

def create_manifold_embedding(topological_signature: Dict) -> ManifoldEmbedding:
    """
    Main entry point. Takes the full topo_features.json dict (or trajectory_features + gs_invariants)
    and returns a geometrically aligned embedding.
    """
    traj = topological_signature.get("trajectory", topological_signature)
    gs_inv = topological_signature.get("gs_invariants", {})

    # Merge for convenience
    merged = {**traj, **gs_inv}

    toroidal = toroidal_angle_embedding(merged)
    gs_vec = gs_regime_embedding(merged)

    # Fused embedding (concatenation + light projection for now)
    fused = np.concatenate([toroidal, gs_vec])

    metadata = {
        "source": topological_signature.get("source_log", "unknown"),
        "cosmic_lock": merged.get("lock_stability", 1.0) > 0.99,
        "curvature_drift_error": merged.get("drift_error", 0.058),
        "gs_alignment": gs_inv.get("gs_regime_alignment", 0.8),
        "sovereign_stability": gs_inv.get("sovereign_stability", 0.9),
        "embedding_dim": len(fused)
    }

    return ManifoldEmbedding(
        toroidal_angles=toroidal,
        gs_regime_vector=gs_vec,
        fused_embedding=fused,
        metadata=metadata
    )

def embedding_to_dict(emb: ManifoldEmbedding) -> Dict:
    return {
        "toroidal_angles": emb.toroidal_angles.tolist(),
        "gs_regime_vector": emb.gs_regime_vector.tolist(),
        "fused_embedding": emb.fused_embedding.tolist(),
        "metadata": emb.metadata
    }

# Quick demo using your latest JED data
if __name__ == "__main__":
    # Fallback signature if topo_features.json not present
    demo_signature = {
        "trajectory": {
            "curvature_drift": 1.342,
            "drift_error": 0.058,
            "lock_stability": 1.0,
            "tr_value": 3.1730059,
            "gs_regime": 1.02,
            "phase_transitions": {"correspondence_entered_cycle": 8}
        },
        "gs_invariants": {
            "gs_regime_alignment": 0.87,
            "sovereign_stability": 0.93,
            "topological_richness": 0.55
        }
    }

    emb = create_manifold_embedding(demo_signature)
    print("=== Tordial-GS Manifold-Aligned Embedding ===")
    print(f"Toroidal angles (θ1–θ4): {np.round(emb.toroidal_angles, 4)}")
    print(f"GS-regime vector     : {np.round(emb.gs_regime_vector, 4)}")
    print(f"Fused embedding dim  : {len(emb.fused_embedding)}")
    print(f"Metadata             : {emb.metadata}")
PYEOF