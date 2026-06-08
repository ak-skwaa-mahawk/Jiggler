cat << 'EOF' > build.rs
fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Compile the master proto layout into native Rust bindings
    tonic_build::configure()
        .compile(
            &["proto/combined_manifold.proto"],
            &["proto"],
        )?;
    Ok(())
}
EOF

cat > src/main.rs << 'ENDMAIN'
//! Tordial-GS Manifold — Minimal Working Entry Point
//! Clean build with IntentEngine + BasinValidator

use std::net::SocketAddr;

use tonic::{transport::Server, Request, Response, Status};
use tracing::info;

pub mod issttoft {
    tonic::include_proto!("issttoft");
}

mod intent_engine;
use intent_engine::{IntentEngine, BasinValidator, Regime};

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

    async fn stream_intent_updates(
        &self,
        _request: Request<StreamIntentUpdatesRequest>,
    ) -> Result<Response<Self::StreamIntentUpdatesStream>, Status> {
        Err(Status::unimplemented("Streaming not yet wired in this minimal build"))
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

    // Demo: show basin validator working
    let distance = BasinValidator::distance_to_ridge(27.0, 155.0, 60.0, 0.325);
    let regime = BasinValidator::classify_regime(27.0, 155.0, 60.0, 0.325);
    info!(
        "Basin check → distance_to_ridge = {:.2}, regime = {:?}",
        distance, regime
    );

    let addr: SocketAddr = "0.0.0.0:50051".parse()?;
    info!("🔥 Tordial-GS Manifold listening on {}", addr);

    Server::builder()
        .add_service(InferenceServiceServer::new(service))
        .serve(addr)
        .await?;

    Ok(())
}
ENDMAIN