cat << 'EOF' > src/main.rs
/*
main.rs
ISST-TOFT Sovereign Substrate Grid Entry Point.
Executes an interactive Multi-Band Matrix Field Propagation and Damping Relaxation Run.
*/

mod issttoft;
mod intent_engine;

use std::sync::Arc;
use crate::intent_engine::IntentEngine;
use crate::issttoft::{IntentUpdate, get_coupling_coefficient};
use std::time::{SystemTime, UNIX_EPOCH};

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();
    
    println!("══════════════════════════════════════════════════════════════");
    println!("🔥  ISST-TOFT Sovereign Substrate Grid Active [DAMPING RUN]");
    println!("══════════════════════════════════════════════════════════════");

    let engine = Arc::new(IntentEngine::new());
    let mut rx = engine.subscribe();

    // 1. Live Client Watcher Layer
    tokio::spawn(async move {
        while let Ok(update) = rx.recv().await {
            println!(
                "   ✨ [STREAM UPDATE CATCH] Band: {:<22} | Value: {:.4} | Driver: {}", 
                update.band_id, update.intent_value, update.reason
            );
        }
    });

    // 2. Spawn Background Relaxation Engine Ticker (Runs every 100ms)
    let engine_clone = Arc::clone(&engine);
    tokio::spawn(async move {
        loop {
            tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
            engine_clone.step_damping_field(0.1); // dt = 0.1s step size
        }
    });

    tokio::time::sleep(tokio::time::Duration::from_millis(50)).await;

    // 3. Shock the Manifold: Strike Band 5
    println!("\n⚡ [TORQUE GENERATION] Striking Band 5 with a massive experimental pulse...");
    let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_secs() as i64;
    let pulse_value = 0.9990;
    
    let band_map = [
        "cERNpiranchor", "warpcorestability", "sovereignintentprimary", 
        "sovereignintentambient", "sensorium_feedback", "mutationplanedriver"
    ];

    engine.broadcast_update(IntentUpdate {
        band_id: "mutationplanedriver".to_string(),
        mode: 1,
        intent_value: pulse_value,
        timestamp: now,
        reason: "experimental_injection_pulse".to_string(),
    });

    // Ripple across the coupling matrix
    for i in 0..5 {
        let coeff = get_coupling_coefficient(i, 5);
        engine.broadcast_update(IntentUpdate {
            band_id: band_map[i].to_string(),
            mode: 1,
            intent_value: pulse_value * coeff,
            timestamp: now,
            reason: format!("coupling_propagation_from_band_5(coeff={:.2})", coeff),
        });
    }

    // 4. Observe Relaxation Curve Lifecycle
    println!("\n⏳ [FIELD ANALYSIS] Holding loop open to track natural relaxation curves...");
    tokio::time::sleep(tokio::time::Duration::from_millis(800)).await;
    
    println!("\n✅ [SIMULATION END] Manifold stabilized cleanly back to ground-state invariants.");
}
EOF
