cat << 'EOF' > src/intent_engine.rs
//! IntentEngine — Self-Calibrating Core with Learning Governor and Non-Associative GS Operator.

use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::time::{SystemTime, UNIX_EPOCH};
use tokio::sync::broadcast;
use tracing::info;

use crate::issttoft::{IntentBand, IntentUpdate, HandshakeResponse, get_band_stiffness, CouplingMatrix};
use crate::gs::GsCombiner;

#[derive(Clone)]
pub struct IntentEngine {
    intent_tx: broadcast::Sender<IntentUpdate>,
    intent_bands: Arc<Mutex<HashMap<String, IntentBand>>>,
    pub coupling_matrix: Arc<Mutex<CouplingMatrix>>,
}

impl IntentEngine {
    pub fn new() -> Self {
        let (intent_tx, _) = broadcast::channel(128);
        let engine = Self {
            intent_tx,
            intent_bands: Arc::new(Mutex::new(HashMap::new())),
            coupling_matrix: Arc::new(Mutex::new(CouplingMatrix::new())),
        };
        engine.seed_default_bands();
        engine
    }

    fn seed_default_bands(&self) {
        let now = current_unix_timestamp();
        let seeds = [
            (0, "cERNpiranchor",          1, 0.8742, "pi_r_engine"),
            (1, "warpcorestability",      1, 0.6180, "toroidal_core"),
            (2, "sovereignintentprimary",  2, 0.9510, "safety_monitor"),
            (3, "sovereignintentambient",  0, 0.3820, "lineage"),
            (4, "sensorium_feedback",      0, 0.2360, "telemetry_drift"),
            (5, "mutationplanedriver",     1, 0.7777, "resonance_lattice"),
        ];

        if let Ok(mut bands) = self.intent_bands.lock() {
            for (index, id, mode, value, source) in seeds {
                bands.insert(id.to_string(), IntentBand {
                    band_id: id.to_string(),
                    mode,
                    intent_value: value,
                    base_value: value,
                    last_updated: now,
                    source: source.to_string(),
                    stiffness: get_band_stiffness(index),
                });
            }
        }
        info!(target: "isst_toft::intent", "GS Non-Associative Core and Learning Governor armed.");
    }

    pub fn broadcast_update(&self, update: IntentUpdate) {
        let _ = self.intent_tx.send(update.clone());

        if let Ok(mut bands) = self.intent_bands.lock() {
            if let Some(band) = bands.get_mut(&update.band_id) {
                band.intent_value = update.intent_value;
                band.last_updated = update.timestamp;
            }
        }
    }

    /// Dynamic GS Curvature Tuning Loop with Complete Learning Governor Infrastructure
    pub fn update_c_from_strike(
        &self,
        source_band: usize,
        source_initial: f64,
        first_step_values: &[f64],
        alpha: f64,
    ) {
        if source_initial.abs() < 1e-6 { return; }

        if let Ok(mut matrix) = self.coupling_matrix.lock() {
            for target in 0..first_step_values.len() {
                if target == source_band { continue; }

                let observed = first_step_values[target];
                let c_eff = observed / source_initial;
                let old = matrix.get(target, source_band);

                // 1. Governor: Magnitude Dead-band Gate
                if (c_eff - old).abs() < 0.005 {
                    continue;
                }

                let mut alpha_eff = alpha;

                // 2. Governor: Stability Gating (Dampen step sizes during high-energy saturation shocks)
                let high_energy = source_initial > 0.95;
                if high_energy {
                    alpha_eff *= 0.25; 
                }

                // 3. Governor: Curvature-Aware Gating (Anchor isolation protection)
                if target == 0 {
                    alpha_eff *= 0.10;
                }

                // 4. GS Non-Associative Curvature Operator Step
                let stiffness = get_band_stiffness(target);
                let state = matrix.edge_state_mut(target, source_band);
                let new = GsCombiner::update(old, c_eff, stiffness, alpha_eff, state);

                matrix.set(target, source_band, new);
            }
        }
    }

    pub fn subscribe(&self) -> broadcast::Receiver<IntentUpdate> {
        self.intent_tx.subscribe()
    }
}

fn current_unix_timestamp() -> i64 {
    SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_secs() as i64
}
EOF
