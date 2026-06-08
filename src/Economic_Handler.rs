impl ManifoldService {
    pub async fn handle_economic(
        &self,
        ev: EconomicVector,
        ts: i64,
    ) {
        self.econ_state.update(ev, ts);
        self.regime.update_from_economics(ev);
    }
}