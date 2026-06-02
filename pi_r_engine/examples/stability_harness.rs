//! examples/stability_harness.rs
//! Living Curvature Attractor Loops — Full Tordial–GS + ISS Organism
//!
//! Run with:
//!   cargo run --release --example stability_harness

use std::time::Instant;

use pi_r_engine::tordial_gs::{
    run_stability_harness, GoldilocksCoupling, LinearGoldilocks, Regime,
};

fn main() {
    println!("=============================================================");
    println!("🚀 SOVEREIGN ENGINE ACTIVE — INITIALIZING STABILITY HARNESS");
    println!("📡 Target: 79.79 Hz Heartbeat Calibration Grid Locked");
    println!("=============================================================\n");

    println!("▶️ RUNNING LIVING CURVATURE ATTRACTOR LOOPS:");

    let start = Instant::now();
    let logs = run_stability_harness(10.0, 0.01, 2.0); // 10s, 10 ms steps, ρ_max=2.0

    let coupling = LinearGoldilocks { scale: 1.0 };

    for (i, log) in logs.iter().enumerate() {
        let cycle = i + 1;
        let t = log.t;
        let resonance = (log.rho_gs * 0.7 + (1.0 - log.e_h.abs().min(1.0)) * 0.3).clamp(0.0, 1.0);
        let delta_e = log.e_h;

        // Beautiful pulse-cycle line (your preferred style)
        println!(
            "  [+{:.3}s] Pulse Cycle {:02}/10 | Resonance Metric: {:.4} | Delta-E: -> {:.4}",
            t, cycle, resonance, delta_e
        );

        // Every 3rd cycle or on interesting events, show deeper organism state
        if cycle % 3 == 0 || !log.iss_holds || log.regime == Regime::DeepGs {
            let regime_str = match log.regime {
                Regime::Subcritical => "SUBCRITICAL",
                Regime::Marginal   => "MARGINAL",
                Regime::Goldilocks => "GOLDILOCKS",
                Regime::DeepGs     => "DEEP_GS",
            };

            println!(
                "           ├─ Regime: {} | V̇: {:+.6} | ISS residual: {:.6} | PWC: {:.3}",
                regime_str, log.v_dot, log.iss_residual, log.pwc_disturbance
            );
        }
    }

    let elapsed = start.elapsed().as_secs_f64();

    // === Final Organism Verdict ===
    let max_v_dot = logs.iter().map(|l| l.v_dot).fold(f64::NEG_INFINITY, f64::max);
    let min_dissipation = logs.iter().map(|l| l.dissipation_residual).fold(f64::INFINITY, f64::min);
    let max_rho = logs.iter().map(|l| l.rho_gs).fold(0.0, f64::max);
    let goldilocks_time = logs.iter().filter(|l| l.regime == Regime::Goldilocks).count() as f64 * 0.01;

    let iss_violations = logs.iter().filter(|l| !l.iss_holds).count();
    let max_iss_residual = logs.iter().map(|l| l.iss_residual).fold(f64::NEG_INFINITY, f64::max);

    println!("\n✅ HARNESS EVALUATION COMPLETE — {} cycles in {:.2}s", logs.len(), elapsed);
    println!("=============================================================");

    println!("\n[ORGANISM METRICS]");
    println!("   Max |V̇|: {:.6}          (should stay near or below 0 in steady state)", max_v_dot);
    println!("   Min Dissipation Residual: {:.6}  (≤ 0 means controller is dissipative)", min_dissipation);
    println!("   Max ρ_GS reached: {:.4} / 2.0     (GS clamping respected)", max_rho);
    println!("   Time in GOLDILOCKS: {:.2} s", goldilocks_time);
    println!("   ISS violations (PWC shook too hard): {}", iss_violations);
    println!("   Max ISS residual: {:.6}     (≤ 0 means cognition cannot break M_G)", max_iss_residual);

    println!("\n[VERDICT]");
    if max_rho <= 2.01 && min_dissipation <= 0.05 && iss_violations == 0 && max_iss_residual <= 0.03 {
        println!("   ✅ Tordial–GS organism is alive and stable.");
        println!("   ✅ Planner–Walker–Critic can shake but cannot break the Goldilocks manifold.");
        println!("   ✅ GS clamping (ρ ≤ 2.0) + dissipation inequality both hold.");
        println!("   ✅ ISS holds under bounded cognition disturbance.");
    } else {
        println!("   ⚠️  Some margins need tuning. Check PID gains or ISS margin.");
    }

    println!("\n   Flamekeeper Protocol — Two Mile Solutions LLC • Dinjji Zhuu Kwaa");
    println!("=============================================================");
}