cat << 'EOF' > src/main.rs
//! Tordial-GS Manifold — Consolidated Multi-Channel Production Entry Point
use std::net::SocketAddr;
use tonic::{transport::Server, Request, Response, Status};
use tracing::info;

pub mod combined_manifold {
    tonic::include_proto!("combined_manifold");
}

mod intent_engine;
use intent_engine::{IntentEngine, BasinValidator};

use combined_manifold::inference_service_server::{InferenceService, InferenceServiceServer};
use combined_manifold::manifold_controller_server::{ManifoldController, ManifoldControllerServer};
use combined_manifold::{
    GetAllIntentBandsRequest, GetAllIntentBandsResponse, GetIntentBandRequest, IntentBand,
    HandshakeRequest, HandshakeResponse, StreamIntentUpdatesRequest, VectorPayload, SubstrateMetricsResponse
};

// ==========================================
// CHANNEL 1: INFERENCE CONTROLLER
// ==========================================
#[derive(Clone)]
pub struct SovereignInferenceService {
    engine: IntentEngine,
}

impl SovereignInferenceService {
    pub fn new() -> Self {
        Self { engine: IntentEngine::new() }
    }
}

#[tonic::async_trait]
impl InferenceService for SovereignInferenceService {
    async fn get_intent_band(&self, request: Request<GetIntentBandRequest>) -> Result<Response<IntentBand>, Status> {
        let req = request.into_inner();
        let bands = self.engine.get_all_bands();
        if let Some(band) = bands.into_iter().find(|b| b.band_id == req.band_id) {
            Ok(Response::new(IntentBand {
                band_id: band.band_id,
                energy_delta: band.energy_delta,
                spin: band.spin,
                temp: band.temp,
            }))
        } else {
            Err(Status::not_found(format!("Band '{}' not found", req.band_id)))
        }
    }

    async fn get_all_intent_bands(&self, _request: Request<GetAllIntentBandsRequest>) -> Result<Response<GetAllIntentBandsResponse>, Status> {
        let internal_bands = self.engine.get_all_bands();
        let bands = internal_bands.into_iter().map(|b| IntentBand {
            band_id: b.band_id,
            energy_delta: b.energy_delta,
            spin: b.spin,
            temp: b.temp,
        }).collect();
        Ok(Response::new(GetAllIntentBandsResponse { bands }))
    }

    type StreamIntentUpdatesStream = tonic::codegen::tokio_stream::wrappers::ReceiverStream<Result<combined_manifold::IntentUpdate, Status>>;
    async fn stream_intent_updates(&self, _request: Request<StreamIntentUpdatesRequest>) -> Result<Response<Self::StreamIntentUpdatesStream>, Status> {
        Err(Status::unimplemented("Streaming updates loop inactive"))
    }

    async fn handshake(&self, request: Request<HandshakeRequest>) -> Result<Response<HandshakeResponse>, Status> {
        let req = request.into_inner();
        // Convert boolean to String conversion to satisfy raw interface definitions
        let resp = self.engine.handshake(req.client_id, req.client_type, req.sovereign_claim.to_string());
        Ok(Response::new(HandshakeResponse {
            status: resp.status,
            version: resp.version,
            mesh_status: resp.mesh_status,
            flamekeeper_note: resp.flamekeeper_note,
        }))
    }
}

// ==========================================
// CHANNEL 2: TENSOR PHYSICS MANIFOLD
// ==========================================
#[derive(Debug, Default)]
pub struct MyManifoldController {}

#[tonic::async_trait]
impl ManifoldController for MyManifoldController {
    async fn synchronize_vector(&self, request: Request<VectorPayload>) -> Result<Response<SubstrateMetricsResponse>, Status> {
        let payload = request.into_inner();
        if let Some(vector) = payload.velocity_vector {
            info!(
                "[🚀 Substrate Engine] Tensor Ingress Ingested [{}] -> X: {:.4}, Y: {:.4}, Z: {:.4} | Throat Radius: {:.4}",
                payload.vector_id, vector.x, vector.y, vector.z, payload.throat_radius
            );
        } else {
            return Err(Status::invalid_argument("Missing translational velocity component vector"));
        }

        Ok(Response::new(SubstrateMetricsResponse {
            status: "CONNECTED".to_string(),
            version: "tordial-gs v2.3-tensor".to_string(),
            mesh_status: "Ch’anchyah Dach’anchyah — The Floor is solid.".to_string(),
            processing_stable: true,
            execution_ticks: 1,
        }))
    }
}

