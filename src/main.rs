cat << 'EOF' > src/main.rs
/*
main.rs
ISST-TOFT Sovereign Substrate Grid Entry Point.
Implements non-blocking broadcast updates across memory-mapped intent bands.
*/

mod issttoft;
mod intent_engine;

use std::sync::Arc;
use crate::intent_engine::IntentEngine;
use crate::issttoft::IntentUpdate;
use std::time::{SystemTime, UNIX_EPOCH};

#[tokio::main]
async fn main() {
    // Initialize tracing subscriber console logger
    tracing_subscriber::fmt::init();
    
    println!("══════════════════════════════════════════════════════════════");
    println!("🔥  ISST-TOFT Sovereign Substrate Grid Active");
    println!("══════════════════════════════════════════════════════════════");

    // Initialize the single source of truth engine
    let engine = Arc::new(IntentEngine::new());

    // 1. Establish an asynchronous stream listener to mimic a live cluster client
    let mut rx = engine.subscribe();
    tokio::spawn(async move {
        println!("📥 [STREAM WATCHER] Consumer subscription online. Monitoring field changes...");
        while let Ok(update) = rx.recv().await {
            println!(
                "   ✨ [STREAM UPDATE CATCH] Band: '{}' | Value: {:.4} | Source: {}", 
                update.band_id, update.intent_value, update.reason
            );
        }
    });

    // Pause briefly to let the asynchronous task bind cleanly
    tokio::time::sleep(tokio::time::Duration::from_millis(50)).await;

    // 2. Execute Handshake Verification
    let response = engine.handshake(
        "Zhuu-01".to_string(), 
        "WARP_CORE".to_string(), 
        "SovereignClaim_Active".to_string()
    );

    println!("\n🤝 [HANDSHAKE RESPONSE]");
    println!("   Status: {}", response.mesh_status);
    println!("   Keeper Note: {}", response.flamekeeper_note);
    println!("   Active Bands Cached: {}", response.initial_bands.len());

    // 3. Fire a live broadcast update into the network to exercise the telemetry loops
    println!("\n⚡ [MUTATION PLANE] Perturbing the dynamic_pi_r_floor...");
    let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_secs() as i64;
    
    engine.broadcast_update(IntentUpdate {
        band_id: "dynamic_pi_r_floor".to_string(),
        mode: 1,
        intent_value: 0.999, // Static ceiling safety limit
        timestamp: now,
        reason: "pi_r_engine_stabilization_pulse".to_string(),
    });

    // Hold the runtime open for a fraction of a second to capture the outbound packet
    tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
}
EOF
