// ============================================================
// BasinValidator + Distance-to-Ridge Damping
// Sovereign Attractor Basin Enforcement for Tordial-GS
// ============================================================

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Regime {
    Subcritical,
    Goldilocks,
    Extreme,
    Transitional,
}

#[derive(Debug, Clone)]
pub struct BasinBounds {
    pub d_min: f64,
    pub d_max: f64,
    pub r_min: f64,
    pub r_max: f64,
    pub sigma_t_min: f64,
    pub sigma_t_max: f64,
    pub rho_min: f64,
    pub rho_max: f64,
}

impl Default for BasinBounds {
    fn default() -> Self {
        Self {
            d_min: 24.0,
            d_max: 30.0,
            r_min: 140.0,
            r_max: 180.0,
            sigma_t_min: 50.0,
            sigma_t_max: 70.0,
            rho_min: 0.31,
            rho_max: 0.34,
        }
    }
}

pub struct BasinValidator;

impl BasinValidator {
    pub fn get_bounds() -> BasinBounds {
        BasinBounds::default()
    }

    /// Returns true if current state is inside the attractor basin
    pub fn is_inside_basin(d: f64, r: f64, sigma_t: f64, rho: f64) -> bool {
        let b = Self::get_bounds();
        d >= b.d_min && d <= b.d_max &&
        r >= b.r_min && r <= b.r_max &&
        sigma_t >= b.sigma_t_min && sigma_t <= b.sigma_t_max &&
        rho >= b.rho_min && rho <= b.rho_max
    }

    pub fn classify_regime(d: f64, r: f64, sigma_t: f64, rho: f64) -> Regime {
        let b = Self::get_bounds();

        if d < b.d_min || d >= b.d_max || r < b.r_min || r > b.r_max {
            return Regime::Subcritical;
        }

        if sigma_t < b.sigma_t_min || rho < b.rho_min {
            return Regime::Subcritical;
        }

        if sigma_t > b.sigma_t_max || rho > b.rho_max {
            return Regime::Extreme;
        }

        if sigma_t >= 55.0 && sigma_t <= 65.0 && rho >= 0.315 && rho <= 0.335 {
            return Regime::Goldilocks;
        }

        Regime::Transitional
    }

    /// Euclidean distance to the attractor ridge in (d, r, σₜ, ρ) space
    pub fn distance_to_ridge(d: f64, r: f64, sigma_t: f64, rho: f64) -> f64 {
        let b = Self::get_bounds();

        let d_dist = if d < b.d_min { b.d_min - d } else if d > b.d_max { d - b.d_max } else { 0.0 };
        let r_dist = if r < b.r_min { b.r_min - r } else if r > b.r_max { r - b.r_max } else { 0.0 };
        let sigma_dist = if sigma_t < b.sigma_t_min { b.sigma_t_min - sigma_t }
                         else if sigma_t > b.sigma_t_max { sigma_t - b.sigma_t_max } else { 0.0 };
        let rho_dist = if rho < b.rho_min { b.rho_min - rho }
                       else if rho > b.rho_max { rho - b.rho_max } else { 0.0 };

        (d_dist.powi(2) + r_dist.powi(2) + sigma_dist.powi(2) + rho_dist.powi(2)).sqrt()
    }

    /// Distance-to-ridge damping factor
    /// - distance ≤ 1.5 → full strength (1.0)
    /// - distance > 8.0 → strong damping (0.15)
    /// - Smooth roll-off in between
    pub fn compute_damping_factor(distance: f64) -> f64 {
        if distance <= 1.5 {
            1.0
        } else if distance >= 8.0 {
            0.15
        } else {
            1.0 - 0.12 * (distance - 1.5)
        }
    }

    /// Applies damping to an intent value based on distance from ridge
    pub fn apply_damping(intent_value: f64, distance: f64) -> f64 {
        let factor = Self::compute_damping_factor(distance);
        (intent_value * factor).clamp(0.0, 0.999)
    }
}
/// Broadcasts an update and applies basin-aware damping if drifting from ridge
pub fn broadcast_update_with_basin_check(
    &self,
    update: IntentUpdate,
    current_d: f64,
    current_r: f64,
    current_sigma_t: f64,
    current_rho: f64,
) {
    let distance = BasinValidator::distance_to_ridge(
        current_d, current_r, current_sigma_t, current_rho
    );

    let damped_value = BasinValidator::apply_damping(update.intent_value, distance);

    let damped_update = IntentUpdate {
        intent_value: damped_value,
        ..update
    };

    self.broadcast_update(damped_update);

    if distance > 4.0 {
        tracing::warn!(
            target: "isst_toft::basin",
            "Drifting from attractor ridge | distance={:.2} | damping applied",
            distance
        );
    }
}
let distance = BasinValidator::distance_to_ridge(27.5, 155.0, 62.0, 0.325);
let damping = BasinValidator::compute_damping_factor(distance);
let corrected = BasinValidator::apply_damping(0.87, distance);

println!("Distance to ridge: {:.2}", distance);
println!("Damping factor: {:.3}", damping);
println!("Corrected intent: {:.4}", corrected);