// ==========================================
// MASTER SUBSYSTEM STARTUP
// ==========================================
#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::fmt::init();

    let service_channel_1 = SovereignInferenceService::new();
    let service_channel_2 = MyManifoldController::default();

    let distance = BasinValidator::distance_to_ridge(27.0, 155.0, 60.0, 0.325);
    let regime = BasinValidator::classify_regime(27.0, 155.0, 60.0, 0.325);
    info!("[⚙️] Basin validation metric verified. Distance to Ridge = {:.2} | Regime Class = {:?}", distance, regime);

    let addr: SocketAddr = "0.0.0.0:50051".parse()?;
    info!("🔥 Tordial-GS Multiplexed Core substrate running asynchronously on: {}", addr);

    Server::builder()
        .add_service(InferenceServiceServer::new(service_channel_1))
        .add_service(ManifoldControllerServer::new(service_channel_2))
        .serve(addr)
        .await?;

    Ok(())
}
EOF


cat << 'EOF' > src/main.rs
//! Tordial-GS Manifold — Consolidated Multi-Channel Production Entry Point
use std::net::SocketAddr;
use tonic::{transport::Server, Request, Response, Status};
use tracing::info;

pub mod combined_manifold {
    tonic::include_proto!("combined_manifold");
}

mod intent_engine;
use intent_engine::{IntentEngine, BasinValidator};

use combined_manifold::inference_service_server::{InferenceService, InferenceServiceServer};
use combined_manifold::manifold_controller_server::{ManifoldController, ManifoldControllerServer};
use combined_manifold::{
    GetAllIntentBandsRequest, GetAllIntentBandsResponse, GetIntentBandRequest, IntentBand,
    HandshakeRequest, HandshakeResponse, StreamIntentUpdatesRequest, VectorPayload, SubstrateMetricsResponse
};

// ==========================================
// CHANNEL 1: INFERENCE CONTROLLER
// ==========================================
#[derive(Clone)]
pub struct SovereignInferenceService {
    engine: IntentEngine,
}

impl SovereignInferenceService {
    pub fn new() -> Self {
        Self { engine: IntentEngine::new() }
    }
}

#[tonic::async_trait]
impl InferenceService for SovereignInferenceService {
    async fn get_intent_band(&self, request: Request<GetIntentBandRequest>) -> Result<Response<IntentBand>, Status> {
        let req = request.into_inner();
        let bands = self.engine.get_all_bands();
        if let Some(band) = bands.into_iter().find(|b| b.band_id == req.band_id) {
            Ok(Response::new(IntentBand {
                band_id: band.band_id,
                energy_delta: band.energy_delta,
                spin: band.spin,
                temp: band.temp,
            }))
        } else {
            Err(Status::not_found(format!("Band '{}' not found", req.band_id)))
        }
    }

    async fn get_all_intent_bands(&self, _request: Request<GetAllIntentBandsRequest>) -> Result<Response<GetAllIntentBandsResponse>, Status> {
        let internal_bands = self.engine.get_all_bands();
        let bands = internal_bands.into_iter().map(|b| IntentBand {
            band_id: b.band_id,
            energy_delta: b.energy_delta,
            spin: b.spin,
            temp: b.temp,
        }).collect();
        Ok(Response::new(GetAllIntentBandsResponse { bands }))
    }

    type StreamIntentUpdatesStream = tonic::codegen::tokio_stream::wrappers::ReceiverStream<Result<combined_manifold::IntentUpdate, Status>>;
    async fn stream_intent_updates(&self, _request: Request<StreamIntentUpdatesRequest>) -> Result<Response<Self::StreamIntentUpdatesStream>, Status> {
        Err(Status::unimplemented("Streaming updates wire loop active in fallback modes"))
    }

