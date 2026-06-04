/*
contract_envelope.rs
The Governing Constitution of the ISST-TOFT Sovereign Substrate.
Defines absolute metric boundaries, velocity caps, and dynamic adjustment factors.
*/

#[derive(Debug, Clone)]
pub struct ContractEnvelope {
    // Absolute Parallel Transport Boundaries
    pub holonomy_min: f64,       // Floor: below this, system is too rigid/symmetric
    pub holonomy_max: f64,       // Ceiling: above this, topology risks chaotic distortion

    // Kinematic/Dynamic Boundaries
    pub holonomy_velocity_max: f64, // Max allowable delta(||Ω||_F) per processing interval

    // Adaptive Feedback Scalers
    pub mutation_accel_factor: f64,  // Rate multiplier when geometry is too flat
    pub learning_rate_clamp: f64,    // Damping multiplier when geometry is too twisted

    // Immune Safeguards
    pub rollback_enabled: f64,       // Binary flag representation (1.0 = Active, 0.0 = Bypassed)
    pub quarantine_threshold: f64,   // Critical boundary that triggers immediate node isolation

    // Local invariants (already tracked elsewhere in your pipeline)
    pub holonomy_norm_local: f64,
    pub commutator_1_5: f64,

    // Cross-lineage drift gains (tiny mutual lean toward Python means)
    pub eta_h_rust: f64,
    pub eta_c_rust: f64,
}

impl ContractEnvelope {
    /// Instantiates a pristine constitutional baseline tailored for the 6-band intent mesh
    pub fn default_production_contract() -> Self {
        Self {
            holonomy_min: 0.01000,          // Triggers exploratory mutation waves
            holonomy_max: 0.05000,          // Triggers immediate protective damping
            holonomy_velocity_max: 0.02500, // Halts integration if state shifts too violently
            mutation_accel_factor: 2.00000, // Doubled adaptation velocity
            learning_rate_clamp: 0.25000,   // Throttled down to a quarter-speed crawl
            rollback_enabled: 1.00000,      // Immune response armed
            quarantine_threshold: 0.12000,  // Nuclear option: immediate core lockdown

            holonomy_norm_local: 0.0,
            commutator_1_5: 0.0,

            // very small mutual drift gains
            eta_h_rust: 0.0005,
            eta_c_rust: 0.0002,
        }
    }

    /// Evaluates a proposed holonomy metric and its velocity against constitutional limits
    /// Returns an action directive code: 0 = OK, 1 = Adjust (Governor), 2 = Veto (Rollback)
    pub fn evaluate_state_compliance(&self, current_h: f64, velocity_h: f64) -> i32 {
        // Condition Red: Velocity or absolute curvature breaches critical survival limits
        if current_h > self.quarantine_threshold || velocity_h.abs() > self.holonomy_velocity_max {
            return 2; // Immediate Veto & Rollback Directive
        }

        // Condition Yellow: System is outside the target Goldilocks Corridor, requiring governor modulation
        if current_h > self.holonomy_max || current_h < self.holonomy_min {
            return 1; // Governor Correction Directive
        }

        0 // Core Matrix Stable (Nominal Corridor)
    }
}

/// Cross-lineage bias snapshot (fed from your bias-matrix sync layer)
pub struct CrossLineageBias {
    pub mean_h_rust: f64,
    pub mean_c_rust: f64,
    pub mean_h_python: f64,
    pub mean_c_python: f64,
}

/// Apply tiny mutual drift toward Python means, with safety clamp
pub fn apply_cross_lineage_drift(env: &mut ContractEnvelope, bias: &CrossLineageBias) {
    let h_other = bias.mean_h_python;
    let c_other = bias.mean_c_python;

    let delta_h = h_other - env.holonomy_norm_local;
    let delta_c = c_other - env.commutator_1_5;

    env.holonomy_norm_local += env.eta_h_rust * delta_h;
    env.commutator_1_5 += env.eta_c_rust * delta_c;

    // safety clamp on Rust-side invariants
    env.holonomy_norm_local = env.holonomy_norm_local.clamp(0.0, 0.2);
}