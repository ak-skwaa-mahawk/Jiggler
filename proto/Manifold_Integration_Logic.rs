impl ManifoldService {
    pub async fn handle_magnetic(
        &self,
        mv: MagneticVector,
        ts: i64,
    ) {
        // 1. Update canopy coherence model
        self.magnetic_state.update_field(mv.bx_n_t, mv.by_n_t, mv.bz_n_t);

        // 2. Feed variance into GS-band stability
        self.regime.update_from_magnetic(mv.variance_n_t);

        // 3. Use flux_delta as a micro-tick modulator
        self.clock.update_from_magnetic_flux(mv.flux_delta);

        // 4. Ledger entry
        self.ecology_state.record_magnetic(mv, ts);
    }
}