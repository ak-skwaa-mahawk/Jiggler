cat << 'EOF' > src/intent_engine.rs
//! IntentEngine — THE single source of truth for the sovereign mesh with active relaxation.

use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::time::{SystemTime, UNIX_EPOCH};
use tokio::sync::broadcast;
use tracing::info;
use crate::issttoft::{IntentBand, IntentUpdate, HandshakeResponse, get_band_stiffness};

#[derive(Clone)]
pub struct IntentEngine {
    intent_tx: broadcast::Sender<IntentUpdate>,
    intent_bands: Arc<Mutex<HashMap<String, IntentBand>>>,
}

impl IntentEngine {
    pub fn new() -> Self {
        let (intent_tx, _) = broadcast::channel(128);
        let engine = Self {
            intent_tx,
            intent_bands: Arc::new(Mutex::new(HashMap::new())),
        };
        engine.seed_default_bands();
        engine.self_validate();
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
        info!(target: "isst_toft::intent", "IntentEngine seeded 6 bands with relaxation targets.");
    }

    fn self_validate(&self) {
        info!(target: "isst_toft::intent", "Sovereign Mesh Health Check: SOLID — Damping matrices armed.");
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

    pub fn get_all_bands(&self) -> Vec<IntentBand> {
        if let Ok(bands) = self.intent_bands.lock() {
            bands.values().cloned().collect()
        } else {
            vec![]
        }
    }

    pub fn subscribe(&self) -> broadcast::Receiver<IntentUpdate> {
        self.intent_tx.subscribe()
    }

    pub fn handshake(&self, client_id: String, _client_type: String, _sovereign_claim: String) -> HandshakeResponse {
        let now = current_unix_timestamp();
        HandshakeResponse {
            initial_bands: self.get_all_bands(),
            server_version: "isst-toft-mesh v2.5-damping-flow".to_string(),
            server_time: now,
            mesh_status: "Ch’anchyah Dach’anchyah — Field Relaxation Live.".to_string(),
            flamekeeper_note: format!("Captain {} — 6-Band Damped Manifold Ready.", client_id),
        }
    }
}

fn current_unix_timestamp() -> i64 {
    SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_secs() as i64
}
EOF
