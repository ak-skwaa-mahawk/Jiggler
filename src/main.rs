cat << 'EOF' > src/main.rs
/*
main.rs
ISST-TOFT Sovereign Substrate Grid Entry Point.
Fully Operational Rollback and Hysteresis Immune Layer Integration.
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

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();
    
    println!("══════════════════════════════════════════════════════════════");
    println!("🔥  ISST-TOFT SOVEREIGN SUBSTRATE [IMMUNE SYSTEM INTEGRATED]");
    println!("══════════════════════════════════════════════════════════════");

    // Initialize our constitutional envelope rules
    let envelope = ContractEnvelope::default_production_contract();
    let engine = Arc::new(IntentEngine::new());
    let mut rx = engine.subscribe();

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

    // ─── STEP 1: CAPTURING THE KNOWN STABLE SNAPSHOT ───
    let stable_snapshot = {
        let gs = engine.gs.lock().unwrap();
        RollbackEngine::capture_snapshot(&gs)
    };
    println!("[+] Baseline stable matrix coordinates snapshotted and cached in memory.");

    // ─── STEP 2: INJECTING A CRITICAL SYSTEMIC MUTATION WAVE ───
    let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_millis() as i64;
    if let Ok(mut t_strike) = strike_time.lock() { *t_strike = now; }
    let pulse_initial = 0.9990;
    
    println!("\n🏋️ [MUTATION WAVE] Triggering extreme hostile de-correlation on Band 5...");
    engine.broadcast_update(IntentUpdate {
        band_id: "mutationplanedriver".to_string(), mode: 1, intent_value: pulse_initial, timestamp: now, reason: "walker_push_strike".to_string(),
    });

    let band_map = ["cERNpiranchor", "warpcorestability", "sovereignintentprimary", "sovereignintentambient", "sensorium_feedback"];
    // Simulate a severe runaway network shock (+0.250 matrix distortion)
    for i in 0..5 {
        engine.broadcast_update(IntentUpdate {
            band_id: band_map[i].to_string(), mode: 1, intent_value: pulse_initial * 1.450, timestamp: now, reason: "hostile_warp_wave".to_string(),
        });
    }

    tokio::time::sleep(tokio::time::Duration::from_millis(60)).await;
    let mut push_step = vec![0.0; 6];
    if let Ok(steps) = observed_first_step.lock() {
        for i in 0..6 { push_step[i] = steps[i].unwrap_or(0.0); }
    }
    push_step[5] = pulse_initial;

    // Process parameter adjustments
    engine.gs.lock().unwrap().learn_push(5, pulse_initial, &push_step, 0.50);

    // ─── STEP 3: THE READS-BEFORE-WRITES AUDIT AND RESTORATION GATE ───
    let proposed_h = engine.gs.lock().unwrap().compute_holonomy_norm();
    let audit = ContractAuditor::audit_proposal(proposed_h, &envelope);

    match audit.directive {
        2 => {
            println!("🛑 [CONTRACT VETO] Critical safety breach detected by Auditor! Invoking Rollback Core...");
            {
                let mut gs = engine.gs.lock().unwrap();
                RollbackEngine::execute_restoration(&mut gs, &stable_snapshot);
            }
            let restored_h = engine.gs.lock().unwrap().compute_holonomy_norm();
            println!("🛡️  [HEALED] Substrate returned to uncorrupted parallel transport baseline: {:.5}", restored_h);
            
            // Commit defensive transaction to the shared ledger
            RollbackEngine::commit_rollback_log(proposed_h, restored_h, audit.computed_velocity);
        },
        _ => {
            println!("✅ [CONFORMITY PASS] Updates within acceptable parameters. No immune response required.");
        }
    }
}
EOF
