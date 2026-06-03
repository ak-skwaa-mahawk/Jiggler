impl<D> IntentEngine<D>
where
    D: IntentStorage + Send + Sync,
{
    pub fn heartbeat_step(&self, now_ms: i64, metrics: &SystemMetrics) -> Result<()> {
        let mut bands = self.db.load_all_bands()?;

        for band_state in &mut bands {
            let (drive, decay, safety) =
                self.compute_deltas(band_state, now_ms, metrics);

            let delta_i = drive - decay - safety;

            // Skip if change is negligible
            if delta_i.abs() < 1e-9 {
                continue;
            }

            let clamped_delta = self.clamp_delta(delta_i);
            if clamped_delta.abs() < 1e-9 {
                continue;
            }

            // Apply change to in-memory state
            band_state.intent_value = (band_state.intent_value + clamped_delta)
                .clamp(-self.params.imax_per_mode, self.params.imax_per_mode);
            band_state.lastupdatets = now_ms;

            let reason = self.reason_for_delta(drive, decay, safety);

            // === ATOMIC UPDATE + EVENT ===
            self.db.update_band_and_append_event(band_state, clamped_delta, reason)?;
        }

        Ok(())
    }

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
}