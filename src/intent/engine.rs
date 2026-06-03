// src/intent/engine.rs
// Complete Intent Engine — Medium coupling with Tordial-GS

use super::storage::IntentStorage;
use super::types::{
    IntentBandId, IntentBandState, IntentParams, IntentReason, ModeId, SystemMetrics,
};
use anyhow::Result;

pub struct IntentEngine<D> {
    db: D,
    params: IntentParams,
}

impl<D> IntentEngine<D>
where
    D: IntentStorage + Send + Sync,
{
    pub fn new(db: D, params: IntentParams) -> Self {
        Self { db, params }
    }

    /// Main heartbeat step — call this periodically from your decision plane
    pub fn heartbeat_step(&self, now_ms: i64, metrics: &SystemMetrics) -> Result<()> {
        let mut bands = self.db.load_all_bands()?;

        for band_state in &mut bands {
            let (drive, decay, safety) =
                self.compute_deltas(band_state, now_ms, metrics);

            let delta_i = drive - decay - safety;

            if delta_i.abs() < 1e-9 {
                continue;
            }

            let clamped_delta = self.clamp_delta(delta_i);
            if clamped_delta.abs() < 1e-9 {
                continue;
            }

            // Apply change
            band_state.intent_value = (band_state.intent_value + clamped_delta)
                .clamp(-self.params.imax_per_mode, self.params.imax_per_mode);
            band_state.lastupdatets = now_ms;

            let reason = self.reason_for_delta(drive, decay, safety);

            // Atomic update + event log
            self.db.update_band_and_append_event(band_state, clamped_delta, reason)?;
        }

        Ok(())
    }

    // ==================== PRIVATE HELPERS ====================

    fn clamp_delta(&self, delta: f64) -> f64 {
        delta.clamp(-self.params.didt_max, self.params.didt_max)
    }

    fn reason_for_delta(&self, drive: f64, decay: f64, safety: f64) -> IntentReason {
        if safety > 0.0 {
            IntentReason::Safety
        } else if drive > decay {
            IntentReason::Drive
        } else {
            IntentReason::Decay
        }
    }

    fn compute_deltas(
        &self,
        band: &IntentBandState,
        now_ms: i64,
        metrics: &SystemMetrics,
    ) -> (f64, f64, f64) {
        let dt_ms = (now_ms - band.lastupdatets).max(0) as f64;

        // Decay (exponential toward 0)
        let halflife = self.params.decay_halflife_ms as f64;
        let lambda = (2.0_f64.ln() / halflife).max(1e-12);
        let decay = band.intent_value.abs() * (1.0 - (-lambda * dt_ms).exp());

        let drive = self.compute_drive_for_band(band, metrics, dt_ms);
        let safety = self.compute_safety_for_band(band, metrics, dt_ms);

        (drive, decay, safety)
    }

    fn compute_drive_for_band(
        &self,
        band: &IntentBandState,
        metrics: &SystemMetrics,
        dt_ms: f64,
    ) -> f64 {
        match band.band.0.as_str() {
            "safety.checkpoints" => 0.12 * metrics.error_rate * dt_ms,
            "resonance.drive" => 0.08 * metrics.load_factor * dt_ms,
            "curvature.stability" => 0.06 * metrics.gs_curvature * dt_ms,
            "energy.governor" => 0.10 * (100.0 - metrics.energy_level).max(0.0) * dt_ms,
            "fission.control" => 0.07 * metrics.load_factor * dt_ms,
            "observer.flame" => 0.05 * metrics.error_rate * dt_ms,
            _ => 0.0,
        }
    }

    fn compute_safety_for_band(
        &self,
        band: &IntentBandState,
        metrics: &SystemMetrics,
        dt_ms: f64,
    ) -> f64 {
        // Never suppress safety bands
        if band.band.0.starts_with("safety.") {
            return 0.0;
        }

        let mut suppression = 0.0;

        // High curvature suppression
        if metrics.gs_curvature > 0.85 {
            suppression += 0.25 * (metrics.gs_curvature - 0.85) * dt_ms;
        }

        // Low energy suppression
        if metrics.energy_level < 80.0 {
            suppression += 0.18 * (80.0 - metrics.energy_level) * dt_ms;
        }

        // High load suppression
        if metrics.load_factor > 0.9 {
            suppression += 0.12 * (metrics.load_factor - 0.9) * dt_ms;
        }

        suppression
    }
}