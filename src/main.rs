//! Tordial-GS Manifold — Clean Production Entry Point
//! Integrates synchronized gRPC services with broadcast-damped intent tracking

use std::net::SocketAddr;
use tonic::{transport::Server, Request, Response, Status};
use tracing::info;

pub mod issttoft {
    tonic::include_proto!("issttoft");
}

mod intent_engine;
use intent_engine::{IntentEngine, BasinValidator};

use issttoft::{
    inference_service_server::{InferenceService, InferenceServiceServer},
    GetAllIntentBandsRequest, GetAllIntentBandsResponse,
    GetIntentBandRequest, IntentBand,
    HandshakeRequest, HandshakeResponse,
    StreamIntentUpdatesRequest,
};

#[derive(Clone)]
pub struct SovereignInferenceService {
    engine: IntentEngine,
}

impl SovereignInferenceService {
    pub fn new() -> Self {
        Self {
            engine: IntentEngine::new(),
        }
    }
}

#[tonic::async_trait]
impl InferenceService for SovereignInferenceService {
    async fn get_intent_band(
        &self,
        request: Request<GetIntentBandRequest>,
    ) -> Result<Response<IntentBand>, Status> {
        let req = request.into_inner();
        let bands = self.engine.get_all_bands();
        if let Some(band) = bands.into_iter().find(|b| b.band_id == req.band_id) {
            Ok(Response::new(band))
        } else {
            Err(Status::not_found(format!("Band '{}' not found", req.band_id)))
        }
    }

    async fn get_all_intent_bands(
        &self,
        _request: Request<GetAllIntentBandsRequest>,
    ) -> Result<Response<GetAllIntentBandsResponse>, Status> {
        let bands = self.engine.get_all_bands();
        Ok(Response::new(GetAllIntentBandsResponse { bands }))
    }

    type StreamIntentUpdatesStream = tonic::codegen::tokio_stream::wrappers::ReceiverStream<
        Result<issttoft::IntentUpdate, Status>
    >;

    async fn stream_intent_updates(
        &self,
        _request: Request<StreamIntentUpdatesRequest>,
    ) -> Result<Response<Self::StreamIntentUpdatesStream>, Status> {
        Err(Status::unimplemented("Streaming updates wire loop coming up next"))
    }

    async fn handshake(
        &self,
        request: Request<HandshakeRequest>,
    ) -> Result<Response<HandshakeResponse>, Status> {
        let req = request.into_inner();
        let response = self.engine.handshake(req.client_id, req.client_type, req.sovereign_claim);
        Ok(Response::new(response))
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::fmt::init();

    let service = SovereignInferenceService::new();

    // Verify system telemetry classification math runs smoothly on initialization
    let distance = BasinValidator::distance_to_ridge(27.0, 155.0, 60.0, 0.325);
    let regime = BasinValidator::classify_regime(27.0, 155.0, 60.0, 0.325);
    info!(
        "[⚙️] Basin validation metric verified. Distance to Ridge = {:.2} | Regime Class = {:?}",
        distance, regime
    );

    let addr: SocketAddr = "0.0.0.0:50051".parse()?;
    info!("🔥 Tordial-GS Manifold asynchronous microservice listening on: {}", addr);

    Server::builder()
        .add_service(InferenceServiceServer::new(service))
        .serve(addr)
        .await?;

    Ok(())
}
