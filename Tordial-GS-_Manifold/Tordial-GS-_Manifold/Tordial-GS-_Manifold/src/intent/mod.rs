// src/intent/mod.rs
//
// Intent Engine — Medium-coupled, auditable intent layer for the sovereign stack.
// Drives bounded evolution of I(t, ω) across task bands with drive / decay / safety terms.
// Works with the existing Tordial-GS manifold and SQLite-backed storage.

pub mod engine;
pub mod storage;
pub mod types;

// Re-export the main public API
pub use engine::IntentEngine;
pub use storage::{IntentStorage, SqliteIntentStore};
pub use types::{
    IntentBandId, IntentBandState, IntentParams, IntentReason, ModeId, SystemMetrics,
};