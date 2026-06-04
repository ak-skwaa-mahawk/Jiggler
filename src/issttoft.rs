cat << 'EOF' > src/issttoft.rs
/*
issttoft.rs
Foundational Protocol Mapping Structs with Formal Roles and Curvature Invariants.
*/

#[derive(Debug, Clone)]
pub struct IntentBand {
    pub band_id: String,
    pub mode: i32,
    pub intent_value: f64,
    pub base_value: f64,   // ◄── Added to establish relaxation target limits
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

/// Structural Stiffness Matrix Setup (Vector D)
pub fn get_band_stiffness(band_index: usize) -> f64 {
    match band_index {
        0 => 0.95, // Band 0: cERNpiranchor (Highest stiffness — unyielding baseline)
        1 => 0.65, // Band 1: warpcorestability (Moderate stiffness)
        2 => 0.60, // Band 2: sovereignintentprimary (Moderate stiffness)
        3 => 0.20, // Band 3: sovereignintentambient (Low stiffness)
        4 => 0.15, // Band 4: sensorium_feedback (Low stiffness)
        5 => 0.40, // Band 5: mutationplanedriver (Experimental zone)
        _ => 0.50,
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
