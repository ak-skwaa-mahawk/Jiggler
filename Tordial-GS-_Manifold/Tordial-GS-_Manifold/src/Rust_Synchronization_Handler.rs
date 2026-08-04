#[tonic::async_trait]
impl Manifold for ManifoldService {
    async fn synchronize(
        &self,
        request: tonic::Request<ManifoldTick>,
    ) -> Result<tonic::Response<SyncAck>, tonic::Status> {

        let tick = request.into_inner();

        // --- Economic artery ---
        if let Some(ev) = tick.economic_vector {
            self.handle_economic(ev, tick.ts_utc).await;
        }

        // --- Sap-flux artery ---
        if let Some(sf) = tick.sap_flux_vector {
            self.handle_sap_flux(sf, tick.ts_utc).await;
        }

        // --- Ledger entry ---
        self.ledger.append_tick(&tick).await;

        Ok(tonic::Response::new(SyncAck {
            status: "ok".into(),
        }))
    }
}