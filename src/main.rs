cat << 'EOF' > src/main.rs
/*
main.rs
ISST-TOFT Sovereign Substrate Grid Entry Point.
Dual Ledger-Writing Run: Synchronizes Rust invariant scores natively into tordial_gs.db.
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
    println!("🔥  ISST-TOFT Sovereign Substrate Grid [SHARED LEDGER CORE]");
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
                "cERNpiranchor" => 0,
                "warpcorestability" => 1,
                "sovereignintentprimary" => 2,
                "sovereignintentambient" => 3,
                "sensorium_feedback" => 4,
                "mutationplanedriver" => 5,
                _ => continue,
            };
            if update.reason.contains("strike") { continue; }
            if let Ok(t_strike) = strike_time_clone.lock() {
                if *t_strike > 0 && (update.timestamp - *t_strike) <= 50 {
                    if let Ok(mut steps) = observed_clone.lock() {
                        if steps[idx].is_none() {
                            steps[idx] = Some(update.intent_value);
                        }
                    }
                }
            }
        }
    });

    tokio::time::sleep(tokio::time::Duration::from_millis(50)).await;

    // ─── STAGE 1: ACTIVE INJECTION PASS ───
    let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_millis() as i64;
    if let Ok(mut t_strike) = strike_time.lock() { *t_strike = now; }
    
    let pulse_initial = 0.9990;
    println!("\n🏋️ [RUST RUNTIME] Dispatching active WalkerPush surge...");
    engine.broadcast_update(IntentUpdate {
        band_id: "mutationplanedriver".to_string(),
        mode: 1,
        intent_value: pulse_initial,
        timestamp: now,
        reason: "walker_push_strike".to_string(),
    });

    let initial_operator = engine.gs.lock().unwrap().clone();
    let band_map = ["cERNpiranchor", "warpcorestability", "sovereignintentprimary", "sovereignintentambient", "sensorium_feedback"];

    for i in 0..5 {
        let distorted_coeff = initial_operator.effective(i, 5, GSMode::WalkerPush) + 0.040;
        engine.broadcast_update(IntentUpdate {
            band_id: band_map[i].to_string(),
            mode: 1,
            intent_value: pulse_initial * distorted_coeff,
            timestamp: now,
            reason: "distorted_push_wave".to_string(),
        });
    }

    tokio::time::sleep(tokio::time::Duration::from_millis(60)).await;

    let mut push_step = vec![0.0; 6];
    if let Ok(steps) = observed_first_step.lock() {
        for i in 0..6 { push_step[i] = steps[i].unwrap_or(0.0); }
    }
    push_step[5] = pulse_initial;

    engine.gs.lock().unwrap().learn_push(5, pulse_initial, &push_step, 0.10);

    // ─── COMPUTE LOCAL GEOMETRIC INVARIANT ───
    let final_gs = engine.gs.lock().unwrap().clone();
    let rust_holonomy_norm = final_gs.compute_holonomy_norm();
    println!("📊 [RUST RUNTIME] Computed Frobenius Holonomy Norm (||Ω||_F): {:.5}", rust_holonomy_norm);

    // ─── COMMIT NATIVELY TO THE TORDIAL CORE LEDGER ───
    println!("[*] Committing local invariant entry directly into tordial_gs.db ledger...");
    let query = format!(
        "INSERT INTO runs (timestamp, runtime_env, node_count, final_freq, quarantine_rate, avg_kappa, stability_score, holonomy_norm, holonomy_norm_local) VALUES (datetime('now'), 'Rust', 6, 0.0, 0.0, 0.0, 0.85, 0.0, {});", 
        rust_holonomy_norm
    );

    let status = Command::new("sqlite3")
        .arg("tordial_gs.db")
        .arg(&query)
        .status();

    match status {
        Ok(s) if s.success() => println!("✅ [LEDGER SYNC SUCCESS] Substrate metric saved securely."),
        _ => eprintln!("❌ [LEDGER SYNC FAILURE] Verification track blocked."),
    }
}
EOF
cargo run
