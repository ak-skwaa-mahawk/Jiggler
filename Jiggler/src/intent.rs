cat > src/intent.rs << 'ENDINTENT'
use rusqlite::{Connection, Result as SqliteResult};
use std::time::Instant;

#[derive(Debug, Clone)]
pub struct IntentParams {
    pub imax_per_mode: f64,
    pub didt_max: f64,
    pub decay_halflife_ms: u64,
}

pub struct SqliteIntentStore {
    pub conn: Connection,
}

impl SqliteIntentStore {
    pub fn new(conn: Connection) -> SqliteResult<Self> {
        conn.execute(
            "CREATE TABLE IF NOT EXISTS intent_bands (
                band_id TEXT PRIMARY KEY,
                mode INTEGER,
                intent_value REAL,
                last_updated INTEGER,
                source TEXT
            )",
            [],
        )?;
        Ok(SqliteIntentStore { conn })
    }
}

pub struct IntentEngine {
    pub store: SqliteIntentStore,
    pub params: IntentParams,
    pub last_update: Instant,
}

impl IntentEngine {
    pub fn new(store: SqliteIntentStore, params: IntentParams) -> Self {
        IntentEngine {
            store,
            params,
            last_update: Instant::now(),
        }
    }

    pub fn inspect_bounds(&self) {
        println!("🔒 IntentEngine Bounds Active");
        println!("   Max Saturation (I_max): {}", self.params.imax_per_mode);
        println!("   Velocity Limit (dI/dt): {}", self.params.didt_max);
    }
}
ENDINTENT