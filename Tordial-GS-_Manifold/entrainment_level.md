/// Entrainment Level — how fluidly the toroidal field has absorbed chaotic noise ξ(t)
/// into its own coherent rotation instead of carrying raw deviation.
///
/// 0.0 = rigid / still fighting the disturbance (high residual deviation)
/// 1.0 = fully entrained (disturbance has been dissolved into smooth toroidal flow)
pub fn entrainment_level(&self) -> f64 {
    if self.phi.is_empty() {
        return 0.0;
    }

    // Average absolute deviation from the attractor baseline (Φ₀)
    let mean_deviation: f64 = self.phi.iter()
        .map(|p| (p - self.phi0).abs())
        .sum::<f64>() / self.phi.len() as f64;

    // How much noise energy has been processed so far
    let processed_noise = (self.noise_energy + 1e-9).min(4.0);

    // Ratio of remaining raw deviation vs processed disturbance
    let raw_ratio = (mean_deviation / processed_noise).min(1.0);

    // Entrainment = 1 - remaining raw deviation fraction
    (1.0 - raw_ratio * 0.82).clamp(0.08, 0.97)
}