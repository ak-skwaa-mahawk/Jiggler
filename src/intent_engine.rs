cat << 'EOF' > src/intent_engine.rs
//! IntentEngine — Noise-Resistant, Stiffness-Weighted Self-Calibrating Core.

use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::time::{SystemTime, UNIX_EPOCH};
use tokio::sync::broadcast;
use tracing::info;
use crate::issttoft::{IntentBand, IntentUpdate, HandshakeResponse, get_band_stiffness, CouplingMatrix};

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
        info!(target: "isst_toft::intent", "Stiffness-weighted, noise-resistant engine armed.");
    }

    pub fn step_damping_field(&self, dt: f64) {
        let now = current_unix_timestamp();
        let mut updates_to_fire = vec![];

        if let Ok(mut bands) = self.intent_bands.lock() {
            for band in bands.values_mut() {
                if (band.intent_value - band.base_value).abs() > 0.001 {
                    let lambda = 0.4 * (1.0 - band.stiffness);
                    let delta = band.intent_value - band.base_value;
                    
                    band.intent_value -= delta * lambda * dt;
                    band.last_updated = now;

                    updates_to_fire.push(IntentUpdate {
                        band_id: band.band_id.clone(),
                        mode: band.mode,
                        intent_value: band.intent_value,
                        timestamp: now,
                        reason: "ambient_field_relaxation".to_string(),
                    });
                }
            }
        }

        for update in updates_to_fire {
            let _ = self.intent_tx.send(update);
        }
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

    /// Calibrates C using noise-gated boundaries and stiffness-weighted alpha multipliers
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

                // 1. Noise Floor Gate: Filter out micro-adjustments
                if (c_eff - old).abs() < 0.005 {
                    continue;
                }

                // 2. GS Stiffness Adaptive Modulator: High-inertia bands learn slower
                let stiffness = get_band_stiffness(target);
                let alpha_eff = alpha * (1.0 - stiffness);

                // 3. Extrapolate tracking trajectory
                let new = (1.0 - alpha_eff) * old + alpha_eff * c_eff;
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
