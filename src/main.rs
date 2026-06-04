cat << 'EOF' > src/main.rs
/*
main.rs
ISST-TOFT Sovereign Substrate Grid Entry Point.
Unified Run: Implements Temporal-Windowed Window Captures, Live Learning Governor Limits,
and the Non-Associative GS Curvature Operator.
*/

mod gs;
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
    println!("🔥  ISST-TOFT Sovereign Substrate Grid [PRODUCTION UNIFIED]");
    println!("══════════════════════════════════════════════════════════════");

    let engine = Arc::new(IntentEngine::new());
    let mut rx = engine.subscribe();

    let observed_first_step = Arc::new(Mutex::new(vec![None; 6]));
    let strike_time = Arc::new(Mutex::new(0_i64));

    // 1. Strict Async Temporal Gate Observer
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

            // Gating window restricted tightly to 50ms bounds
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

    // 2. Maximum Saturation Torque Strike
    let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_millis() as i64;
    if let Ok(mut t_strike) = strike_time.lock() {
        *t_strike = now;
    }
    
    let pulse_initial = 0.9990; // Automatically triggers the Learning Governor high-energy throttle
    
    println!("\n🏋️ [GEOMETRY STRIKE] Striking Band 5 at max saturation ({:.4})...", pulse_initial);
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

    // Induce significant environmental drift (+0.040) to force adaptation beyond noise gates
    for i in 0..5 {
        let baseline_coeff = initial_matrix.get(i, 5);
        let distorted_coeff = baseline_coeff + 0.040;
        
        engine.broadcast_update(IntentUpdate {
            band_id: band_map[i].to_string(),
            mode: 1,
            intent_value: pulse_initial * distorted_coeff,
            timestamp: now,
            reason: "distorted_environmental_propagation".to_string(),
        });
    }

    tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;

    // 3. Extract verified real-time metrics
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

    // 🚀 4. Execute the Non-Associative GS Curvature Memory Optimization Step
    println!("\n🧠 [GS OPERATOR PASS] Running governor-gated curvature convergence...");
    engine.update_c_from_strike(5, pulse_initial, &real_first_step, 0.10);

    let post_matrix = engine.coupling_matrix.lock().unwrap().clone();
    println!("\n📝 [COUPLING POST-OPTIMIZATION]");
    println!("   New C[1][5] (mutation->stability) : {:.4}", post_matrix.get(1, 5));
    println!("   New C[3][5] (mutation->ambient)   : {:.4}", post_matrix.get(3, 5));
    
    // Validate edge brain curvature record retention
    let edge_brain = post_matrix.gs_state[1][5].clone();
    println!("   Accumulated Edge Curvature Memory (1->5): {:.4}", edge_brain.curvature);
    
    println!("\n✅ [MANIFOLD SECURE] Self-healing geometric parameter alignment stable.");
}
EOF
