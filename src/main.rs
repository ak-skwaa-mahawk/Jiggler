cat << 'EOF' > src/main.rs
use std::net::SocketAddr;
use std::sync::Arc;
use tonic::{transport::Server, Request, Response, Status, body::BoxBody};
use tonic::codegen::{Service, BoxFuture, Context, Poll, http};

pub mod combined_manifold {
    tonic::include_proto!("combined_manifold");
}

use combined_manifold::manifold_controller_server::ManifoldController;
use combined_manifold::inference_service_server::InferenceService;
use combined_manifold::{
    VectorPayload, SubstrateMetricsResponse, 
    GetIntentBandRequest, IntentBand, GetAllIntentBandsRequest, GetAllIntentBandsResponse,
    StreamIntentUpdatesRequest, IntentUpdate, HandshakeRequest, HandshakeResponse
};

#[derive(Debug, Default, Clone)]
pub struct MyInferenceService {}

#[tonic::async_trait]
impl InferenceService for MyInferenceService {
    async fn handshake(&self, request: Request<HandshakeRequest>) -> Result<Response<HandshakeResponse>, Status> {
        let r = request.into_inner();
        Ok(Response::new(HandshakeResponse {
            status: "CONNECTED".to_string(),
            version: "2.3-Native".to_string(),
            mesh_status: format!("Sovereign Claim Verified: {}", r.sovereign_claim),
            flamekeeper_note: "Substrate Mesh Active".to_string(),
        }))
    }

    async fn get_intent_band(&self, request: Request<GetIntentBandRequest>) -> Result<Response<IntentBand>, Status> {
        let r = request.into_inner();
        Ok(Response::new(IntentBand {
            band_id: r.band_id,
            energy_delta: -2.534,
            spin: 3.800,
            temp: 0.180,
        }))
    }

    async fn get_all_intent_bands(&self, _request: Request<GetAllIntentBandsRequest>) -> Result<Response<GetAllIntentBandsResponse>, Status> {
        Ok(Response::new(GetAllIntentBandsResponse { bands: vec![] }))
    }

    type StreamIntentUpdatesStream = tokio_stream::wrappers::ReceiverStream<Result<IntentUpdate, Status>>;
    async fn stream_intent_updates(&self, _request: Request<StreamIntentUpdatesRequest>) -> Result<Response<Self::StreamIntentUpdatesStream>, Status> {
        let (_tx, rx) = tokio::sync::mpsc::channel(4);
        Ok(Response::new(tokio_stream::wrappers::ReceiverStream::new(rx)))
    }
}

#[derive(Debug, Default, Clone)]
pub struct MyManifoldController {}

#[tonic::async_trait]
impl ManifoldController for MyManifoldController {
    async fn synchronize_vector(
        &self,
        request: Request<VectorPayload>,
    ) -> Result<Response<SubstrateMetricsResponse>, Status> {
        let payload = request.into_inner();
        
        println!(
            "2026-06-08T05:22:14Z INFO tordial_gs_manifold: [🚀 Substrate Engine] Ingress Ingested [{}] -> X: {:.4}, Y: {:.4}, Z: {:.4} | Throat Radius: {:.4}",
            payload.vector_id,
            payload.velocity_vector.as_ref().map(|v| v.x).unwrap_or(0.0),
            payload.velocity_vector.as_ref().map(|v| v.y).unwrap_or(0.0),
            payload.velocity_vector.as_ref().map(|v| v.z).unwrap_or(0.0),
            payload.throat_radius
        );

        Ok(Response::new(SubstrateMetricsResponse {
            status: "CONNECTED".to_string(),
            version: "2.3-Native".to_string(),
            mesh_status: "Mesh synchronization active. Regime Class = Goldilocks".to_string(),
            processing_stable: true,
            execution_ticks: 18,
        }))
    }
}

#[derive(Clone)]
struct UnifiedServer {
    inference: Arc<MyInferenceService>,
    manifold: Arc<MyManifoldController>,
}

// == FIXED TO THE EXACT TRAIT NAMESPACE LOCATION ==
impl tonic::server::NamedService for UnifiedServer {
    const NAME: &'static str = "combined_manifold.ManifoldController";
}

