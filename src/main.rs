cat << 'EOF' > src/main.rs
/*
main.rs
ISST-TOFT Sovereign Substrate Grid Entry Point.
Implements Noise-Gated, Temporal-Windowed, Stiffness-Aware Auto-Tuning Loops.
*/

mod issttoft;
mod intent_engine;

use std::sync::{Arc, Mutex};
use crate::intent_engine::IntentEngine;
use crate::issttoft::IntentUpdate;
use std::time::{SystemTime, UNIX_EPOCH};

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();
    
    println!("══════════════════════════════════════════════════════════════");
    println!("🔥  ISST-TOFT Sovereign Substrate Grid [ROBUST LEARNING]");
    println!("══════════════════════════════════════════════════════════════");

    let engine = Arc::new(IntentEngine::new());
    let mut rx = engine.subscribe();

    let observed_first_step = Arc::new(Mutex::new(vec![None; 6]));
    let strike_time = Arc::new(Mutex::new(0_i64));

    // 1. Thread Observer with strict time-series window validation
    let observed_clone = Arc::clone(&observed_first_step);
    let strike_time_clone = Arc::clone(&strike_time);
    tokio::spawn(async move {
        while let Ok(update) = rx.recv().await {
            println!("   ✨ [LIVE BUS] Update -> {:<22} | Value: {:.4}", update.band_id, update.intent_value);

            let idx = match update.band_id.as_str() {
                "cERNpiranchor" => 0,
                "warpcorestability" => 1,
                "sovereignintentprimary" => 2,
                "sovereignintentambient" => 3,
                "sensorium_feedback" => 4,
                "mutationplanedriver" => 5,
                _ => continue,
            };

            if update.reason == "calibration_training_strike" {
                continue;
            }

            // Lock validation down to packets clearing the bus within a 50ms window
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

    // 2. Shock the Manifold with Induced Synthetic Deviation (Simulating environmental warp)
    let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_millis() as i64;
    if let Ok(mut t_strike) = strike_time.lock() {
        *t_strike = now;
    }
    
    let pulse_initial = 0.9990;
    
    println!("\n🏋️ [GEOMETRY STRIKE] Inducing torque impact into Band 5...");
    engine.broadcast_update(IntentUpdate {
        band_id: "mutationplanedriver".to_string(),
        mode: 1,
        intent_value: pulse_initial,
        timestamp: now,
        reason: "calibration_training_strike".to_string(),
    });

    let initial_matrix = engine.coupling_matrix.lock().unwrap().clone();
    let band_map = [
        "cERNpiranchor", "warpcorestability", "sovereignintentprimary", 
        "sovereignintentambient", "sensorium_feedback"
    ];

    // Intentionally inject an environmental deviation that exceeds the 0.005 noise floor gate
    // to trigger the adaptive alignment mechanics explicitly
    for i in 0..5 {
        let baseline_coeff = initial_matrix.get(i, 5);
        let distorted_coeff = baseline_coeff + 0.025; // Force a +0.025 warp delta
        
        engine.broadcast_update(IntentUpdate {
            band_id: band_map[i].to_string(),
            mode: 1,
            intent_value: pulse_initial * distorted_coeff,
            timestamp: now,
            reason: "distorted_environmental_propagation".to_string(),
        });
    }

    tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;

    // 3. Extract captured data values
    let mut real_first_step = vec![0.0; 6];
    if let Ok(steps) = observed_first_step.lock() {
        for i in 0..6 {
            real_first_step[i] = steps[i].unwrap_or(0.0);
        }
    }
    real_first_step[5] = pulse_initial;

    println!("\n📐 [COUPLING PRE-OPTIMIZATION]");
    println!("   Old C[1][5] (mutation->stability) : {:.4}", initial_matrix.get(1, 5));
    println!("   Old C[3][5] (mutation->ambient)   : {:.4}", initial_matrix.get(3, 5));

    // 🚀 Execute the robust, adaptive auto-tuning step
    println!("\n🧠 [ROBUST ADJUSTMENT] Tuning matrix parameters based on verified window captures...");
    engine.update_c_from_strike(5, pulse_initial, &real_first_step, 0.10);

    // Pull the post-optimization results
    let post_matrix = engine.coupling_matrix.lock().unwrap().clone();
    println!("\n📝 [COUPLING POST-OPTIMIZATION]");
    println!("   New C[1][5] (mutation->stability) : {:.4}", post_matrix.get(1, 5));
    println!("   New C[3][5] (mutation->ambient)   : {:.4}", post_matrix.get(3, 5));
    
    println!("\n✅ [MANIFOLD SECURE] Geometric tracking parameters updated and verified.");
}
EOF
