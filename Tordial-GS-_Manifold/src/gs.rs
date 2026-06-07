cat << 'EOF' > src/gs.rs
// gs.rs
// GS non-associative combiner over coupling edges with active curvature memory.

#[derive(Debug, Clone)]
pub struct GsEdgeState {
    pub curvature: f64,
}

impl GsEdgeState {
    pub fn new() -> Self {
        Self { curvature: 0.0 }
    }
}

pub struct GsCombiner;

impl GsCombiner {
    /// Non-associative update: order-sensitive via mutable curvature state and stiffness constraints.
    pub fn update(
        old_c: f64,
        c_eff: f64,
        stiffness: f64,
        alpha: f64,
        state: &mut GsEdgeState,
    ) -> f64 {
        let softness = 1.0 - stiffness; // softer bands adapt more
        let delta = c_eff - old_c;

        // First-order drift calculation
        let forward = old_c + alpha * softness * delta;

        // Curvature memory: accumulate signed curvature of physical updates over time
        state.curvature += alpha * delta * softness;

        // Second-order correction: bend toward c_eff biased by historical wave trends
        let curved = forward + 0.5 * state.curvature * softness;

        // Clamp to a sane operational manifold boundary range
        curved.clamp(0.0, 1.5)
    }
}
EOF
