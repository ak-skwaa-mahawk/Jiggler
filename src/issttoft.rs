cat << 'EOF' > src/issttoft.rs
/*
issttoft.rs
Foundational Protocol Mapping Structs with Explicit GS Combiner and Curvature Memory.
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

#[derive(Clone, Debug)]
pub struct EdgeCurvature {
    pub k: f64,      // Accumulated curvature memory history
    pub count: u64,  // Total update cycles processed
}

#[derive(Clone)]
pub struct GSCombiner {
    pub curvature: Vec<Vec<EdgeCurvature>>, // [target][source]
    pub alpha_min: f64,
    pub alpha_max: f64,
}

impl GSCombiner {
    pub fn new(n: usize) -> Self {
        let curvature = vec![vec![EdgeCurvature { k: 0.0, count: 0 }; n]; n];
        Self {
            curvature,
            alpha_min: 0.01,
            alpha_max: 0.15,
        }
    }

    /// Explicit non-associative GS operator step with tanh non-linear saturation limiting.
    pub fn combine(
        &mut self,
        target: usize,
        source: usize,
        c_old: f64,
        c_eff: f64,
        stiffness_target: f64,
    ) -> (f64, f64) {
        let edge = &mut self.curvature[target][source];

        // Capture local curvature increment (signed distance delta deviation)
        let delta = c_eff - c_old;
        edge.k += delta;
        edge.count += 1;

        // Governor: Softer learning rates for rigid stiff bands, wider learning paths for loose bands
        let stiffness_gate = 1.0 - stiffness_target.clamp(0.0, 1.0);
        let alpha = (self.alpha_min + stiffness_gate * (self.alpha_max - self.alpha_min))
            .clamp(self.alpha_min, self.alpha_max);

        // Non-associative convergence updates: bias step towards historical trajectory
        let curvature_term = 0.5 * edge.k.tanh();
        let c_new = c_old + alpha * (delta + curvature_term);

        (c_new.clamp(0.0, 1.5), edge.k)
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

        // Seed initial values from verified asymmetric role constraints
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
