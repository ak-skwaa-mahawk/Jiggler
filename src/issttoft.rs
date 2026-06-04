cat << 'EOF' > src/issttoft.rs
/*
issttoft.rs
Foundational Protocol Mapping Structs with Live Mutable Coupling Matrices.
*/

#[derive(Debug, Clone)]
pub struct IntentBand {
    pub band_id: String,
    pub mode: i32,
    pub intent_value: f64,
    pub base_value: f64,
    pub last_updated: i64,
    pub source: String,
    pub stiffness: f64,
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

pub fn get_band_stiffness(band_index: usize) -> f64 {
    match band_index {
        0 => 0.01997, // cERNpiranchor
        1 => 0.14090, // warpcorestability
        2 => 0.16130, // sovereignintentprimary
        3 => 0.32520, // sovereignintentambient
        4 => 0.34620, // sensorium_feedback
        5 => 0.24320, // mutationplanedriver
        _ => 0.25000,
    }
}

#[derive(Clone)]
pub struct CouplingMatrix {
    pub c: Vec<Vec<f64>>,
}

impl CouplingMatrix {
    pub fn new() -> Self {
        let mut c = vec![vec![0.10; 6]; 6];
        for i in 0..6 {
            c[i][i] = 1.0;
        }
        
        // Seed initial values from our verified asymmetric role constraints
        c[0][5] = 0.02;
        c[0][1] = 0.01; c[0][2] = 0.01; c[0][3] = 0.01; c[0][4] = 0.01;
        c[1][0] = 0.80; c[2][0] = 0.80;
        c[1][2] = 0.30; c[2][1] = 0.30;
        c[1][5] = 0.55; c[2][5] = 0.55;
        c[3][1] = 0.40; c[3][2] = 0.40; c[4][1] = 0.40; c[4][2] = 0.40;
        c[3][0] = 0.05; c[4][0] = 0.05;
        c[3][5] = 0.50; c[4][5] = 0.50;
        c[5][1] = 0.30; c[5][2] = 0.30;
        c[5][3] = 0.20; c[5][4] = 0.20;
        c[5][0] = 0.05;

        Self { c }
    }

    pub fn get(&self, target: usize, source: usize) -> f64 {
        self.c[target][source]
    }

    pub fn set(&mut self, target: usize, source: usize, value: f64) {
        self.c[target][source] = value;
    }
}
EOF
