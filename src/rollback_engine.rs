cat << 'EOF' > src/rollback_engine.rs
/*
rollback_engine.rs
The Executive Immune Executor of the ISST-TOFT Sovereign Substrate.
Manages deep state snapshotting, rapid memory restorations, and ledger rollback logging.
*/

use std::process::Command;
use crate::issttoft::GSOperator;

#[derive(Clone, Debug)]
pub struct GSOperatorSnapshot {
    pub push_c: Vec<Vec<f64>>,
    pub pull_c: Vec<Vec<f64>>,
    pub push_mem: Vec<Vec<f64>>,
    pub pull_mem: Vec<Vec<f64>>,
}

pub struct RollbackEngine;

impl RollbackEngine {
    /// Captures a flawless, non-destructive deep copy of the active GSOperator matrix lanes
    pub fn capture_snapshot(gs: &GSOperator) -> GSOperatorSnapshot {
        GSOperatorSnapshot {
            push_c: gs.planes.push_c.clone(),
            pull_c: gs.planes.pull_c.clone(),
            push_mem: gs.memory.push_mem.clone(),
            pull_mem: gs.memory.pull_mem.clone(),
        }
    }

    /// Restores a cached, uncorrupted snapshot structure directly into the live execution instance
    pub fn execute_restoration(gs: &mut GSOperator, snapshot: &GSOperatorSnapshot) {
        println!("🔄 [IMMUNE ACTION] Restoring uncorrupted historical snapshot into GSOperator memory...");
        gs.planes.push_c = snapshot.push_c.clone();
        gs.planes.pull_c = snapshot.pull_c.clone();
        gs.memory.push_mem = snapshot.push_mem.clone();
        gs.memory.pull_mem = snapshot.pull_mem.clone();
    }

    /// Logs a sovereign defensive rollback event directly into the shared database ledger
    pub fn commit_rollback_log(violated_h: f64, restored_h: f64, velocity_h: f64) {
        println!("💾 [LEDGER WRITE] Committing sovereign rollback transaction to tordial_gs.db...");
        let query = format!(
            "INSERT INTO runs (timestamp, runtime_env, node_count, final_freq, quarantine_rate, avg_kappa, stability_score, holonomy_norm, holonomy_norm_local) VALUES (datetime('now'), 'Rust_Rollback', 6, 0.0, 1.0, {:.4}, 0.00, {:.5}, {:.5});", 
            velocity_h, violated_h, restored_h
        );

        let status = Command::new("sqlite3")
            .arg("tordial_gs.db")
            .arg(&query)
            .status();

        match status {
            Ok(s) if s.success() => println!("✅ [LEDGER SYNC SUCCESS] Rollback and isolation event logged securely."),
            _ => eprintln!("❌ [LEDGER SYNC FAILURE] Isolation logging track blocked."),
        }
    }
}
EOF
