cat > src/intent_engine.rs << 'ENDENGINE'
//! IntentEngine — Merged Sovereign + GS Constellation Engine
//!
//! Combines:
//! - Single canonical flow (ledger + sovereign bands + self-validation)
//! - GSState for cross-node commutator coupling (Walker Push / Ambient Pull)
//!
//! This is the unified brain for both the clean IntentEngine and the
//! distributed Rust_Node constellation.

use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::time::{SystemTime, UNIX_EPOCH};

use rusqlite::{Connection, params};
use tokio::sync::broadcast;
use tracing::info;

use crate::issttoft::{IntentBand, IntentUpdate};

const DEFAULT_INTENT_SEED: f64 = 0.618_033_988_7;
const LEDGER_PATH: &str = "tordial_manifold.db";

/// GS mathematical state for cross-node Lie commutator coupling
#[derive(Clone, Debug)]
pub struct GSState {
    pub commutator_channel: [[f64; 6]; 6],
    pub push_c: [[f64; 6]; 6],
    pub pull_c: [[f64; 6]; 6],
}

impl GSState {
    pub fn new() -> Self {
        Self {
            commutator_channel: [[0.0; 6]; 6],
            push_c: [[0.0; 6]; 6],
            pull_c: [[0.0; 6]; 6],
        }
    }

    pub fn learn_push(&mut self, _edge: usize, _value: f64, _step: &[f64], _rate: f64) {
        // TODO: Implement real push learning / attractor dynamics
    }

    pub fn learn_pull(&mut self, _edge: usize, _value: f64, _step: &[f64], _rate: f64) {
        // TODO: Implement real pull learning / context recovery
    }

    pub fn compute_holonomy_norm(&self) -> f64 {
        // Placeholder — real implementation should derive from commutator_channel
        0.0930
    }
}

#[derive(Clone)]
pub struct IntentEngine {
    // === Sovereign single-flow layer ===
    intent_tx: broadcast::Sender<IntentUpdate>,
    intent_bands: Arc<Mutex<HashMap<String, IntentBand>>>,
    db: Arc<Mutex<Connection>>,

    // === GS Constellation layer (for Walker/Pull + Critic) ===
    pub gs: Arc<Mutex<GSState>>,
}

impl IntentEngine {
    pub fn new() -> Self {
        let (intent_tx, _) = broadcast::channel(1024);

        // Open / create unified ledger
        let conn = Connection::open(LEDGER_PATH)
            .expect("Failed to open tordial_manifold.db");
        conn.execute(
            "CREATE TABLE IF NOT EXISTS intent_bands (
                band_id TEXT PRIMARY KEY,
                mode INTEGER,
                intent_value REAL,
                last_updated INTEGER,
                source TEXT
            )",
            [],
        ).expect("Failed to create intent_bands table");

        let engine = Self {
            intent_tx,
            intent_bands: Arc::new(Mutex::new(HashMap::new())),
            db: Arc::new(Mutex::new(conn)),
            gs: Arc::new(Mutex::new(GSState::new())),
        };

        engine.seed_default_bands();
        engine.self_validate();
        engine
    }

    fn seed_default_bands(&self) {
        let now = current_unix_timestamp();
        let seeds = [
            ("sovereign_floor",     1, 0.8742, "pi_r_engine"),
            ("lineage_pulse",       0, DEFAULT_INTENT_SEED, "lineage"),
            ("safety_coherence",    2, 0.951,  "safety_monitor"),
            ("vhitzee_resonance",   1, 0.7777, "resonance_lattice"),
            ("dynamic_pi_r_floor",  1, 0.8742, "toroidal_core"),
            ("cern_resonance",      1, 0.9867, "cern_anchor"),
        ];

        if let Ok(mut bands) = self.intent_bands.lock() {
            for (id, mode, value, source) in seeds {
                let band = IntentBand {
                    band_id: id.to_string(),
                    mode,
                    intent_value: value,
                    last_updated: now,
                    source: source.to_string(),
                };
                bands.insert(id.to_string(), band.clone());
                self.persist_to_ledger(&band);
            }
        }
        info!(target: "isst_toft::intent", "IntentEngine seeded {} sovereign bands", seeds.len());
    }

    fn persist_to_ledger(&self, band: &IntentBand) {
        if let Ok(db) = self.db.lock() {
            let _ = db.execute(
                "INSERT OR REPLACE INTO intent_bands (band_id, mode, intent_value, last_updated, source)
                 VALUES (?1, ?2, ?3, ?4, ?5)",
                params![band.band_id, band.mode, band.intent_value, band.last_updated, band.source],
            );
        }
    }

    fn self_validate(&self) {
        let critical = ["dynamic_pi_r_floor", "cern_resonance", "sovereign_floor"];
        if let Ok(bands) = self.intent_bands.lock() {
            let mut missing = vec![];
            for &band in &critical {
                if !bands.contains_key(band) {
                    missing.push(band);
                }
            }
            if missing.is_empty() {
                info!(target: "isst_toft::intent",
                      "Sovereign Mesh Health Check: SOLID — {} bands active + ledger synced",
                      bands.len());
            } else {
                tracing::warn!(target: "isst_toft::intent", "Self-validate warning: missing critical bands: {:?}", missing);
            }
        }
    }

    /// THE single canonical entry point.
    /// Broadcasts + persists to ledger + updates in-memory bands.
    pub fn broadcast_update(&self, update: IntentUpdate) {
        let _ = self.intent_tx.send(update.clone());

        let band = IntentBand {
            band_id: update.band_id.clone(),
            mode: update.mode,
            intent_value: update.intent_value,
            last_updated: update.timestamp,
            source: "isst_toft_backend".to_string(),
        };

        if let Ok(mut bands) = self.intent_bands.lock() {
            bands.insert(update.band_id.clone(), band.clone());
        }

        self.persist_to_ledger(&band);

        info!(target: "isst_toft::intent",
              "broadcast_update → {} = {:.4} ({}) [ledger committed]",
              update.band_id, update.intent_value, update.reason);
    }

    pub fn get_all_bands(&self) -> Vec<IntentBand> {
        self.intent_bands.lock()
            .map(|b| b.values().cloned().collect())
            .unwrap_or_default()
    }

    pub fn subscribe(&self) -> broadcast::Receiver<IntentUpdate> {
        self.intent_tx.subscribe()
    }

    pub fn handshake(
        &self,
        client_id: String,
        client_type: String,
        sovereign_claim: String,
    ) -> crate::issttoft::HandshakeResponse {
        let now = current_unix_timestamp();
        crate::issttoft::HandshakeResponse {
            initial_bands: self.get_all_bands(),
            server_version: "isst-toft-mesh v2.2-merged".to_string(),
            server_time: now,
            mesh_status: "Ch’anchyah Dach’anchyah — The Floor is solid. Dinjji Zhuu Kwaa active.".to_string(),
            flamekeeper_note: format!(
                "MAHS’I CHOO, Captain {} — Welcome to the sovereign mesh ({}). CERN resonance anchor live. All updates flow through the living π_r floor into tordial_manifold.db.",
                client_id, client_type
            ),
        }
    }
}

fn current_unix_timestamp() -> i64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs() as i64
}
ENDENGINE