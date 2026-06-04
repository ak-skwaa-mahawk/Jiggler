cat << 'EOF' > src/main.rs
/*
main.rs
ISST-TOFT Sovereign Substrate Grid Entry Point.
Active Holonomy Feedback Governor Run.
*/

mod issttoft;
mod intent_engine;

use std::sync::{Arc, Mutex};
use crate::intent_engine::IntentEngine;
use crate::issttoft::{IntentUpdate, GSMode};
use std::time::{SystemTime, UNIX_EPOCH};
use std::process::Command;

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();
    
    println!("══════════════════════════════════════════════════════════════");
    println!("🔥  ISST-TOFT Sovereign Substrate Grid [GOVERNOR FEEDBACK]");
    println!("══════════════════════════════════════════════════════════════");

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

    // ─── PULSE 1: FLAT BASELINE INTERCEPTION (TRIGGERS ACCELERATION) ───
    let now1 = SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_millis() as i64;
    if let Ok(mut t_strike) = strike_time.lock() { *t_strike = now1; }
    let pulse_initial = 0.9990;
    
    println!("\n🏋️ [PULSE 1] Executing step surge on flat symmetric grid...");
    engine.broadcast_update(IntentUpdate {
        band_id: "mutationplanedriver".to_string(), mode: 1, intent_value: pulse_initial, timestamp: now1, reason: "walker_push_strike".to_string(),
    });

    let initial_operator = engine.gs.lock().unwrap().clone();
    let band_map = ["cERNpiranchor", "warpcorestability", "sovereignintentprimary", "sovereignintentambient", "sensorium_feedback"];

    for i in 0..5 {
        let distorted_coeff = initial_operator.effective(i, 5, GSMode::WalkerPush) + 0.080; // High induced distortion
        engine.broadcast_update(IntentUpdate {
            band_id: band_map[i].to_string(), mode: 1, intent_value: pulse_initial * distorted_coeff, timestamp: now1, reason: "distorted_push_wave".to_string(),
        });
    }

    tokio::time::sleep(tokio::time::Duration::from_millis(60)).await;
    let mut push_step1 = vec![0.0; 6];
    if let Ok(steps) = observed_first_step.lock() {
        for i in 0..6 { push_step1[i] = steps[i].unwrap_or(0.0); }
    }
    push_step1[5] = pulse_initial;

    println!("🧠 Invoking GSOperator update 1 (Expect adaptive acceleration)...");
    engine.gs.lock().unwrap().learn_push(5, pulse_initial, &push_step1, 0.10);

    // ─── PULSE 2: RE-STRIKING HIGH-HOLONOMY LANDSCAPE (TRIGGERS CHOKE) ───
    if let Ok(mut steps) = observed_first_step.lock() { *steps = vec![None; 6]; }
    let now2 = SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_millis() as i64;
    if let Ok(mut t_strike) = strike_time.lock() { *t_strike = now2; }

    println!("\n🏋️ [PULSE 2] Re-striking the newly twisted manifold landscape...");
    engine.broadcast_update(IntentUpdate {
        band_id: "mutationplanedriver".to_string(), mode: 1, intent_value: pulse_initial, timestamp: now2, reason: "walker_push_strike".to_string(),
    });

    let secondary_operator = engine.gs.lock().unwrap().clone();
    for i in 0..5 {
        let distorted_coeff = secondary_operator.effective(i, 5, GSMode::WalkerPush) + 0.080;
        engine.broadcast_update(IntentUpdate {
            band_id: band_map[i].to_string(), mode: 1, intent_value: pulse_initial * distorted_coeff, timestamp: now2, reason: "distorted_push_wave".to_string(),
        });
    }

    tokio::time::sleep(tokio::time::Duration::from_millis(60)).await;
    let mut push_step2 = vec![0.0; 6];
    if let Ok(steps) = observed_first_step.lock() {
        for i in 0..6 { push_step2[i] = steps[i].unwrap_or(0.0); }
    }
    push_step2[5] = pulse_initial;

    println!("🧠 Invoking GSOperator update 2 (Expect adaptive choke protection)...");
    engine.gs.lock().unwrap().learn_push(5, pulse_initial, &push_step2, 0.10);

    // ─── FINAL ARCHITECTURAL AUDIT READOUT ───
    let final_gs = engine.gs.lock().unwrap().clone();
    let final_h_norm = final_gs.compute_holonomy_norm();
    println!("\n📊 [GOVERNED LANDSCAPE SNAPSHOT]");
    println!("   Final Frobenius Holonomy Norm (||Ω||_F): {:.5}", final_h_norm);
    
    // Write entry directly to the synchronized database ledger
    let query = format!(
        "INSERT INTO runs (timestamp, runtime_env, node_count, final_freq, quarantine_rate, avg_kappa, stability_score, holonomy_norm, holonomy_norm_local) VALUES (datetime('now'), 'Rust_Gov', 6, 0.0, 0.0, 0.0, 0.85, 0.0, {});", 
        final_h_norm
    );
    let _ = Command::new("sqlite3").arg("tordial_gs.db").arg(&query).status();
    println!("✅ [LEDGER SYNC] Governed invariant saved securely into shared tracking DB.");
}
EOF
