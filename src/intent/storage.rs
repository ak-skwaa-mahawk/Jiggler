use super::types::{IntentBandId, IntentBandState, IntentReason, ModeId};
use anyhow::{Context, Result};
use rusqlite::{params, Connection, OptionalExtension};

/// SQLite-backed implementation of IntentStorage
pub struct SqliteIntentStore {
    conn: Connection,
}

impl SqliteIntentStore {
    /// Create a new store. Pass in your existing connection or open a new one.
    pub fn new(conn: Connection) -> Result<Self> {
        let store = Self { conn };
        store.init_schema()?;
        Ok(store)
    }

    /// Initialize the required tables (idempotent)
    fn init_schema(&self) -> Result<()> {
        self.conn.execute_batch(
            r#"
            CREATE TABLE IF NOT EXISTS intent_band (
                id              TEXT    NOT NULL,
                mode            INTEGER NOT NULL,
                intent_value    REAL    NOT NULL,
                lastupdatets    INTEGER NOT NULL,
                source          TEXT    NOT NULL,
                PRIMARY KEY (id, mode)
            );

            CREATE TABLE IF NOT EXISTS intent_event (
                ts       INTEGER NOT NULL,
                band     TEXT    NOT NULL,
                mode     INTEGER NOT NULL,
                delta_I  REAL    NOT NULL,
                reason   TEXT    NOT NULL,
                meta     TEXT    NOT NULL DEFAULT '{}'
            );

            CREATE INDEX IF NOT EXISTS idx_intent_event_band_mode_ts
                ON intent_event (band, mode, ts);
            "#,
        )?;
        Ok(())
    }
}

impl IntentStorage for SqliteIntentStore {
    fn load_all_bands(&self) -> Result<Vec<IntentBandState>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, mode, intent_value, lastupdatets, source FROM intent_band",
        )?;

        let bands = stmt
            .query_map([], |row| {
                Ok(IntentBandState {
                    band: IntentBandId(row.get(0)?),
                    mode: ModeId(row.get(1)?),
                    intent_value: row.get(2)?,
                    lastupdatets: row.get(3)?,
                    source: row.get(4)?,
                })
            })?
            .collect::<std::result::Result<Vec<_>, _>>()?;

        Ok(bands)
    }

    fn update_band(&self, band: &IntentBandState) -> Result<()> {
        self.conn.execute(
            r#"
            INSERT INTO intent_band (id, mode, intent_value, lastupdatets, source)
            VALUES (?1, ?2, ?3, ?4, ?5)
            ON CONFLICT(id, mode) DO UPDATE SET
                intent_value = excluded.intent_value,
                lastupdatets = excluded.lastupdatets,
                source       = excluded.source
            "#,
            params![
                band.band.0,
                band.mode.0,
                band.intent_value,
                band.lastupdatets,
                band.source
            ],
        )?;
        Ok(())
    }

    fn append_event(
        &self,
        ts: i64,
        band: &IntentBandId,
        mode: ModeId,
        delta_i: f64,
        reason: IntentReason,
    ) -> Result<()> {
        self.conn.execute(
            r#"
            INSERT INTO intent_event (ts, band, mode, delta_I, reason, meta)
            VALUES (?1, ?2, ?3, ?4, ?5, '{}')
            "#,
            params![
                ts,
                band.0,
                mode.0,
                delta_i,
                reason.as_str()
            ],
        )?;
        Ok(())
    }
}