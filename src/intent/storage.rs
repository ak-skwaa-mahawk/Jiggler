use super::types::{IntentBandId, IntentBandState, IntentReason, ModeId};
use anyhow::Result;

pub trait IntentStorage: Send + Sync {
    fn load_all_bands(&self) -> Result<Vec<IntentBandState>>;
    fn update_band(&self, band: &IntentBandState) -> Result<()>;
    fn append_event(
        &self,
        ts: i64,
        band: &IntentBandId,
        mode: ModeId,
        delta_i: f64,
        reason: IntentReason,
    ) -> Result<()>;
}

// You will implement this trait using your existing SQLite connection pool
// (tordial_manifold.db). Example skeleton:
//
// impl IntentStorage for SqliteIntentStore { ... }