cat << 'EOF' > src/issttoft.rs
/*
issttoft.rs
Foundational Protocol Mapping Structs with Calibrated Curve Invariants.
*/

#[derive(Debug, Clone)]
pub struct IntentBand {
    pub band_id: String,
    pub mode: i32,
    pub intent_value: f64,
    pub base_value: f64,
    pub last_updated: i64,
    pub source: String,
    pub stiffness: f64,    // D vector component
}

#[derive(Debug, Clone)]
pub struct IntentUpdate {
    pub band_id: String,
    pub mode: i32,
    pub intent_value: f64,
    pub timestamp: i64,
    pub reason: String,
}

#[derive(Debug, Clone)]
pub struct HandshakeResponse {
    pub initial_bands: Vec<IntentBand>,
    pub server_version: String,
    pub server_time: i64,
    pub mesh_status: String,
    pub flamekeeper_note: String,
}

/// Calibrated Stiffness Matrix Setup (Vector D)
/// Derived empirically from linearized log relaxation times: D_i = 1 / tau_i
pub fn get_band_stiffness(band_index: usize) -> f64 {
    match band_index {
        0 => 0.01997, // Band 0: cERNpiranchor (tau = 50.0468s)
        1 => 0.14090, // Band 1: warpcorestability (tau = 7.0950s)
        2 => 0.16130, // Band 2: sovereignintentprimary (tau = 6.1970s)
        3 => 0.32520, // Band 3: sovereignintentambient (tau = 3.0756s)
        4 => 0.34620, // Band 4: sensorium_feedback (tau = 2.8884s)
        5 => 0.24320, // Band 5: mutationplanedriver (tau = 4.1105s)
        _ => 0.25000, // Balanced fallback default baseline
    }
}

/// Coupling Matrix Layout (Array C)
pub fn get_coupling_coefficient(target: usize, source: usize) -> f64 {
    if target == source { return 1.0; }
    match (target, source) {
        (0, _) => 0.02,
        (1, 0) => 0.85,
        (2, 0) => 0.80,
        (3, 1) => 0.70,
        (4, 2) => 0.75,
        (3, 4) => 0.30,
        (4, 3) => 0.30,
        (5, 1) => 0.55,
        (5, 2) => 0.55,
        _ => 0.10,
    }
}
EOF
