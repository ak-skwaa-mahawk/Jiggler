cat << 'EOF' > src/issttoft.rs
/*
issttoft.rs
Formal Asymmetric Directed Connection Fields and Geometric Layer Projections.
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
pub struct DirectedCoupling {
    pub push: Vec<Vec<f64>>,
    pub pull: Vec<Vec<f64>>,
}

#[derive(Clone)]
pub struct DirectedCurvatureMemory {
    pub push_mem: Vec<Vec<f64>>,
    pub pull_mem: Vec<Vec<f64>>,
}

impl DirectedCoupling {
    pub fn new() -> Self {
        let mut push = vec![vec![0.10; 6]; 6];
        let mut pull = vec![vec![0.10; 6]; 6];

        for i in 0..6 {
            push[i][i] = 1.0;
            pull[i][i] = 1.0;
        }

        // Seed initial values from verified asymmetric role constraints
        push[0][5] = 0.02;
        push[0][1] = 0.01; push[0][2] = 0.01; push[0][3] = 0.01; push[0][4] = 0.01;
        push[1][0] = 0.80; push[2][0] = 0.80;
        push[1][2] = 0.30; push[2][1] = 0.30;
        push[1][5] = 0.55; push[2][5] = 0.55;
        push[3][1] = 0.40; push[3][2] = 0.40; push[4][1] = 0.40; push[4][2] = 0.40;
        push[3][0] = 0.05; push[4][0] = 0.05;
        push[3][5] = 0.50; push[4][5] = 0.50;
        push[5][1] = 0.30; push[5][2] = 0.30;
        push[5][3] = 0.20; push[5][4] = 0.20;
        push[5][0] = 0.05;

        // Sync baseline pull state to copy seeding properties
        for i in 0..6 {
            for j in 0..6 {
                if i != j {
                    pull[i][j] = push[i][j];
                }
            }
        }

        Self { push, pull }
    }

    pub fn effective(&self, i: usize, j: usize) -> f64 {
        0.8 * self.push[i][j] + 0.2 * self.pull[i][j]
    }

    pub fn gs_push_update(
        &mut self,
        mem: &mut DirectedCurvatureMemory,
        i: usize,
        j: usize,
        observed: f64,
        source_initial: f64,
        alpha: f64,
    ) {
        if source_initial.abs() < 1e-6 { return; }
        let c_eff = observed / source_initial;
        let old = self.push[i][j];
        let delta = c_eff - old;

        // Curvature memory accumulator for push actions
        mem.push_mem[i][j] += delta;

        // f_push Governor rule: Active, high-responsiveness transformation step size
        let governed = old + alpha * (delta + 0.3 * mem.push_mem[i][j].tanh());
        self.push[i][j] = governed.clamp(0.0, 1.5);
    }

    pub fn gs_pull_update(
        &mut self,
        mem: &mut DirectedCurvatureMemory,
        i: usize,
        j: usize,
        observed: f64,
        source_initial: f64,
        alpha: f64,
    ) {
        if source_initial.abs() < 1e-6 { return; }
        let c_eff = observed / source_initial;
        let old = self.pull[i][j];
        let delta = c_eff - old;

        // Curvature memory accumulator for pull actions
        mem.pull_mem[i][j] += delta;

        // f_pull Governor rule: Heavy dampening, highly conservative recovery step size
        let governed = old + (alpha * 0.4) * (delta + 0.1 * mem.pull_mem[i][j].tanh());
        self.pull[i][j] = governed.clamp(0.0, 1.5);
    }
}

impl DirectedCurvatureMemory {
    pub fn new() -> Self {
        Self {
            push_mem: vec![vec![0.0; 6]; 6],
            pull_mem: vec![vec![0.0; 6]; 6],
        }
    }
}
EOF
