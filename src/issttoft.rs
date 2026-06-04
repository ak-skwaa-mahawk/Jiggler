cat << 'EOF' > src/issttoft.rs
/*
issttoft.rs
Stateful Directed GS Operator Algebra with Adaptive Holonomy Feedback Governors.
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
    pub n: usize,
    // Goldilocks Holonomy Bounds
    pub omega_min: f64,
    pub omega_max: f64,
}

impl GSOperator {
    pub fn new(n: usize) -> Self {
        let mut push_c = vec![vec![0.10; n]; n];
        let mut pull_c = vec![vec![0.10; n]; n];

        for i in 0..n {
            push_c[i][i] = 1.0;
            pull_c[i][i] = 1.0;
        }

        // Seed initial asymmetric base layout configurations
        push_c[1][5] = 0.55; push_c[2][5] = 0.55;
        push_c[1][0] = 0.80; push_c[2][0] = 0.80;

        for i in 0..n {
            for j in 0..n {
                if i != j { pull_c[i][j] = push_c[i][j]; }
            }
        }

        Self {
            planes: GSCouplingPlanes { push_c, pull_c },
            memory: GSCurvatureMemory {
                push_mem: vec![vec![0.0; n]; n],
                pull_mem: vec![vec![0.0; n]; n],
            },
            n,
            omega_min: 0.01000, // Floor: below this, structure is too rigid
            omega_max: 0.04000, // Ceiling: above this, structure is too twisted
        }
    }

    pub fn effective(&self, target: usize, source: usize, mode: GSMode) -> f64 {
        match mode {
            GSMode::WalkerPush => self.planes.push_c[target][source],
            GSMode::AmbientPull => self.planes.pull_c[target][source],
        }
    }

    pub fn compute_holonomy_norm(&self) -> f64 {
        let mut sum_sq = 0.0;
        for i in 0..self.n {
            for j in 0..self.n {
                for k in 0..self.n {
                    if i != j && j != k and k != i {
                        let push_loop = self.planes.push_c[j][i] + self.planes.push_c[k][j] + self.planes.push_c[i][k];
                        let pull_loop = self.planes.pull_c[j][i] + self.planes.pull_c[k][j] + self.planes.pull_c[i][k];
                        sum_sq += (push_loop - pull_loop).powi(2);
                    }
                }
            }
        }
        sum_sq.sqrt()
    }

    /// Dynamically computes an adaptation scalar based on current parallel transport error metrics
    pub fn get_governor_scalar(&self) -> f64 {
        let h_norm = self.compute_holonomy_norm();
        if h_norm > self.omega_max {
            println!("⚠️ [GOVERNOR ALERT] Holonomy Norm ({:.5}) exceeds threshold! Injecting 0.25x damping choke...", h_norm);
            0.25 // Heavy dampening to resist chaotic geometric warp
        } else if h_norm < self.omega_min {
            println!("⚡ [GOVERNOR ALERT] Holonomy Norm ({:.5}) below baseline! Injecting 2.0x mutation acceleration...", h_norm);
            2.00 // Amplify learning rate to shake loose from rigid symmetry
        } else {
            1.00 // Neutral corridor equilibrium
        }
    }

    pub fn learn_push(&mut self, source: usize, source_initial: f64, first_step_values: &[f64], alpha: f64) {
        if source_initial.abs() < 1e-6 { return; }
        
        // Fetch dynamic feedback coefficient before stepping parameters
        let governor = self.get_governor_scalar();
        let adjusted_alpha = alpha * governor;

        for target in 0..first_step_values.len() {
            if target == source { continue; }
            let observed = first_step_values[target];
            let c_eff = observed / source_initial;
            let old = self.planes.push_c[target][source];
            
            self.memory.push_mem[target][source] += c_eff - old;
            self.planes.push_c[target][source] = ((1.0 - adjusted_alpha) * old + adjusted_alpha * c_eff).clamp(0.0, 1.5);
        }
    }

    pub fn learn_pull(&mut self, source: usize, source_initial: f64, first_step_values: &[f64], alpha: f64) {
        if source_initial.abs() < 1e-6 { return; }
        
        let governor = self.get_governor_scalar();
        let adjusted_alpha = (alpha * 0.4) * governor;

        for target in 0..first_step_values.len() {
            if target == source { continue; }
            let observed = first_step_values[target];
            let c_eff = observed / source_initial;
            let old = self.planes.pull_c[target][source];
            
            self.memory.pull_mem[target][source] += c_eff - old;
            self.planes.pull_c[target][source] = ((1.0 - adjusted_alpha) * old + adjusted_alpha * c_eff).clamp(0.0, 1.5);
        }
    }
}
EOF