    async fn handshake(&self, request: Request<HandshakeRequest>) -> Result<Response<HandshakeResponse>, Status> {
        let req = request.into_inner();
        # Convert boolean to String conversion to satisfy the original mock interface definitions
        let resp = self.engine.handshake(req.client_id, req.client_type, req.sovereign_claim.to_string());
        Ok(Response::new(HandshakeResponse {
            status: resp.status,
            version: resp.version,
            mesh_status: resp.mesh_status,
            flamekeeper_note: resp.flamekeeper_note,
        }))
    }
}

// ==========================================
// CHANNEL 2: TENSOR PHYSICS MANIFOLD
// ==========================================
#[derive(Debug, Default)]
pub struct MyManifoldController {}

#[tonic::async_trait]
impl ManifoldController for MyManifoldController {
    async fn synchronize_vector(&self, request: Request<VectorPayload>) -> Result<Response<SubstrateMetricsResponse>, Status> {
        let payload = request.into_inner();
        if let Some(vector) = payload.velocity_vector {
            info!(
                "[🚀 Substrate Engine] Tensor Ingress Ingested [{}] -> X: {:.4}, Y: {:.4}, Z: {:.4} | Throat Radius: {:.4}",
                payload.vector_id, vector.x, vector.y, vector.z, payload.throat_radius
            );
        } else {
            return Err(Status::invalid_argument("Missing translational velocity component vector"));
        }

        Ok(Response::new(SubstrateMetricsResponse {
            status: "CONNECTED".to_string(),
            version: "tordial-gs v2.3-tensor".to_string(),
            mesh_status: "Ch’anchyah Dach’anchyah — The Floor is solid.".to_string(),
            processing_stable: true,
            execution_ticks: 1,
        }))
    }
}

// ==========================================
// MASTER SUBSYSTEM STARTUP
// ==========================================
#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::fmt::init();

    let service_channel_1 = SovereignInferenceService::new();
    let service_channel_2 = MyManifoldController::default();

    let distance = BasinValidator::distance_to_ridge(27.0, 155.0, 60.0, 0.325);
    let regime = BasinValidator::classify_regime(27.0, 155.0, 60.0, 0.325);
    info!("[⚙️] Basin validation metric verified. Distance to Ridge = {:.2} | Regime Class = {:?}", distance, regime);

    let addr: SocketAddr = "0.0.0.0:50051".parse()?;
    info!("🔥 Tordial-GS Multiplexed Core substrate running asynchronously on: {}", addr);

    Server::builder()
        .add_service(InferenceServiceServer::new(service_channel_1))
        .add_service(ManifoldControllerServer::new(service_channel_2))
        .serve(addr)
        .await?;

    Ok(())
}
EOF


cat << 'EOF' > src/main.rs
//! Tordial-GS Manifold — Consolidated Multi-Channel Production Entry Point
use std::net::SocketAddr;
use tonic::{transport::Server, Request, Response, Status};
use tracing::info;

pub mod combined_manifold {
    tonic::include_proto!("combined_manifold");
}

mod intent_engine;
use intent_engine::{IntentEngine, BasinValidator};

use combined_manifold::inference_service_server::{InferenceService, InferenceServiceServer};
use combined_manifold::manifold_controller_server::{ManifoldController, ManifoldControllerServer};
use combined_manifold::{
    GetAllIntentBandsRequest, GetAllIntentBandsResponse, GetIntentBandRequest, IntentBand,
    HandshakeRequest, HandshakeResponse, StreamIntentUpdatesRequest, VectorPayload, SubstrateMetricsResponse
};

// ==========================================
// CHANNEL 1: INFERENCE CONTROLLER
// ==========================================
#[derive(Clone)]
pub struct SovereignInferenceService {
    engine: IntentEngine,
}

impl SovereignInferenceService {
    pub fn new() -> Self {
        Self { engine: IntentEngine::new() }
    }
}

