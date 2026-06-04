cat << 'EOF' > src/intent_engine.rs
//! IntentEngine — Asymmetric Dual-Plane Split Connection Infrastructure Kernel.

use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::time::{SystemTime, UNIX_EPOCH};
use tokio::sync::broadcast;
use tracing::info;

use crate::issttoft::{IntentBand, IntentUpdate, get_band_stiffness, DirectedCoupling, DirectedCurvatureMemory};

#[derive(Clone)]
pub struct IntentEngine {
    intent_tx: broadcast::Sender<IntentUpdate>,
    intent_bands: Arc<Mutex<HashMap<String, IntentBand>>>,
    pub directed_coupling: Arc<Mutex<DirectedCoupling>>,
    pub curvature_memory: Arc<Mutex<DirectedCurvatureMemory>>,
}

impl IntentEngine {
    pub fn new() -> Self {
        let (intent_tx, _) = broadcast::channel(128);
        let engine = Self {
            intent_tx,
            intent_bands: Arc::new(Mutex::new(HashMap::new())),
            directed_coupling: Arc::new(Mutex::new(DirectedCoupling::new())),
            curvature_memory: Arc::new(Mutex::new(DirectedCurvatureMemory::new())),
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
        info!(target: "isst_toft::intent", "Directed coupling planes and memory tracks online.");
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

    pub fn update_from_walker_push(
        &self,
        source_band: usize,
        source_initial: f64,
        first_step_values: &[f64],
        alpha: f64,
    ) {
        if let (Ok(mut dc), Ok(mut cm)) = (self.directed_coupling.lock(), self.curvature_memory.lock()) {
            for target in 0..first_step_values.len() {
                if target == source_band { continue; }
                let observed = first_step_values[target];
                dc.gs_push_update(&mut cm, target, source_band, observed, source_initial, alpha);
            }
        }
    }

    pub fn update_from_ambient_pull(
        &self,
        source_band: usize,
        source_initial: f64,
        first_step_values: &[f64],
        alpha: f64,
    ) {
        if let (Ok(mut dc), Ok(mut cm)) = (self.directed_coupling.lock(), self.curvature_memory.lock()) {
            for target in 0..first_step_values.len() {
                if target == source_band { continue; }
                let observed = first_step_values[target];
                dc.gs_pull_update(&mut cm, target, source_band, observed, source_initial, alpha);
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
