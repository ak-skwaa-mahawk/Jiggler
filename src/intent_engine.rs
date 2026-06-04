cat << 'EOF' > src/intent_engine.rs
//! IntentEngine — Calibrated, Explicitly Governed GS Geometry Substrate Core.

use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::time::{SystemTime, UNIX_EPOCH};
use tokio::sync::broadcast;
use tracing::info;

use crate::issttoft::{IntentBand, IntentUpdate, get_band_stiffness, CouplingMatrix, GSCombiner};

#[derive(Clone)]
pub struct IntentEngine {
    intent_tx: broadcast::Sender<IntentUpdate>,
    intent_bands: Arc<Mutex<HashMap<String, IntentBand>>>,
    pub coupling_matrix: Arc<Mutex<CouplingMatrix>>,
    pub gs_combiner: Arc<Mutex<GSCombiner>>,
}

impl IntentEngine {
    pub fn new() -> Self {
        let (intent_tx, _) = broadcast::channel(128);
        let n = 6;
        let engine = Self {
            intent_tx,
            intent_bands: Arc::new(Mutex::new(HashMap::new())),
            coupling_matrix: Arc::new(Mutex::new(CouplingMatrix::new())),
            gs_combiner: Arc::new(Mutex::new(GSCombiner::new(n))),
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
        info!(target: "isst_toft::intent", "Explicit GS Combiner core architecture online.");
    }

    fn get_stiffness_for_index(&self, idx: usize) -> f64 {
        if let Ok(bands) = self.intent_bands.lock() {
            let id = match idx {
                0 => "cERNpiranchor",
                1 => "warpcorestability",
                2 => "sovereignintentprimary",
                3 => "sovereignintentambient",
                4 => "sensorium_feedback",
                5 => "mutationplanedriver",
                _ => return 0.25,
            };
            if let Some(b) = bands.get(id) {
                return b.stiffness;
            }
        }
        0.25
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

    /// Explicitly updates C-Matrix parameters using the self-contained non-associative combine algorithm
    pub fn update_c_from_strike(
        &self,
        source_band: usize,
        source_initial: f64,
        first_step_values: &[f64],
    ) {
        if source_initial.abs() < 1e-6 { return; }

        if let (Ok(mut matrix), Ok(mut gs)) = (self.coupling_matrix.lock(), self.gs_combiner.lock()) {
            for target in 0..first_step_values.len() {
                if target == source_band { continue; }

                let observed = first_step_values[target];
                let c_eff = observed / source_initial;
                let c_old = matrix.get(target, source_band);

                let stiffness = self.get_stiffness_for_index(target);
                
                // Invoke formal operator execution interface
                let (c_new, k_edge) = gs.combine(target, source_band, c_old, c_eff, stiffness);

                matrix.set(target, source_band, c_new);

                tracing::info!(
                    target: "isst_toft::intent",
                    "GS edge update ({} -> {}): old={:.4}, eff={:.4}, new={:.4}, k={:.4}",
                    source_band, target, c_old, c_eff, c_new, k_edge
                );
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