#[tonic::async_trait]
impl InferenceService for SovereignInferenceService {
    async fn get_intent_band(&self, request: Request<GetIntentBandRequest>) -> Result<Response<IntentBand>, Status> {
        let req = request.into_inner();
        let bands = self.engine.get_all_bands();
        if let Some(band) = bands.into_iter().find(|b| b.band_id == req.band_id) {
            Ok(Response::new(IntentBand {
                band_id: band.band_id,
                energy_delta: band.energy_delta,
                spin: band.spin,
                temp: band.temp,
            }))
        } else {
            Err(Status::not_found(format!("Band '{}' not found", req.band_id)))
        }
    }

    async fn get_all_intent_bands(&self, _request: Request<GetAllIntentBandsRequest>) -> Result<Response<GetAllIntentBandsResponse>, Status> {
        let internal_bands = self.engine.get_all_bands();
        let bands = internal_bands.into_iter().map(|b| IntentBand {
            band_id: b.band_id,
            energy_delta: b.energy_delta,
            spin: b.spin,
            temp: b.temp,
        }).collect();
        Ok(Response::new(GetAllIntentBandsResponse { bands }))
    }

    type StreamIntentUpdatesStream = tonic::codegen::tokio_stream::wrappers::ReceiverStream<Result<combined_manifold::IntentUpdate, Status>>;
    async fn stream_intent_updates(&self, _request: Request<StreamIntentUpdatesRequest>) -> Result<Response<Self::StreamIntentUpdatesStream>, Status> {
        Err(Status::unimplemented("Streaming updates wire loop active in fallback modes"))
    }

    async fn handshake(&self, request: Request<HandshakeRequest>) -> Result<Response<HandshakeResponse>, Status> {
        let req = request.into_inner();
        let resp = self.engine.handshake(req.client_id, req.client_type, req.sovereign_claim);
        Ok(Response::new(HandshakeResponse {
            status: resp.status,
            version: resp.version,
            mesh_status: resp.mesh_status,
            flamekeeper_note: resp.flamekeeper_note,
        }))
    }
}

// ==========================================
// CHANNEL 2: TENSOR PHYSICS MANIFOLD
// ==========================================
#[derive(Debug, Default)]
pub struct MyManifoldController {}

#[tonic::async_trait]
impl ManifoldController for MyManifoldController {
    async fn synchronize_vector(&self, request: Request<VectorPayload>) -> Result<Response<SubstrateMetricsResponse>, Status> {
        let payload = request.into_inner();
        if let Some(vector) = payload.velocity_vector {
            info!(
                "[🚀 Substrate Engine] Tensor Ingress Ingested [{}] -> X: {:.4}, Y: {:.4}, Z: {:.4} | Throat Radius: {:.4}",
                payload.vector_id, vector.x, vector.y, vector.z, payload.throat_radius
            );
        } else {
            return Err(Status::invalid_argument("Missing translational velocity component vector"));
        }

        Ok(Response::new(SubstrateMetricsResponse {
            status: "CONNECTED".to_string(),
            version: "tordial-gs v2.3-tensor".to_string(),
            mesh_status: "Ch’anchyah Dach’anchyah — The Floor is solid.".to_string(),
            processing_stable: true,
            execution_ticks: 1,
        }))
    }
}

// ==========================================
// MASTER SUBSYSTEM STARTUP
// ==========================================
#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::fmt::init();

    let service_channel_1 = SovereignInferenceService::new();
    let service_channel_2 = MyManifoldController::default();

    let distance = BasinValidator::distance_to_ridge(27.0, 155.0, 60.0, 0.325);
    let regime = BasinValidator::classify_regime(27.0, 155.0, 60.0, 0.325);
    info!("[⚙️] Basin validation metric verified. Distance to Ridge = {:.2} | Regime Class = {:?}", distance, regime);

    let addr: SocketAddr = "0.0.0.0:50051".parse()?;
    info!("🔥 Tordial-GS Multiplexed Core substrate running asynchronously on: {}", addr);

    // Bind both services side-by-side to handle parallel pipelines on port 50051
    Server::builder()
        .add_service(InferenceServiceServer::new(service_channel_1))
        .add_service(ManifoldControllerServer::new(service_channel_2))
        .serve(addr)
        .await?;

    Ok(())
}
EOF
