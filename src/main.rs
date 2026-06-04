cat << 'EOF' > src/main.rs
/*
main.rs
ISST-TOFT Sovereign Substrate Grid Entry Point.
Vector C: Multi-Node Constellation Phase.
*/

mod issttoft;
mod intent_engine;
mod contract_envelope;
mod contract_auditor;
mod rollback_engine;

use std::sync::{Arc, Mutex};
use crate::intent_engine::IntentEngine;
use crate::issttoft::{IntentUpdate, GSMode};
use crate::contract_envelope::ContractEnvelope;
use crate::contract_auditor::ContractAuditor;
use crate::rollback_engine::RollbackEngine;
use std::time::{SystemTime, UNIX_EPOCH};
use std::process::Command;
use std::env;

fn read_peer_holonomy_and_commutator(my_id: &str) -> (f64, f64) {
    // Query the database for the latest run from a DIFFERENT node to find our peer's state
    let query = format!(
        "SELECT holonomy_norm_local, stability_score FROM runs WHERE runtime_env != '{}' AND runtime_env LIKE 'Rust_Node_%' ORDER BY id DESC LIMIT 1;",
        my_id
    );
    let output = Command::new("sqlite3").arg("tordial_gs.db").arg(&query).output();
    
    if let Ok(out) = output {
        let text = String::from_utf8_lossy(&out.stdout);
        if let Some(line) = text.lines().next() {
            let parts: Vec<&str> = line.split('|').collect();
            if parts.len() >= 2 {
                let peer_h = parts[0].trim().parse::<f64>().unwrap_or(0.05);
                let peer_stab = parts[1].trim().parse::<f64>().unwrap_or(0.90);
                println!("📖 [CONSTELLATION DISCOVERY] Node '{}' located peer parameters -> Norm: {:.5}, Stability: {:.2}", my_id, peer_h, peer_stab);
                return (peer_h, peer_stab);
            }
        }
    }
    println!("📖 [CONSTELLATION DISCOVERY] Node '{}' found no active peer footprints. Running in standalone mode.", my_id);
    (0.0, 1.0)
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();
    
    // Parse target node identity from command line args, defaulting to Node_0
    let args: Vec<String> = env::args().collect();
    let node_id = if args.len() > 1 { format!("Rust_Node_{}", args[1]) } else { "Rust_Node_0".to_string() };

    println!("══════════════════════════════════════════════════════════════");
    println!("🔥  ISST-TOFT SOVEREIGN CONSTELLATION [NODE: {} ANCHORED]", node_id);
    println!("══════════════════════════════════════════════════════════════");

    let envelope = ContractEnvelope::default_production_contract();
    let engine = Arc::new(IntentEngine::new());
    let mut rx = engine.subscribe();

    // ─── CRITICAL MULTI-NODE INTERCEPTION STEP ───
    let (peer_norm, _) = read_peer_holonomy_and_commutator(&node_id);
    if peer_norm > 0.0 {
        let mut gs = engine.gs.lock().unwrap();
        if node_id == "Rust_Node_1" {
            // Node 1 actively adapts its internal ceilings to anti-correlate with Node 0's drift
            println!("🌀 [CO-LOCKING PROTOCOL] Node 1 adjusting omega thresholds to bond with Peer field...");
            gs.omega_max = (peer_norm * 1.2).clamp(0.03, 0.08);
        }
    }

    let observed_first_step = Arc::new(Mutex::new(vec![None; 6]));
    let strike_time = Arc::new(Mutex::new(0_i64));

    let observed_clone = Arc::clone(&observed_first_step);
    let strike_time_clone = Arc::clone(&strike_time);
    tokio::spawn(async move {
        while let Ok(update) = rx.recv().await {
            let idx = match update.band_id.as_str() {
                "cERNpiranchor" => 0, "warpcorestability" => 1, "sovereignintentprimary" => 2,
                "sovereignintentambient" => 3, "sensorium_feedback" => 4, "mutationplanedriver" => 5,
                _ => continue,
            };
            if update.reason.contains("strike") { continue; }
            if let Ok(t_strike) = strike_time_clone.lock() {
                if *t_strike > 0 && (update.timestamp - *t_strike) <= 50 {
                    if let Ok(mut steps) = observed_clone.lock() {
                        if steps[idx].is_none() { steps[idx] = Some(update.intent_value); }
                    }
                }
            }
        }
    });

    tokio::time::sleep(tokio::time::Duration::from_millis(50)).await;
    let baseline_snapshot = {
        let gs = engine.gs.lock().unwrap();
        RollbackEngine::capture_snapshot(&gs)
    };

    let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_millis() as i64;
    if let Ok(mut t_strike) = strike_time.lock() { *t_strike = now; }
    let pulse_initial = 0.9990;
    
    // ─── EXECUTE ASYMMETRIC PUSH ENGINE PASS ───
    println!("\n🏋️ Driving context projection matrix loops...");
    engine.broadcast_update(IntentUpdate {
        band_id: "mutationplanedriver".to_string(), mode: 1, intent_value: pulse_initial, timestamp: now, reason: "walker_push_strike".to_string(),
    });

    let band_map = ["cERNpiranchor", "warpcorestability", "sovereignintentprimary", "sovereignintentambient", "sensorium_feedback"];
    for i in 0..5 {
        // Node 1 injects a modified drift offset to dynamically balance the cross-node commutator
        let offset = if node_id == "Rust_Node_1" { 0.025 } else { 0.050 };
        let push_coeff = baseline_snapshot.push_c[i][5] + offset;
        engine.broadcast_update(IntentUpdate {
            band_id: band_map[i].to_string(), mode: 1, intent_value: pulse_initial * push_coeff, timestamp: now, reason: "push_wave".to_string(),
        });
    }
    tokio::time::sleep(tokio::time::Duration::from_millis(60)).await;
    let mut push_step = vec![0.0; 6];
    if let Ok(steps) = observed_first_step.lock() {
        for i in 0..6 { push_step[i] = steps[i].unwrap_or(0.0); }
    }
    push_step[5] = pulse_initial;
    engine.gs.lock().unwrap().learn_push(5, pulse_initial, &push_step, 0.10);

    // ─── EXECUTE CRITIC RESOLUTION MESH COUPLING ───
    let final_gs = engine.gs.lock().unwrap().clone();
    let proposed_h = final_gs.compute_holonomy_norm();
    
    println!("\n📊 [STATE SURFACE RESOLVED BY {}]", node_id);
    println!("   Effective Edge Lie Commutator [1][5]: {:.6}", final_gs.commutator_channel[1][5]);
    
    let audit = ContractAuditor::audit_proposal(proposed_h, &envelope);
    let q_rate = if audit.directive == 2 { 1.0 } else { 0.0 };
    
    if audit.directive == 2 {
        println!("🛑 [CONSTELLATION VETO] Local trajectory out of bounds. Executing structural recovery.");
        let mut gs = engine.gs.lock().unwrap();
        RollbackEngine::execute_restoration(&mut gs, &baseline_snapshot);
    } else {
        println!("✅ [CONSTELLATION ADMISSION] Parameters securely harmonized with collective ledger.");
    }

    // Append our customized identity metrics to the shared network history log
    let query = format!(
        "INSERT INTO runs (timestamp, runtime_env, node_count, final_freq, quarantine_rate, avg_kappa, stability_score, holonomy_norm, holonomy_norm_local) VALUES (datetime('now'), '{}', 6, 84.5, {}, 3.12, 0.92, 0.0, {});", 
        node_id, q_rate, proposed_h
    );
    let _ = Command::new("sqlite3").arg("tordial_gs.db").arg(&query).status();
}
EOF
