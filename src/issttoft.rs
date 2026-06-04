cat << 'EOF' > src/issttoft.rs
/*
issttoft.rs
Formal Primitive Definitions for the Stateful Directed GS Operator Algebra.
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

#[derive(Copy, Clone, Debug, PartialEq)]
pub enum GSMode {
    WalkerPush,
    AmbientPull,
}

#[derive(Clone, Debug)]
pub struct GSCurvatureMemory {
    pub push_mem: Vec<Vec<f64>>,
    pub pull_mem: Vec<Vec<f64>>,
}

#[derive(Clone, Debug)]
pub struct GSCouplingPlanes {
    pub push_c: Vec<Vec<f64>>,
    pub pull_c: Vec<Vec<f64>>,
}

#[derive(Clone, Debug)]
pub struct GSOperator {
    pub planes: GSCouplingPlanes,
    pub memory: GSCurvatureMemory,
}

impl GSOperator {
    pub fn new(n: usize) -> Self {
        let mut push_c = vec![vec![0.10; n]; n];
        let mut pull_c = vec![vec![0.10; n]; n];

        for i in 0..n {
            push_c[i][i] = 1.0;
            pull_c[i][i] = 1.0;
        }

        // Seed initial asymmetric configurations into Walker push tracks
        push_c[0][5] = 0.02;
        push_c[0][1] = 0.01; push_c[0][2] = 0.01; push_c[0][3] = 0.01; push_c[0][4] = 0.01;
        push_c[1][0] = 0.80; push_c[2][0] = 0.80;
        push_c[1][2] = 0.30; push_c[2][1] = 0.30;
        push_c[1][5] = 0.55; push_c[2][5] = 0.55;
        push_c[3][1] = 0.40; push_c[3][2] = 0.40; push_c[4][1] = 0.40; push_c[4][2] = 0.40;
        push_c[3][0] = 0.05; push_c[4][0] = 0.05;
        push_c[3][5] = 0.50; push_c[4][5] = 0.50;
        push_c[5][1] = 0.30; push_c[5][2] = 0.30;
        push_c[5][3] = 0.20; push_c[5][4] = 0.20;
        push_c[5][0] = 0.05;

        // Mirror baseline pull configuration to preserve metric symmetry at initialization
        for i in 0..n {
            for j in 0..n {
                if i != j {
                    pull_c[i][j] = push_c[i][j];
                }
            }
        }

        Self {
            planes: GSCouplingPlanes { push_c, pull_c },
            memory: GSCurvatureMemory {
                push_mem: vec![vec![0.0; n]; n],
                pull_mem: vec![vec![0.0; n]; n],
            },
        }
    }

    pub fn get_push(&self, target: usize, source: usize) -> f64 {
        self.planes.push_c[target][source]
    }

    pub fn get_pull(&self, target: usize, source: usize) -> f64 {
        self.planes.pull_c[target][source]
    }

    pub fn effective(&self, target: usize, source: usize, mode: GSMode) -> f64 {
        match mode {
            GSMode::WalkerPush => self.get_push(target, source),
            GSMode::AmbientPull => self.get_pull(target, source),
        }
    }

    pub fn learn_push(&mut self, source: usize, source_initial: f64, first_step_values: &[f64], alpha: f64) {
        if source_initial.abs() < 1e-6 { return; }

        for target in 0..first_step_values.len() {
            if target == source { continue; }

            let observed = first_step_values[target];
            let c_eff = observed / source_initial;
            let old = self.planes.push_c[target][source];
            let curv = c_eff - old;

            // Save push field tensor updates to the active curvature tracks
            self.memory.push_mem[target][source] += curv;

            // Non-linear, memory-biased transport step integration
            let new = (1.0 - alpha) * old + alpha * c_eff;
            self.planes.push_c[target][source] = new.clamp(0.0, 1.5);
        }
    }

    pub fn learn_pull(&mut self, source: usize, source_initial: f64, first_step_values: &[f64], alpha: f64) {
        if source_initial.abs() < 1e-6 { return; }

        for target in 0..first_step_values.len() {
            if target == source { continue; }

            let observed = first_step_values[target];
            let c_eff = observed / source_initial;
            let old = self.planes.pull_c[target][source];
            let curv = c_eff - old;

            // Save pull field tensor updates to the passive curvature tracks
            self.memory.pull_mem[target][source] += curv;

            // Tempered ambient recovery step integration
            let new = (1.0 - (alpha * 0.4)) * old + (alpha * 0.4) * c_eff;
            self.planes.pull_c[target][source] = new.clamp(0.0, 1.5);
        }
    }
}
EOF
