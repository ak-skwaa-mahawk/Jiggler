impl SqliteIntentStore {
    pub fn update_band_and_append_event(
        &self,
        band: &IntentBandState,
        delta: f64,
        reason: IntentReason,
    ) -> Result<()> {
        let tx = self.conn.unchecked_transaction()?;

        // update band
        tx.execute(
            "...", // same as update_band above
            params![...],
        )?;

        // append event
        tx.execute(
            "...", // same as append_event above
            params![...],
        )?;

        tx.commit()?;
        Ok(())
    }
}