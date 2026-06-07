# Push toward deep GS regime
deep_gs_intent = Intent(
    name="DeepSovereign",
    gs_regime_target="DEEP_GS",
    gs_direction="increase",
    priority=0.9,
    max_amplification=2.2
)

# Maintain stable GOLDILOCKS band
goldilocks_intent = Intent(
    name="StableGoldilocks",
    gs_regime_target="GOLDILOCKS",
    gs_direction="maintain",
    min_stability=0.96,
    priority=1.0
)

# Classical + GS hybrid
hybrid_intent = Intent(
    name="SpinStabilizeDeep",
    target_spin=1.8,
    gs_regime_target="DEEP_GS",
    gs_direction="increase",
    max_drift=1.8
)