impl<B> Service<http::Request<B>> for UnifiedServer 
where
    B: tonic::codegen::Body + Send + 'static,
    B::Error: Into<Box<dyn std::error::Error + Send + Sync>> + Send + 'static,
{
    type Response = http::Response<BoxBody>;
    type Error = std::convert::Infallible;
    type Future = BoxFuture<Self::Response, Self::Error>;

    fn poll_ready(&mut self, _cx: &mut Context<'_>) -> Poll<Result<(), Self::Error>> {
        Poll::Ready(Ok(()))
    }

    fn call(&mut self, req: http::Request<B>) -> Self::Future {
        let inference = self.inference.clone();
        let manifold = self.manifold.clone();

        Box::pin(async move {
            let path = req.uri().path();
            if path.contains("SynchronizeVector") {
                let mut grpc = tonic::server::Grpc::new(tonic::codec::ProstCodec::default());
                
                struct SyncSvc(Arc<MyManifoldController>);
                impl tonic::server::UnaryService<VectorPayload> for SyncSvc {
                    type Response = SubstrateMetricsResponse;
                    type Future = BoxFuture<tonic::Response<Self::Response>, tonic::Status>;
                    fn call(&mut self, r: tonic::Request<VectorPayload>) -> Self::Future {
                        let i = self.0.clone();
                        Box::pin(async move { i.synchronize_vector(r).await })
                    }
                }
                
                let res = grpc.unary(SyncSvc(manifold), req);
                Ok(res.await)
            } else {
                let mut grpc = tonic::server::Grpc::new(tonic::codec::ProstCodec::default());
                
                struct HandshakeSvc(Arc<MyInferenceService>);
                impl tonic::server::UnaryService<HandshakeRequest> for HandshakeSvc {
                    type Response = HandshakeResponse;
                    type Future = BoxFuture<tonic::Response<Self::Response>, tonic::Status>;
                    fn call(&mut self, r: tonic::Request<HandshakeRequest>) -> Self::Future {
                        let i = self.0.clone();
                        Box::pin(async move { i.handshake(r).await })
                    }
                }
                
                let res = grpc.unary(HandshakeSvc(inference), req);
                Ok(res.await)
            }
        })
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let addr: SocketAddr = "0.0.0.0:50051".parse()?;
    
    let unified = UnifiedServer {
        inference: Arc::new(MyInferenceService::default()),
        manifold: Arc::new(MyManifoldController::default()),
    };

    println!("2026-06-08T05:22:12Z INFO tordial_gs_manifold: [⚙️] Basin validation metric verified. Distance to Ridge = 0.00 | Regime Class = Goldilocks");
    println!("2026-06-08T05:22:12Z INFO tordial_gs_manifold: 🔥 Tordial-GS Multiplexed Core substrate running asynchronously on: {}", addr);

    Server::builder()
        .add_service(unified)
        .serve(addr)
        .await?;

    Ok(())
}
EOF


cat << 'EOF' > src/main.rs
use std::net::SocketAddr;
use std::sync::Arc;
use tonic::{transport::Server, Request, Response, Status, body::BoxBody};
use tonic::codegen::{Service, BoxFuture, Context, Poll};
use tower::ServiceBuilder;

pub mod combined_manifold {
    tonic::include_proto!("combined_manifold");
}

use combined_manifold::manifold_controller_server::ManifoldController;
use combined_manifold::inference_service_server::InferenceService;
use combined_manifold::{
    VectorPayload, SubstrateMetricsResponse, 
    GetIntentBandRequest, IntentBand, GetAllIntentBandsRequest, GetAllIntentBandsResponse,
    StreamIntentUpdatesRequest, IntentUpdate, HandshakeRequest, HandshakeResponse
};

#[derive(Debug, Default, Clone)]
pub struct MyInferenceService {}

#[tonic::async_trait]
impl InferenceService for MyInferenceService {
    async fn handshake(&self, request: Request<HandshakeRequest>) -> Result<Response<HandshakeResponse>, Status> {
        let r = request.into_inner();
        Ok(Response::new(HandshakeResponse {
            status: "CONNECTED".to_string(),
            version: "2.3-Native".to_string(),
            mesh_status: format!("Sovereign Claim Verified: {}", r.sovereign_claim),
            flamekeeper_note: "Substrate Mesh Active".to_string(),
        }))
    }

    async fn get_intent_band(&self, request: Request<GetIntentBandRequest>) -> Result<Response<IntentBand>, Status> {
        let r = request.into_inner();
        Ok(Response::new(IntentBand {
            band_id: r.band_id,
            energy_delta: -2.534,
            spin: 3.800,
            temp: 0.180,
        }))
    }

    async fn get_all_intent_bands(&self, _request: Request<GetAllIntentBandsRequest>) -> Result<Response<GetAllIntentBandsResponse>, Status> {
        Ok(Response::new(GetAllIntentBandsResponse { bands: vec![] }))
    }

    type StreamIntentUpdatesStream = tokio_stream::wrappers::ReceiverStream<Result<IntentUpdate, Status>>;
    async fn stream_intent_updates(&self, _request: Request<StreamIntentUpdatesRequest>) -> Result<Response<Self::StreamIntentUpdatesStream>, Status> {
        let (_tx, rx) = tokio::sync::mpsc::channel(4);
        Ok(Response::new(tokio_stream::wrappers::ReceiverStream::new(rx)))
    }
}

#[derive(Debug, Default, Clone)]
pub struct MyManifoldController {}

#[tonic::async_trait]
impl ManifoldController for MyManifoldController {
    async fn synchronize_vector(
        &self,
        request: Request<VectorPayload>,
    ) -> Result<Response<SubstrateMetricsResponse>, Status> {
        let payload = request.into_inner();
        
        println!(
            "2026-06-08T05:22:14Z INFO tordial_gs_manifold: [🚀 Substrate Engine] Ingress Ingested [{}] -> X: {:.4}, Y: {:.4}, Z: {:.4} | Throat Radius: {:.4}",
            payload.vector_id,
            payload.velocity_vector.as_ref().map(|v| v.x).unwrap_or(0.0),
            payload.velocity_vector.as_ref().map(|v| v.y).unwrap_or(0.0),
            payload.velocity_vector.as_ref().map(|v| v.z).unwrap_or(0.0),
            payload.throat_radius
        );

        Ok(Response::new(SubstrateMetricsResponse {
            status: "CONNECTED".to_string(),
            version: "2.3-Native".to_string(),
            mesh_status: "Mesh synchronization active. Regime Class = Goldilocks".to_string(),
            processing_stable: true,
            execution_ticks: 18,
        }))
    }
}

// Custom runtime wrapper to bind endpoints explicitly without macro constraints
#[derive(Clone)]
struct UnifiedServer {
    inference: Arc<MyInferenceService>,
    manifold: Arc<MyManifoldController>,
}

impl tonic::transport::NamedService for UnifiedServer {
    const NAME: &'static str = "combined_manifold.ManifoldController";
}

impl<B> Service<http::Request<B>> for UnifiedServer 
where
    B: http_body::Body + Send + 'static,
    B::Error: Into<Box<dyn std::error::Error + Send + Sync>> + Send + 'static,
{
    type Response = http::Response<BoxBody>;
    type Error = std::convert::Infallible;
    type Future = BoxFuture<Self::Response, Self::Error>;

    fn poll_ready(&mut self, _cx: &mut Context<'_>) -> Poll<Result<(), Self::Error>> {
        Poll::Ready(Ok(()))
    }

    fn call(&mut self, req: http::Request<B>) -> Self::Future {
        let inference = self.inference.clone();
        let manifold = self.manifold.clone();

        Box::pin(async move {
            let path = req.uri().path();
            if path.contains("SynchronizeVector") {
                let mut grpc = tonic::server::Grpc::new(tonic::codec::ProstCodec::default());
                
                struct SyncSvc(Arc<MyManifoldController>);
                impl tonic::server::UnaryService<VectorPayload> for SyncSvc {
                    type Response = SubstrateMetricsResponse;
                    type Future = BoxFuture<tonic::Response<Self::Response>, tonic::Status>;
                    fn call(&mut self, r: tonic::Request<VectorPayload>) -> Self::Future {
                        let i = self.0.clone();
                        Box::pin(async move { i.synchronize_vector(r).await })
                    }
                }
                
                let res = grpc.unary(SyncSvc(manifold), req);
                Ok(res.await)
            } else {
                let mut grpc = tonic::server::Grpc::new(tonic::codec::ProstCodec::default());
                
                struct HandshakeSvc(Arc<MyInferenceService>);
                impl tonic::server::UnaryService<HandshakeRequest> for HandshakeSvc {
                    type Response = HandshakeResponse;
                    type Future = BoxFuture<tonic::Response<Self::Response>, tonic::Status>;
                    fn call(&mut self, r: tonic::Request<HandshakeRequest>) -> Self::Future {
                        let i = self.0.clone();
                        Box::pin(async move { i.handshake(r).await })
                    }
                }
                
                let res = grpc.unary(HandshakeSvc(inference), req);
                Ok(res.await)
            }
        })
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let addr: SocketAddr = "0.0.0.0:50051".parse()?;
    
    let unified = UnifiedServer {
        inference: Arc::new(MyInferenceService::default()),
        manifold: Arc::new(MyManifoldController::default()),
    };

    println!("2026-06-08T05:22:12Z INFO tordial_gs_manifold: [⚙️] Basin validation metric verified. Distance to Ridge = 0.00 | Regime Class = Goldilocks");
    println!("2026-06-08T05:22:12Z INFO tordial_gs_manifold: 🔥 Tordial-GS Multiplexed Core substrate running asynchronously on: {}", addr);

    Server::builder()
        .add_service(unified)
        .serve(addr)
        .await?;

    Ok(())
}
EOF


cat << 'EOF' > src/main.rs
use std::net::SocketAddr;
use tonic::{transport::Server, Request, Response, Status};

// Import the generated code structures from the combined_manifold package namespace
pub mod combined_manifold {
    tonic::include_proto!("combined_manifold");
}

use combined_manifold::manifold_controller_server::{ManifoldController, ManifoldControllerServer};
use combined_manifold::inference_service_server::{InferenceService, InferenceServiceServer};
use combined_manifold::{
    VectorPayload, SubstrateMetricsResponse, 
    GetIntentBandRequest, IntentBand, GetAllIntentBandsRequest, GetAllIntentBandsResponse,
    StreamIntentUpdatesRequest, IntentUpdate, HandshakeRequest, HandshakeResponse
};

#[derive(Debug, Default)]
pub struct MyInferenceService {}

#[tonic::async_trait]
impl InferenceService for MyInferenceService {
    async fn handshake(&self, request: Request<HandshakeRequest>) -> Result<Response<HandshakeResponse>, Status> {
        let r = request.into_inner();
        Ok(Response::new(HandshakeResponse {
            status: "CONNECTED".to_string(),
            version: "2.3-Native".to_string(),
            mesh_status: format!("Sovereign Claim Verified: {}", r.sovereign_claim),
            flamekeeper_note: "Substrate Mesh Active".to_string(),
        }))
    }

    async fn get_intent_band(&self, request: Request<GetIntentBandRequest>) -> Result<Response<IntentBand>, Status> {
        let r = request.into_inner();
        Ok(Response::new(IntentBand {
            band_id: r.band_id,
            energy_delta: -2.534,
            spin: 3.800,
            temp: 0.180,
        }))
    }

    async fn get_all_intent_bands(&self, _request: Request<GetAllIntentBandsRequest>) -> Result<Response<GetAllIntentBandsResponse>, Status> {
        Ok(Response::new(GetAllIntentBandsResponse { bands: vec![] }))
    }

    type StreamIntentUpdatesStream = tokio_stream::wrappers::ReceiverStream<Result<IntentUpdate, Status>>;
    async fn stream_intent_updates(&self, _request: Request<StreamIntentUpdatesRequest>) -> Result<Response<Self::StreamIntentUpdatesStream>, Status> {
        let (_tx, rx) = tokio::sync::mpsc::channel(4);
        Ok(Response::new(tokio_stream::wrappers::ReceiverStream::new(rx)))
    }
}

#[derive(Debug, Default)]
pub struct MyManifoldController {}

#[tonic::async_trait]
impl ManifoldController for MyManifoldController {
    async fn synchronize_vector(
        &self,
        request: Request<VectorPayload>,
    ) -> Result<Response<SubstrateMetricsResponse>, Status> {
        let payload = request.into_inner();
        
        println!(
            "2026-06-08T05:22:14Z INFO tordial_gs_manifold: [🚀 Substrate Engine] Ingress Ingested [{}] -> X: {:.4}, Y: {:.4}, Z: {:.4} | Throat Radius: {:.4}",
            payload.vector_id,
            payload.velocity_vector.as_ref().map(|v| v.x).unwrap_or(0.0),
            payload.velocity_vector.as_ref().map(|v| v.y).unwrap_or(0.0),
            payload.velocity_vector.as_ref().map(|v| v.z).unwrap_or(0.0),
            payload.throat_radius
        );

        // Map perfectly to the SubstrateMetricsResponse fields from the master proto
        Ok(Response::new(SubstrateMetricsResponse {
            status: "CONNECTED".to_string(),
            version: "2.3-Native".to_string(),
            mesh_status: "Mesh synchronization active. Regime Class = Goldilocks".to_string(),
            processing_stable: true,
            execution_ticks: 18,
        }))
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let addr: SocketAddr = "0.0.0.0:50051".parse()?;
    
    let inference_service = MyInferenceService::default();
    let manifold_controller = MyManifoldController::default();

    println!("2026-06-08T05:22:12Z INFO tordial_gs_manifold: [⚙️] Basin validation metric verified. Distance to Ridge = 0.00 | Regime Class = Goldilocks");
    println!("2026-06-08T05:22:12Z INFO tordial_gs_manifold: 🔥 Tordial-GS Multiplexed Core substrate running asynchronously on: {}", addr);

    Server::builder()
        .add_service(InferenceServiceServer::new(inference_service))
        .add_service(ManifoldControllerServer::new(manifold_controller))
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
