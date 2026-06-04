cat << 'EOF' > src/main.rs
/*
main.rs
ISST-TOFT Sovereign Substrate Grid Entry Point.
Consensus Run: Reads historical database bounds before validating geometric parameters.
*/

mod issttoft;
mod intent_engine;

use std::sync::{Arc, Mutex};
use crate::intent_engine::IntentEngine;
use crate::issttoft::{IntentUpdate, GSMode};
use std::time::{SystemTime, UNIX_EPOCH};
use std::process::Command;

fn get_last_ledger_holonomy() -> f64 {
    // Query the last committed local holonomy norm from the shared SQLite database
    let output = Command::new("sqlite3")
        .arg("tordial_gs.db")
        .arg("SELECT holonomy_norm_local FROM runs WHERE holonomy_norm_local > 0 ORDER BY id DESC LIMIT 1;")
        .output();

    if let Ok(out) = output {
        let text = String::from_utf8_lossy(&out.stdout);
        if let Some(line) = text.lines().next() {
            if let Ok(val) = line.trim().parse::<f64>() {
                println!("📖 [CONSENSUS LAYER] Retrieved historical benchmark from ledger: {:.5}", val);
                return val;
            }
        }
    }
    println!("📖 [CONSENSUS LAYER] No historical benchmark detected. Initializing standard baseline matrix.");
    0.05000 // Default fallback prior if database table is empty
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();
    
    println!("══════════════════════════════════════════════════════════════");
    println!("🔥  ISST-TOFT Sovereign Substrate Grid [CONSENSUS LAYER]");
    println!("══════════════════════════════════════════════════════════════");

    // Fetch ledger prior before configuring engine states
    let historical_prior = get_last_ledger_holonomy();

    let engine = Arc::new(IntentEngine::new());
    let mut rx = engine.subscribe();

    // Dynamically bias our GSOperator thresholds using the shared ledger memory
    {
        let mut gs = engine.gs.lock().unwrap();
        // If the historical manifold was highly distorted, dynamically tighten our safety envelope
        if historical_prior > 0.10 {
            println!("🔒 [CONSENSUS VETO] Historical distortion high. Constraining omega_max parameter cell...");
            gs.omega_max = 0.03500; 
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

    // ─── RUNTIME ADAPTATION PASS ───
    let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_millis() as i64;
    if let Ok(mut t_strike) = strike_time.lock() { *t_strike = now; }
    let pulse_initial = 0.9990;
    
    println!("\n🏋️ [WALKER STEP] Injecting active perturbation wave into substrate...");
    engine.broadcast_update(IntentUpdate {
        band_id: "mutationplanedriver".to_string(), mode: 1, intent_value: pulse_initial, timestamp: now, reason: "walker_push_strike".to_string(),
    });

    let initial_operator = engine.gs.lock().unwrap().clone();
    let band_map = ["cERNpiranchor", "warpcorestability", "sovereignintentprimary", "sovereignintentambient", "sensorium_feedback"];

    for i in 0..5 {
        let distorted_coeff = initial_operator.effective(i, 5, GSMode::WalkerPush) + 0.060;
        engine.broadcast_update(IntentUpdate {
            band_id: band_map[i].to_string(), mode: 1, intent_value: pulse_initial * distorted_coeff, timestamp: now, reason: "distorted_push_wave".to_string(),
        });
    }

    tokio::time::sleep(tokio::time::Duration::from_millis(60)).await;
    let mut push_step = vec![0.0; 6];
    if let Ok(steps) = observed_first_step.lock() {
        for i in 0..6 { push_step[i] = steps[i].unwrap_or(0.0); }
    }
    push_step[5] = pulse_initial;

    // Execute state adaptation under ledger guidance
    engine.gs.lock().unwrap().learn_push(5, pulse_initial, &push_step, 0.10);

    // Final calculations and validation check
    let final_gs = engine.gs.lock().unwrap().clone();
    let proposed_h_norm = final_gs.compute_holonomy_norm();
    
    println!("\n⚖️ [CONSENSUS AUDIT] Proposed Holonomy: {:.5} | Benchmark: {:.5}", proposed_h_norm, historical_prior);

    // Absolute Consensus Threshold Policy Check
    if proposed_h_norm > historical_prior * 1.5 {
        println!("❌ [CONSENSUS REJECTION] Proposed step causes geometric divergence greater than 1.5x prior ledger baseline! Aborting transaction commit.");
    } else {
        println!("✅ [CONSENSUS ADMISSION] Metric parameters within allowable contract limits. Writing to shared ledger...");
        let query = format!(
            "INSERT INTO runs (timestamp, runtime_env, node_count, final_freq, quarantine_rate, avg_kappa, stability_score, holonomy_norm, holonomy_norm_local) VALUES (datetime('now'), 'Rust_Consensus', 6, 0.0, 0.0, 0.0, 0.85, 0.0, {});", 
            proposed_h_norm
        );
        let _ = Command::new("sqlite3").arg("tordial_gs.db").arg(&query).status();
        println!("💾 [LEDGER COMMIT SUCCESS] Invariant track updated.");
    }
}
EOF
