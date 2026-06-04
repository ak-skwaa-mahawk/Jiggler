cat << 'EOF' > src/issttoft.rs
/*
issttoft.rs
Active Non-Commutative Dual-Plane GS Operator with Full Lie Commutator Integration.
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

pub fn get_band_stiffness(band_index: usize) -> f64 {
    match band_index {
        0 => 0.01997, 1 => 0.14090, 2 => 0.16130,
        3 => 0.32520, 4 => 0.34620, 5 => 0.24320,
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
    pub commutator_channel: Vec<Vec<f64>>,
    pub n: usize,
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

        // Seed asymmetric infrastructure layout
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
            commutator_channel: vec![vec![0.0; n]; n],
            n,
            omega_min: 0.01000,
            omega_max: 0.05000,
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
                    if i != j && j != k && k != i {
                        let push_l = self.effective(j, i, GSMode::WalkerPush) + self.effective(k, j, GSMode::WalkerPush) + self.effective(i, k, GSMode::WalkerPush);
                        let pull_l = self.effective(j, i, GSMode::AmbientPull) + self.effective(k, j, GSMode::AmbientPull) + self.effective(i, k, GSMode::AmbientPull);
                        sum_sq += (push_l - pull_l).powi(2);
                    }
                }
            }
        }
        sum_sq.sqrt()
    }

    /// Computes the Lie Bracket on the wire: [Push, Pull] = (Push * Pull) - (Pull * Push)
    pub fn update_commutator_channel(&mut self) {
        let mut new_commutator = vec![vec![0.0; self.n]; self.n];
        for i in 0..self.n {
            for j in 0..self.n {
                let mut push_pull_sum = 0.0;
                let mut pull_push_sum = 0.0;
                for k in 0..self.n {
                    push_pull_sum += self.effective(i, k, GSMode::WalkerPush) * self.effective(k, j, GSMode::AmbientPull);
                    pull_push_sum += self.effective(i, k, GSMode::AmbientPull) * self.effective(k, j, GSMode::WalkerPush);
                }
                new_commutator[i][j] = push_pull_sum - pull_push_sum;
            }
        }
        self.commutator_channel = new_commutator;
    }

    pub fn get_governor_scalar(&self) -> f64 {
        let h_norm = self.compute_holonomy_norm();
        if h_norm > self.omega_max { 0.25 } else if h_norm < self.omega_min { 2.00 } else { 1.00 }
    }

    pub fn learn_push(&mut self, source: usize, source_initial: f64, first_step_values: &[f64], alpha: f64) {
        if source_initial.abs() < 1e-6 { return; }
        let governor = self.get_governor_scalar();
        let adjusted_alpha = alpha * governor;

        for target in 0..first_step_values.len() {
            if target == source { continue; }
            let observed = first_step_values[target];
            let c_eff = observed / source_initial;
            let old = self.effective(target, source, GSMode::WalkerPush);
            
            self.memory.push_mem[target][source] += c_eff - old;
            self.planes.push_c[target][source] = ((1.0 - adjusted_alpha) * old + adjusted_alpha * c_eff).clamp(0.0, 1.5);
        }
        self.update_commutator_channel();
    }

    pub fn learn_pull(&mut self, source: usize, source_initial: f64, first_step_values: &[f64], alpha: f64) {
        if source_initial.abs() < 1e-6 { return; }
        let governor = self.get_governor_scalar();
        let adjusted_alpha = (alpha * 0.4) * governor; // Ambient recovery is traditionally damped

        for target in 0..first_step_values.len() {
            if target == source { continue; }
            let observed = first_step_values[target];
            let c_eff = observed / source_initial;
            let old = self.effective(target, source, GSMode::AmbientPull);
            
            self.memory.pull_mem[target][source] += c_eff - old;
            self.planes.pull_c[target][source] = ((1.0 - adjusted_alpha) * old + adjusted_alpha * c_eff).clamp(0.0, 1.5);
        }
        self.update_commutator_channel();
    }
}
EOF
