let mut rx = self.engine.subscribe();

let output_stream = async_stream::stream! {
    loop {
        match rx.recv().await {
            Ok(update) => yield Ok(update),
            Err(broadcast::error::RecvError::Lagged(skipped)) => {
                warn!(target: "isst_toft::intent", "Client lagged — skipped {} updates", skipped);
                continue;
            }
            Err(broadcast::error::RecvError::Closed) => break,
        }
    }
};

Ok(Response::new(Box::pin(output_stream)))
async fn stream_intent_updates(
    &self,
    _request: Request<StreamIntentUpdatesRequest>,
) -> Result<Response<Self::StreamIntentUpdatesStream>, Status> {
    info!(target: "isst_toft::intent", "New client subscribed to StreamIntentUpdates (broadcast)");

    let mut rx = self.intent_tx.subscribe();

    let output_stream = stream! {
        loop {
            match rx.recv().await {
                Ok(update) => yield Ok(update),
                Err(broadcast::error::RecvError::Lagged(skipped)) => {
                    warn!(target: "isst_toft::intent", "Client lagged — skipped {} updates", skipped);
                    continue;
                }
                Err(broadcast::error::RecvError::Closed) => break,
            }
        }
    };

    Ok(Response::new(Box::pin(output_stream)))
}