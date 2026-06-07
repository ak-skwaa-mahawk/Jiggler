impl SqliteIntentStore {
    pub fn update_band_and_append_event(
        &self,
        band: &IntentBandState,
        delta_i: f64,
        reason: IntentReason,
    ) -> Result<()> {
        let tx = self.conn.unchecked_transaction()?;

        // Update current intent state
        tx.execute(
            r#"
            INSERT INTO intent_band (id, mode, intent_value, lastupdatets, source)
            VALUES (?1, ?2, ?3, ?4, ?5)
            ON CONFLICT(id, mode) DO UPDATE SET
                intent_value = excluded.intent_value,
                lastupdatets = excluded.lastupdatets,
                source       = excluded.source
            "#,
            params![
                band.band.0,
                band.mode.0,
                band.intent_value,
                band.lastupdatets,
                band.source
            ],
        )?;

        // Append to causal log
        tx.execute(
            r#"
            INSERT INTO intent_event (ts, band, mode, delta_I, reason, meta)
            VALUES (?1, ?2, ?3, ?4, ?5, '{}')
            "#,
            params![
                band.lastupdatets,
                band.band.0,
                band.mode.0,
                delta_i,
                reason.as_str()
            ],
        )?;

        tx.commit()?;
        Ok(())
    }
}