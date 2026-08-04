impl ManifoldService {
    pub async fn handle_sap_flux(
        &self,
        sf: SapFluxVector,
        ts: i64,
    ) {
        let fm = sf.fm_norm;

        // Update manifold clock
        self.clock.update_from_flux(fm);

        // Feed GS-band selector
        self.regime.update_from_flux(fm);

        // Store ecological pulse
        self.ecology_state.record_flux(sf, ts);
    }
}