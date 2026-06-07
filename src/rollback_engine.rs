cat > src/rollback_engine.rs << 'ENDROLL'
/*
 * rollback_engine.rs
 * The Executive Immune Executor with Commutator Tracking Capabilities.
 *
 * Works with the current GSState in intent_engine.rs.
 */

use std::process::Command;
use crate::intent_engine::GSState;

#[derive(Clone, Debug)]
pub struct Snapshot {
    pub push_c: [[f64; 6]; 6],
    pub pull_c: [[f64; 6]; 6],
    pub commutator_channel: [[f64; 6]; 6],
}

pub struct RollbackEngine;

impl RollbackEngine {
    pub fn capture_snapshot(gs: &GSState) -> Snapshot {
        Snapshot {
            push_c: gs.push_c,
            pull_c: gs.pull_c,
            commutator_channel: gs.commutator_channel,
        }
    }

    pub fn execute_restoration(gs: &mut GSState, snapshot: &Snapshot) {
        println!("🔄 [IMMUNE ACTION] Restoring uncorrupted historical snapshot into GSState...");
        gs.push_c = snapshot.push_c;
        gs.pull_c = snapshot.pull_c;
        gs.commutator_channel = snapshot.commutator_channel;
    }

    pub fn commit_rollback_log(violated_h: f64, restored_h: f64, velocity_h: f64) {
        println!("💾 [LEDGER WRITE] Committing sovereign rollback transaction to tordial_gs.db...");
        let query = format!(
            "INSERT INTO runs (timestamp, runtime_env, node_count, final_freq, quarantine_rate, avg_kappa, stability_score, holonomy_norm, holonomy_norm_local) 
             VALUES (datetime('now'), 'Rust_Rollback_Lie', 6, 0.0, 1.0, {:.4}, 0.00, {:.5}, {:.5});",
            velocity_h, violated_h, restored_h
        );
        let _ = Command::new("sqlite3").arg("tordial_gs.db").arg(&query).status();
    }
}
ENDROLL