//! sovereign_operator.rs
//! Unified Sovereign Control Surface — Tordial-GS Manifold
//! Flamekeeper Protocol — Dinjji Zhuu Kwaa

use std::sync::{Arc, Mutex};

use crate::intent_engine::{IntentEngine, IntentUpdate, Regime};
use tracing::info;

/// Sovereign manifold observation snapshot
#[derive(Clone, Debug)]
pub struct ManifoldState {
    pub distance_to_ridge: f64,
    pub regime: Regime,
    pub current_d: f64,
    pub current_r: f64,
    pub current_sigma_t: f64,
    pub current_rho: f64,
    pub last_damped_value: f64,
    pub holonomy_norm: f64,      // placeholder for future retention
    pub sigma_floor: f64,        // invariant floor
}

/// Result of applying sovereign intent
#[derive(Clone, Debug)]
pub struct DampedIntent {
    pub original_value: f64,
    pub damped_value: f64,
    pub distance: f64,
    pub regime: Regime,
    pub band_id: String,
    pub reason: String,
}

/// Sovereign action receipt (closed-loop conservation)
#[derive(Clone, Debug)]
pub struct SovereignReceipt {
    pub action: String,
    pub timestamp: i64,
    pub manifold_state: ManifoldState,
    pub intent_applied: Option<DampedIntent>,
    pub note: String,
}

/// Unified Sovereign Operator — single control surface for the manifold
#[derive(Clone)]
pub struct SovereignOperator {
    engine: IntentEngine,
    gs_pressure: Arc<Mutex<f64>>,
    drift_ceiling: f64,
    sigma_floor: f64,
}

impl SovereignOperator {
    pub fn new() -> Self {
        Self {
            engine: IntentEngine::new(),
            gs_pressure: Arc::new(Mutex::new(1.0)),
            drift_ceiling: 8.0,
            sigma_floor: 0.0,
        }
    }

    // ============================================================
    // CORE SOVEREIGN INTERFACE
    // ============================================================

    /// Apply sovereign intent with automatic damping + GS bounding.
    /// This is the primary steering method.
    pub fn apply_intent(
        &self,
        band_id: String,
        intent_value: f64,
        d: f64,
        r: f64,
        sigma_t: f64,
        rho: f64,
        reason: String,
    ) -> DampedIntent {
        let update = IntentUpdate {
            band_id: band_id.clone(),
            intent_value,
            reason: reason.clone(),
            timestamp: crate::intent_engine::current_unix_timestamp(),
            ..Default::default()
        };

        // Route through the damped broadcast path
        self.engine.broadcast_update(update.clone(), d, r, sigma_t, rho);

        // Recompute for return value (engine already did the work)
        let distance = crate::intent_engine::BasinValidator::distance_to_ridge(d, r, sigma_t, rho);
        let damped_value = crate::intent_engine::BasinValidator::apply_damping(intent_value, distance);
        let regime = crate::intent_engine::BasinValidator::classify_regime(d, r, sigma_t, rho);

        let result = DampedIntent {
            original_value: intent_value,
            damped_value,
            distance,
            regime,
            band_id,
            reason,
        };

        info!(
            target: "sovereign::operator",
            action = "apply_intent",
            distance = distance,
            regime = ?regime,
            damped = damped_value,
            "Sovereign intent applied"
        );

        result
    }

    /// Set global GS pressure (affects future damping behavior)
    pub fn set_gs_pressure(&self, pressure: f64) {
        let mut p = self.gs_pressure.lock().unwrap();
        *p = pressure.clamp(0.0, 2.0);
        info!(target: "sovereign::operator", gs_pressure = pressure, "GS pressure updated");
    }

    pub fn get_gs_pressure(&self) -> f64 {
        *self.gs_pressure.lock().unwrap()
    }

    /// Observe current manifold state
    pub fn observe_manifold(&self, d: f64, r: f64, sigma_t: f64, rho: f64) -> ManifoldState {
        let distance = crate::intent_engine::BasinValidator::distance_to_ridge(d, r, sigma_t, rho);
        let regime = crate::intent_engine::BasinValidator::classify_regime(d, r, sigma_t, rho);

        ManifoldState {
            distance_to_ridge: distance,
            regime,
            current_d: d,
            current_r: r,
            current_sigma_t: sigma_t,
            current_rho: rho,
            last_damped_value: 0.0, // TODO: track last applied value
            holonomy_norm: 0.0,     // future: from GSState
            sigma_floor: self.sigma_floor,
        }
    }

    /// Inject a control pulse (placeholder for non-associative forcing)
    pub fn inject_pulse(&self, _pulse: String, _strength: f64) {
        // Future: non-associative forcing combiner
        info!(target: "sovereign::operator", "Pulse injection received (stub)");
    }

    /// Get current regime directly
    pub fn get_regime(&self, d: f64, r: f64, sigma_t: f64, rho: f64) -> Regime {
        crate::intent_engine::BasinValidator::classify_regime(d, r, sigma_t, rho)
    }

    /// Enforce drift ceiling (sovereign safety)
    pub fn enforce_drift_ceiling(&self, distance: f64) -> bool {
        distance <= self.drift_ceiling
    }

    // ============================================================
    // FUTURE EXTENSION POINTS (Planner / Walker / Critic / SP)
    // ============================================================

    // pub fn plan(&self, goal: SovereignGoal) -> SovereignPlan { ... }
    // pub fn walk(&self, plan: SovereignPlan) -> SovereignWalkResult { ... }
    // pub fn critique(&self, result: SovereignWalkResult) -> SovereignCritique { ... }
}