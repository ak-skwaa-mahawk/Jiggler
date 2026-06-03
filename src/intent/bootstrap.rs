// src/intent/bootstrap.rs

use super::types::{IntentBandId, ModeId};
use anyhow::Result;
use rusqlite::Connection;

/// Seeds the 7 core intent bands on first startup if they don't exist.
/// This is idempotent — safe to call every time the system starts.
pub fn seed_initial_intent_bands(conn: &Connection) -> Result<()> {
    const INITIAL_BANDS: &[&str] = &[
        "safety.checkpoints",
        "lineage.protection",
        "resonance.drive",
        "curvature.stability",
        "energy.governor",
        "fission.control",
        "observer.flame",
    ];

    let mut stmt = conn.prepare(
        r#"
        INSERT OR IGNORE INTO intent_band (id, mode, intent_value, lastupdatets, source)
        VALUES (?1, 0, 0.0, ?2, 'bootstrap')
        "#,
    )?;

    let now = crate::utils::current_time_millis(); // or use your time util

    for band in INITIAL_BANDS {
        stmt.execute(rusqlite::params![band, now])?;
    }

    Ok(())
}