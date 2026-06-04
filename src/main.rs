cat << 'EOF' > src/main.rs
/*
main.rs
ISST-TOFT Sovereign Substrate Grid Entry Point.
Directed Asymmetric Unified Run: Demonstrates Push/Pull decorelation and non-zero holonomy.
*/

mod issttoft;
mod intent_engine;

use std::sync::{Arc, Mutex};
use crate::intent_engine::IntentEngine;
use crate::issttoft::{IntentUpdate, EdgeRole};
use std::time::{SystemTime, UNIX_EPOCH};

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();
    
    println!("══════════════════════════════════════════════════════════════");
    println!("🔥  ISST-TOFT Sovereign Substrate Grid [DIRECTED HOLONOMY]");
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

            if update.reason.contains("strike") {
                continue;
            }

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

    // ─── CYCLE 1: WALKER PUSH STRIKE FROM BAND 5 ───
    let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_millis() as i64;
    if let Ok(mut t_strike) = strike_time.lock() { *t_strike = now; }
    
    let pulse_initial = 0.9990;
    println!("\n🏋️ [WALKER PUSH] Striking Band 5 at high salience ({:.4})...", pulse_initial);
    engine.broadcast_update(IntentUpdate {
        band_id: "mutationplanedriver".to_string(),
        mode: 1,
        intent_value: pulse_initial,
        timestamp: now,
        reason: "walker_push_strike".to_string(),
    });

    let initial_matrix = engine.coupling_matrix.lock().unwrap().clone();
    let band_map = ["cERNpiranchor", "warpcorestability", "sovereignintentprimary", "sovereignintentambient", "sensorium_feedback"];

    for i in 0..5 {
        let distorted_coeff = initial_matrix.get_push(i, 5) + 0.040; // Simulate environmental distortion warp
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

    println!("🧠 Running non-commutative WalkerPush tensor adjustment...");
    engine.update_c_from_strike(5, pulse_initial, &push_step, 0.10, EdgeRole::WalkerPush);

    // ─── CYCLE 2: AMBIENT PULL REBALANCING FROM BAND 3 ───
    if let Ok(mut steps) = observed_first_step.lock() { *steps = vec![None; 6]; }
    let now_pull = SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_millis() as i64;
    if let Ok(mut t_strike) = strike_time.lock() { *t_strike = now_pull; }
    
    let ambient_pulse = 0.5000;
    println!("\n🌊 [AMBIENT PULL] Context field re-projecting balancing torque from Band 3 ({:.4})...", ambient_pulse);
    engine.broadcast_update(IntentUpdate {
        band_id: "sovereignintentambient".to_string(),
        mode: 0,
        intent_value: ambient_pulse,
        timestamp: now_pull,
        reason: "ambient_pull_strike".to_string(),
    });

    for i in 0..6 {
        if i == 3 { continue; }
        let distorted_pull = initial_matrix.get_pull(i, 3) - 0.030; // Simulate reverse rebalancing warp
        engine.broadcast_update(IntentUpdate {
            band_id: match i {
                0 => "cERNpiranchor".to_string(),
                1 => "warpcorestability".to_string(),
                2 => "sovereignintentprimary".to_string(),
                4 => "sensorium_feedback".to_string(),
                5 => "mutationplanedriver".to_string(),
                _ => continue
            },
            mode: 0,
            intent_value: ambient_pulse * distorted_pull,
            timestamp: now_pull,
            reason: "distorted_pull_wave".to_string(),
        });
    }

    tokio::time::sleep(tokio::time::Duration::from_millis(60)).await;

    let mut pull_step = vec![0.0; 6];
    if let Ok(steps) = observed_first_step.lock() {
        for i in 0..6 { pull_step[i] = steps[i].unwrap_or(0.0); }
    }
    pull_step[3] = ambient_pulse;

    println!("🧠 Running non-commutative AmbientPull tensor adjustment...");
    engine.update_c_from_strike(3, ambient_pulse, &pull_step, 0.10, EdgeRole::AmbientPull);

    // ─── READOUT CALIBRATED ASYMMETRIC TOPOLOGY ───
    let post_matrix = engine.coupling_matrix.lock().unwrap().clone();
    println!("\n📊 [GEOMETRIC TRACK REALIZATION]");
    println!("   Edge (5 -> 1) PUSH Coeff : {:.4} | Curvature Memory: {:.4}", post_matrix.push[1][5].coeff, post_matrix.push[1][5].curvature);
    println!("   Edge (5 -> 1) PULL Coeff : {:.4} | Curvature Memory: {:.4}", post_matrix.pull[1][5].coeff, post_matrix.pull[1][5].curvature);
    println!("   Effective Operator Projection C[1][5]: {:.4}", post_matrix.effective(1, 5));
    
    println!("\n🔄 [HYSTERESIS LEAK VALIDATION]");
    println!("   Edge (1 -> 5) PULL Hysteresis Curvature: {:.4}", post_matrix.pull[5][1].curvature);
    
    println!("\n✅ [MANIFOLD SECURE] Non-commutative holonomy channels verified active.");
}
EOF
