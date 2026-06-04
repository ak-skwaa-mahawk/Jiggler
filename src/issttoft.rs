cat << 'EOF' > src/issttoft.rs
/*
issttoft.rs
Foundational Protocol Mapping Structs with Dual-Plane Directed Edge Memories.
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

#[derive(Copy, Clone, Debug)]
pub enum EdgeRole {
    WalkerPush,   // Core/Walker driven activation energy wave
    AmbientPull,  // Sub-critical field balancing and context pull
}

#[derive(Clone, Debug)]
pub struct EdgeMemory {
    pub coeff: f64,
    pub curvature: f64,
}

#[derive(Clone)]
pub struct CouplingMatrix {
    pub push: Vec<Vec<EdgeMemory>>, // Walker-driven propagation planes j -> i
    pub pull: Vec<Vec<EdgeMemory>>, // Ambient-driven reprojection planes j -> i
}

impl CouplingMatrix {
    pub fn new() -> Self {
        let mut push = vec![vec![EdgeMemory { coeff: 0.10, curvature: 0.0 }; 6]; 6];
        let mut pull = vec![vec![EdgeMemory { coeff: 0.10, curvature: 0.0 }; 6]; 6];

        for i in 0..6 {
            push[i][i].coeff = 1.0;
            pull[i][i].coeff = 1.0;
        }

        // Seed initial asymmetric role constraints into PUSH side (Walker-driven)
        push[0][5].coeff = 0.02;
        push[0][1].coeff = 0.01; push[0][2].coeff = 0.01; push[0][3].coeff = 0.01; push[0][4].coeff = 0.01;
        push[1][0].coeff = 0.80; push[2][0].coeff = 0.80;
        push[1][2].coeff = 0.30; push[2][1].coeff = 0.30;
        push[1][5].coeff = 0.55; push[2][5].coeff = 0.55;
        push[3][1].coeff = 0.40; push[3][2].coeff = 0.40; push[4][1].coeff = 0.40; push[4][2].coeff = 0.40;
        push[3][0].coeff = 0.05; push[4][0].coeff = 0.05;
        push[3][5].coeff = 0.50; push[4][5].coeff = 0.50;
        push[5][1].coeff = 0.30; push[5][2].coeff = 0.30;
        push[5][3].coeff = 0.20; push[5][4].coeff = 0.20;
        push[5][0].coeff = 0.05;

        // Pull plane acts initially as a balanced mirror baseline configuration
        for i in 0..6 {
            for j in 0..6 {
                if i != j {
                    pull[i][j].coeff = push[i][j].coeff;
                }
            }
        }

        Self { push, pull }
    }

    pub fn get_push(&self, target: usize, source: usize) -> f64 {
        self.push[target][source].coeff
    }

    pub fn get_pull(&self, target: usize, source: usize) -> f64 {
        self.pull[target][source].coeff
    }

    /// Computes the effective operational topology projection
    pub fn effective(&self, target: usize, source: usize) -> f64 {
        let cp = self.push[target][source].coeff;
        let ca = self.pull[target][source].coeff;
        0.8 * cp + 0.2 * ca
    }

    /// Core Non-Commutative GS Curvature Operator update rule with directional hysteresis cross-bleed
    pub fn gs_update_edge(
        &mut self,
        target: usize,
        source: usize,
        observed: f64,
        source_initial: f64,
        alpha: f64,
        role: EdgeRole,
    ) {
        if source_initial.abs() < 1e-6 { return; }

        let c_eff = observed / source_initial;

        let (edge, gamma, k_bleed) = match role {
            EdgeRole::WalkerPush => {
                let edge = &mut self.push[target][source];
                (edge, 0.08, 0.01) // Decisive modification window, small feedback bleed
            }
            EdgeRole::AmbientPull => {
                let edge = &mut self.pull[target][source];
                (edge, 0.03, 0.00) // Highly tempered adaptation window, zero baseline leak
            }
        };

        let delta = c_eff - edge.coeff;

        // Accumulate signed curvature parameters over non-associative trajectories
        edge.curvature += alpha * delta;

        // Non-commutative governor step modifications
        edge.coeff += gamma * edge.curvature;
        edge.coeff = edge.coeff.clamp(0.0, 1.5);

        // Hysteresis step injection: transfer structural alignment into opposite track memory
        if let EdgeRole::WalkerPush = role {
            let back = &mut self.pull[source][target];
            back.curvature += k_bleed * delta;
        }
    }
}
EOF
