cat << 'EOF' > src/main.rs
/*
main.rs
ISST-TOFT Sovereign Substrate Grid Entry Point.
Implements Live Geometric Auto-Tuning Loops and Field Refinement Optimization Passes.
*/

mod issttoft;
mod intent_engine;

use std::sync::Arc;
use crate::intent_engine::IntentEngine;
use crate::issttoft::IntentUpdate;
use std::time::{SystemTime, UNIX_EPOCH};

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();
    
    println!("══════════════════════════════════════════════════════════════");
    println!("🔥  ISST-TOFT Sovereign Substrate Grid [AUTO-TUNING RUN]");
    println!("══════════════════════════════════════════════════════════════");

    let engine = Arc::new(IntentEngine::new());
    let mut rx = engine.subscribe();

    tokio::spawn(async move {
        while let Ok(update) = rx.recv().await {
            println!("   ✨ [LIVE BUS] Mapped update to {} -> {:.4}", update.band_id, update.intent_value);
        }
    });

    tokio::time::sleep(tokio::time::Duration::from_millis(50)).await;

    let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_secs() as i64;
    let pulse_initial = 0.9990;
    
    println!("\n🏋️ [GEOMETRY PASS] Instantiating primary torque injection on Band 5...");
    engine.broadcast_update(IntentUpdate {
        band_id: "mutationplanedriver".to_string(),
        mode: 1,
        intent_value: pulse_initial,
        timestamp: now,
        reason: "calibration_training_strike".to_string(),
    });

    // Capture the first-step response vector across the 6-band manifold layout
    let initial_matrix = engine.coupling_matrix.lock().unwrap().clone();
    let mut first_step_values = vec![0.0; 6];
    
    // Calculate the expected immediate wavefront propagation
    for i in 0..5 {
        first_step_values[i] = pulse_initial * initial_matrix.get(i, 5);
        engine.broadcast_update(IntentUpdate {
            band_id: match i {
                0 => "cERNpiranchor".to_string(),
                1 => "warpcorestability".to_string(),
                2 => "sovereignintentprimary".to_string(),
                3 => "sovereignintentambient".to_string(),
                4 => "sensorium_feedback".to_string(),
                _ => "unknown".to_string()
            },
            mode: 1,
            intent_value: first_step_values[i],
            timestamp: now,
            reason: "calibration_wave_propagation".to_string(),
        });
    }
    first_step_values[5] = pulse_initial;

    // Print baseline calibration parameters before optimization pass
    println!("\n📐 [COUPLING PRE-OPTIMIZATION]");
    println!("   Old C[1][5] (mutation->stability) : {:.4}", initial_matrix.get(1, 5));
    println!("   Old C[3][5] (mutation->ambient)   : {:.4}", initial_matrix.get(3, 5));

    // 🚀 Execute the Geometry Adaptation Step (Learning rate alpha = 0.05)
    println!("\n🧠 [ADAPTIVE ADJUSTMENT] Matrix running self-aware correction step...");
    engine.update_c_from_strike(5, pulse_initial, &first_step_values, 0.05);

    // Pull the modified matrix layers post training update
    let post_matrix = engine.coupling_matrix.lock().unwrap().clone();
    println!("\n📝 [COUPLING POST-OPTIMIZATION]");
    println!("   New C[1][5] (mutation->stability) : {:.4}", post_matrix.get(1, 5));
    println!("   New C[3][5] (mutation->ambient)   : {:.4}", post_matrix.get(3, 5));
    
    println!("\n✅ [LEARNING MATRIX STABLE] Calibration adjustments completed successfully.");
}
EOF
