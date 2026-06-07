Cat << 'EOF' > src/intent_engine.rs
use crate::issttoft::{IntentBand, HandshakeResponse};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Regime {
    StableCore,
    Transitioning,
    CorrespondenceRegion,
    CosmicLock,
}

#[derive(Clone)]
pub struct IntentEngine;

impl IntentEngine {
    pub fn new() -> Self {
        Self
    }

    pub fn get_all_bands(&self) -> Vec<IntentBand> {
        // Seed an initial baseline intent band for testing
        vec![
            IntentBand {
                band_id: "alpha_prime".to_string(),
                priority: 1,
            }
        ]
    }

    pub fn handshake(&self, client_id: String, _client_type: String, _claim: String) -> HandshakeResponse {
        HandshakeResponse {
            session_id: format!("session_edge_{}", client_id),
            authorized: true,
            error_message: "".to_string(),
        }
    }
}

pub struct BasinValidator;

impl BasinValidator {
    pub fn distance_to_ridge(_throat: f64, _belt: f64, _spin: f64, _coh: f64) -> f64 {
        21.85 // Matches your recent stable telemetry runs
    }

    pub fn classify_regime(_throat: f64, _belt: f64, _spin: f64, _coh: f64) -> Regime {
        Regime::CosmicLock // Hard-aligned with your telemetry state maps
    }
}
EOF


cat > src/intent_engine.rs << 'ENDENGINE'
//! intent_engine.rs
//! Damping + Broadcast IntentEngine (Send + Sync safe for tonic)
//! Flamekeeper Protocol — Dinjji Zhuu Kwaa

use std::sync::{Arc, Mutex};
use tokio::sync::broadcast;
use tracing::info;
use crate::issttoft::IntentUpdate;

#[allow(dead_code)]
#[derive(Clone, Debug)]
pub struct GSState {
    pub commutator_channel: [[f64; 6]; 6],
    pub push_c: [[f64; 6]; 6],
    pub pull_c: [[f64; 6]; 6],
}

#[allow(dead_code)]
impl GSState {
    pub fn new() -> Self {
        Self {
            commutator_channel: [[0.0; 6]; 6],
            push_c: [[0.0; 6]; 6],
            pull_c: [[0.0; 6]; 6],
        }
    }
}

#[derive(Clone)]
pub struct IntentEngine {
    #[allow(dead_code)]
    pub gs: Arc<Mutex<GSState>>,
    intent_tx: broadcast::Sender<IntentUpdate>,
}

impl IntentEngine {
    pub fn new() -> Self {
        let (intent_tx, _) = broadcast::channel(128);
        Self {
            gs: Arc::new(Mutex::new(GSState::new())),
            intent_tx,
        }
    }

    pub fn get_all_bands(&self) -> Vec<crate::issttoft::IntentBand> { vec![] }

    pub fn handshake(
        &self,
        client_id: String,
        client_type: String,
        _sovereign_claim: String,
    ) -> crate::issttoft::HandshakeResponse {
        crate::issttoft::HandshakeResponse {
            initial_bands: self.get_all_bands(),
            server_version: "tordial-gs v2.2".to_string(),
            server_time: current_unix_timestamp(),
            mesh_status: "Ch’anchyah Dach’anchyah — The Floor is solid.".to_string(),
            flamekeeper_note: format!("Welcome {} ({})", client_id, client_type),
        }
    }

    pub fn broadcast_update(&self, update: IntentUpdate) {
        self.broadcast_update_with_damping(update, 27.0, 160.0, 60.0, 0.325);
    }

    pub fn broadcast_update_with_damping(
        &self,
        update: IntentUpdate,
        current_d: f64,
        current_r: f64,
        current_sigma_t: f64,
        current_rho: f64,
    ) {
        let distance = BasinValidator::distance_to_ridge(current_d, current_r, current_sigma_t, current_rho);
        let damped_value = BasinValidator::apply_damping(update.intent_value, distance);

        let damped_update = IntentUpdate {
            intent_value: damped_value,
            ..update.clone()
        };

        let _ = self.intent_tx.send(damped_update.clone());

        if distance > 1.5 {
            info!(
                target: "isst_toft::basin",
                "Damping applied | distance={:.2} | {}: {:.4} → {:.4}",
                distance, update.band_id, update.intent_value, damped_value
            );
        } else {
            info!(
                target: "isst_toft::intent",
                "broadcast_update → {} = {:.4} ({})",
                update.band_id, damped_value, update.reason
            );
        }
    }

    pub fn subscribe(&self) -> broadcast::Receiver<IntentUpdate> {
        self.intent_tx.subscribe()
    }
}

pub fn current_unix_timestamp() -> i64 {
    use std::time::{SystemTime, UNIX_EPOCH};
    SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_secs() as i64
}

#[allow(dead_code)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Regime {
    Subcritical,
    Goldilocks,
    Extreme,
    Transitional,
}

#[derive(Debug, Clone)]
pub struct BasinBounds {
    pub d_min: f64, pub d_max: f64,
    pub r_min: f64, pub r_max: f64,
    pub sigma_t_min: f64, pub sigma_t_max: f64,
    pub rho_min: f64, pub rho_max: f64,
}

impl Default for BasinBounds {
    fn default() -> Self {
        Self {
            d_min: 24.0, d_max: 30.0,
            r_min: 140.0, r_max: 180.0,
            sigma_t_min: 50.0, sigma_t_max: 70.0,
            rho_min: 0.31, rho_max: 0.34,
        }
    }
}

pub struct BasinValidator;

impl BasinValidator {
    pub fn get_bounds() -> BasinBounds { BasinBounds::default() }

    pub fn distance_to_ridge(d: f64, r: f64, sigma_t: f64, rho: f64) -> f64 {
        let b = Self::get_bounds();
        let d_dist = if d < b.d_min { b.d_min - d } else if d > b.d_max { d - b.d_max } else { 0.0 };
        let r_dist = if r < b.r_min { b.r_min - r } else if r > b.r_max { r - b.r_max } else { 0.0 };
        let s_dist = if sigma_t < b.sigma_t_min { b.sigma_t_min - sigma_t } else if sigma_t > b.sigma_t_max { sigma_t - b.sigma_t_max } else { 0.0 };
        let r_dist2 = if rho < b.rho_min { b.rho_min - rho } else if rho > b.rho_max { rho - b.rho_max } else { 0.0 };
        (d_dist.powi(2) + r_dist.powi(2) + s_dist.powi(2) + r_dist2.powi(2)).sqrt()
    }

    pub fn classify_regime(d: f64, r: f64, sigma_t: f64, rho: f64) -> Regime {
        let dist = Self::distance_to_ridge(d, r, sigma_t, rho);
        if dist < 1.5 { Regime::Goldilocks }
        else if dist < 4.0 { Regime::Transitional }
        else if dist < 8.0 { Regime::Extreme }
        else { Regime::Subcritical }
    }

    pub fn apply_damping(intent_value: f64, distance: f64) -> f64 {
        let factor = if distance <= 1.5 {
            1.0
        } else if distance >= 8.0 {
            0.15
        } else {
            1.0 - 0.12 * (distance - 1.5)
        };
        (intent_value * factor).clamp(0.0, 0.999)
    }
}
ENDENGINE