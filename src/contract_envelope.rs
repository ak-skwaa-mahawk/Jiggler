cat > src/contract_envelope.rs << 'ENDENV'
/*
 * contract_envelope.rs
 * The Governing Constitution of the ISST-TOFT Sovereign Substrate.
 * Defines absolute metric boundaries, velocity caps, and dynamic adjustment factors.
 */

#[derive(Debug, Clone)]
pub struct ContractEnvelope {
    // Absolute Parallel Transport Boundaries
    pub holonomy_min: f64,           // Floor: below this, system is too rigid/symmetric
    pub holonomy_max: f64,           // Ceiling: above this, topology risks chaotic distortion

    // Kinematic/Dynamic Boundaries
    pub holonomy_velocity_max: f64,  // Max allowable delta(||Ω||_F) per processing interval

    // Adaptive Feedback Scalers
    pub mutation_accel_factor: f64,  // Rate multiplier when geometry is too flat
    pub learning_rate_clamp: f64,    // Damping multiplier when geometry is too twisted

    // Immune Safeguards
    pub rollback_enabled: f64,       // Binary flag (1.0 = Active, 0.0 = Bypassed)
    pub quarantine_threshold: f64,   // Critical boundary that triggers immediate node isolation

    // Local invariants (tracked elsewhere in pipeline)
    pub holonomy_norm_local: f64,
    pub commutator_1_5: f64,

    // Cross-lineage drift gains (tiny mutual lean toward Python means)
    pub eta_h_rust: f64,
    pub eta_c_rust: f64,

    // Convenience field used by current main.rs
    pub target_holonomy: f64,
}

impl ContractEnvelope {
    /// Instantiates a pristine constitutional baseline tailored for the 6-band intent mesh
    pub fn default_production_contract() -> Self {
        Self {
            holonomy_min: 0.01000,
            holonomy_max: 0.05000,
            holonomy_velocity_max: 0.02500,
            mutation_accel_factor: 2.00000,
            learning_rate_clamp: 0.25000,
            rollback_enabled: 1.00000,
            quarantine_threshold: 0.12000,

            holonomy_norm_local: 0.0,
            commutator_1_5: 0.0,

            eta_h_rust: 0.0005,
            eta_c_rust: 0.0002,

            target_holonomy: 0.0930,
        }
    }

    /// Evaluates a proposed holonomy metric and its velocity against constitutional limits.
    /// Returns: 0 = OK, 1 = Adjust (Governor), 2 = Veto (Rollback)
    pub fn evaluate_state_compliance(&self, current_h: f64, velocity_h: f64) -> i32 {
        if current_h > self.quarantine_threshold || velocity_h.abs() > self.holonomy_velocity_max {
            return 2; // Immediate Veto & Rollback
        }
        if current_h > self.holonomy_max || current_h < self.holonomy_min {
            return 1; // Governor Correction
        }
        0 // Nominal
    }
}

/// Cross-lineage bias snapshot (fed from bias-matrix sync layer)
pub struct CrossLineageBias {
    pub mean_h_rust: f64,
    pub mean_c_rust: f64,
    pub mean_h_python: f64,
    pub mean_c_python: f64,
}

/// Apply tiny mutual drift toward Python means, with safety clamp
pub fn apply_cross_lineage_drift(env: &mut ContractEnvelope, bias: &CrossLineageBias) {
    let delta_h = bias.mean_h_python - env.holonomy_norm_local;
    let delta_c = bias.mean_c_python - env.commutator_1_5;

    env.holonomy_norm_local += env.eta_h_rust * delta_h;
    env.commutator_1_5 += env.eta_c_rust * delta_c;

    // safety clamp
    env.holonomy_norm_local = env.holonomy_norm_local.clamp(0.0, 0.2);
}
ENDENV