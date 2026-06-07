/// pi_r_engine.rs
/// High-Performance Numerical Core for the Tordial-GS Substrate.
/// Implements stabilized parameter scaling, high-stress fission triggers, and assertive energy governing.

use std::collections::HashMap;

// Global Governor Invariants
pub const MIN_ENERGY_FLOOR: f64 = 50.0;
pub const MAX_ENERGY_CAP: f64 = 500.0;

#[derive(Debug, Clone)]
pub struct TordialAgentNode {
    pub node_id: String,
    pub config: HashMap<String, String>,
    pub curvature_pressure: f64,
    pub energy: f64,
}

#[derive(Debug, Clone)]
pub struct OpenTordialAgentNode {
    pub base: TordialAgentNode,
    pub sigma_t: f64,
}

impl OpenTordialAgentNode {
    pub fn new(node_id: &str, config: HashMap<String, String>) -> Self {
        Self {
            base: TordialAgentNode {
                node_id: node_id.to_string(),
                config,
                curvature_pressure: 0.0,
                energy: 100.0,
            },
            sigma_t: 1.0, // Non-zero initialization parameter
        }
    }

    /// Updates internal geometry states and tracks regime transitions
    pub fn compute_and_update_gs(&mut self, manifold_state: &HashMap<String, f64>) -> &'static str {
        let pressure = manifold_state.get("curvature_pressure").cloned().unwrap_or(0.3);
        self.base.curvature_pressure = pressure;

        // Synchronized scaling: Compute a meaningful, growing sigma_T based on manifold tension
        self.sigma_t = pressure * 220.0;

        // === FISSION TRIGGER (High Positive Stress Check) ===
        if self.sigma_t > 180.0 {
            self.trigger_fission();
        }

        // === GS Regime Threshold Verification ===
        if pressure > 0.85 {
            "DEEP_GS"
        } else if pressure > 0.6 {
            "GOLDILOCKS"
        } else if pressure > 0.35 {
            "MARGINAL"
        } else {
            "SUBCRITICAL"
        }
    }

    fn trigger_fission(&self) {
        println!(
            "   🧬 [FISSION EVENT] Node {} fissioning — sigma_T={:.2f}",
            self.base.node_id, self.sigma_t
        );
    }
}

/// Assertive Global Energy Governor
/// Dynamically calculates system resource spend, preventing unchecked cluster inflation.
pub fn update_global_energy(global_energy: f64, avg_kappa: f64, node_count: usize) -> f64 {
    // Assertive decay: Breakeven point pinned to ~15 active elements
    let energy_delta = 12.0 + (0.8 * avg_kappa) - (node_count as f64 * 0.8);

    let mut new_energy = global_energy + energy_delta;
    
    // Enforce strict bounding constraints
    if new_energy < MIN_ENERGY_FLOOR {
        new_energy = MIN_ENERGY_FLOOR;
    } else if new_energy > MAX_ENERGY_CAP {
        new_energy = MAX_ENERGY_CAP;
    }

    // Trigger alert telemetry if the energy floor blocks system mutation capabilities
    if new_energy <= MIN_ENERGY_FLOOR && global_energy > MIN_ENERGY_FLOOR {
        println!(
            "⚠️  [GOVERNOR] Energy floor hit — spawn suppressed (nodes={})",
            node_count
        );
    }

    new_energy
}

fn main() {
    println!("[+] Instantiating Rust Substrate Reference Environment...");
    
    let mut global_energy = 150.0;
    let mut nodes: Vec<OpenTordialAgentNode> = (0..5)
        .map(|i| OpenTordialAgentNode::new(&format!("node_{}", i), HashMap::new()))
        .collect();

    // Run a bounded simulation loop to watch the governor clamp down
    for tick in 1..=15 {
        println!("\n--- Tick {} ---", tick);
        
        let node_count = nodes.len();
        let simulated_pressure = 0.4 + (node_count as f64 * 0.04);
        let avg_kappa = 0.12 * node_count as f64;

        // Update Governor
        global_energy = update_global_energy(global_energy, avg_kappa, node_count);
        println!(
            "  [METRICS] Global Energy: {:.1f} | Active Nodes: {} | Pressure: {:.2f}",
            global_energy, node_count, simulated_pressure
        );

        // Step Node Lifecycles
        let mut state_map = HashMap::new();
        state_map.insert("curvature_pressure".to_string(), simulated_pressure);
        
        for node in nodes.iter_mut() {
            let _regime = node.compute_and_update_gs(&state_map);
        }

        // Spawn Gating Evaluation
        if global_energy > MIN_ENERGY_FLOOR {
            let next_id = format!("node_{}", rand::random::<u16>() % 900 + 100);
            nodes.push(OpenTordialAgentNode::new(&next_id, HashMap::new()));
            println!("  [SPAWNER] Instantiated node {} successfully.", next_id);
        } else {
            println!("  [SPAWNER] Injection BLOCKED by Energy Governor.");
        }
    }
}
