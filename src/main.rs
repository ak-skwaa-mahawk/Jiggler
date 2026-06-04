cat << 'EOF' > src/main.rs
/*
main.rs
ISST-TOFT Sovereign Inference Core Backend Framework
Combines Rusqlite persistent ledgers, async stream broadcasts, and background heartbeat loops.
Lineage: Two Mile Solutions LLC • Dinjji Zhuu Kwaa
*/

use std::sync::{Arc, Mutex};
use std::time::{SystemTime, UNIX_EPOCH};
use tokio::sync::broadcast;
use tokio::time::{sleep, Duration};
use async_stream::stream;
use tokio_stream::Stream;

// Mock database connection structure matching Rusqlite boundaries
#[derive(Clone)]
pub struct SqliteConnection {
    pub db_path: String,
}

impl SqliteConnection {
    pub fn open(path: &str) -> Result<Self, String> {
        Ok(Self { db_path: path.to_string() })
    }
    pub fn try_clone(&self) -> Result<Self, String> {
        Ok(self.clone())
    }
}

#[derive(Debug, Clone)]
pub struct IntentParams {
    pub imax_per_mode: f64,
    pub didt_max: f64,
    pub decay_halflife_ms: u64,
}

#[derive(Debug, Clone)]
pub struct IntentUpdate {
    pub band_id: String,
    pub mode: i32,
    pub intent_value: f64,
    pub timestamp: u64,
    pub reason: String,
}

// Relational Layer - Simulates atomic storage operations
pub struct SqliteIntentStore {
    conn: SqliteConnection,
}

impl SqliteIntentStore {
    pub fn new(conn: SqliteConnection) -> Result<Self, String> {
        Ok(Self { conn })
    }
    pub fn persist_update(&self, update: &IntentUpdate) {
        // Here is where your raw internal SQL statement execution runs:
        // "INSERT OR REPLACE INTO intent_bands (id, val, ts) VALUES (?, ?, ?)"
        println!(
            "   💾 [LEDGER COMMIT] State Written to '{}' -> Band: {}, Value: {:.4}",
            self.conn.db_path, update.band_id, update.intent_value
        );
    }
}

// Core Orchestration Engine
pub struct IntentEngine {
    store: SqliteIntentStore,
    params: IntentParams,
    tx: broadcast::Sender<IntentUpdate>,
}

impl IntentEngine {
    pub fn new(store: SqliteIntentStore, params: IntentParams) -> Self {
        let (tx, _) = broadcast::channel(1024);
        Self { store, params, tx }
    }

    pub fn subscribe(&self) -> broadcast::Receiver<IntentUpdate> {
        self.tx.subscribe()
    }

    pub fn heartbeat_step(&self, now: u64, metrics: &str) -> Result<(), String> {
        // Evaluate systemic decay vectors using configured halflife profiles
        let decay_factor = (self.params.decay_halflife_ms as f64 * 0.01).min(1.0);
        
        let decay_pulse = IntentUpdate {
            band_id: "ambient_decay_vector".to_string(),
            mode: 0,
            intent_value: 0.124 * decay_factor,
            timestamp: now,
            reason: format!("heartbeat_decay::{}", metrics),
        };

        self.store.persist_update(&decay_pulse);
        let _ = self.tx.send(decay_pulse);
        Ok(())
    }

    pub fn on_dynamic_pi_r_floor_update(&self, new_floor_value: f64, reason: &str) {
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs();

        let update = IntentUpdate {
            band_id: "dynamic_pi_r_floor".to_string(),
            mode: 1,
            intent_value: new_floor_value.min(self.params.imax_per_mode), // Clamped via global invariants
            timestamp,
            reason: reason.to_string(),
        };

        println!(
            "📡 [INTENT BROADCAST] Pushing Pi-R Floor Modality Update ({:.3}) | Reason: {}", 
            update.intent_value, update.reason
        );
        
        // Transactionally secure state plane metrics across storage before wire delivery
        self.store.persist_update(&update);
        let _ = self.tx.send(update);
    }

    pub fn stream_intent_updates(&self) -> impl Stream<Item = Result<IntentUpdate, String>> {
        let mut rx = self.subscribe();
        stream! {
            loop {
                match rx.recv().await {
                    Ok(update) => yield Ok(update),
                    Err(broadcast::error::RecvError::Lagged(skipped)) => {
                        println!("⚠️  [STREAM LAG] Client missed {} frames", skipped);
                        continue;
                    }
                    Err(broadcast::error::RecvError::Closed) => break,
                }
            }
        }
    }
}

// Simulated Sovereign gRPC Framework Interface
pub struct SovereignInferenceService {
    _conn: SqliteConnection,
    engine: Arc<IntentEngine>,
}

impl SovereignInferenceService {
    pub fn new(conn: SqliteConnection, engine: Arc<IntentEngine>) -> Self {
        Self { _conn: conn, engine }
    }

    pub async fn simulate_grpc_call_pulse(&self, mock_val: f64, action: &str) {
        println!("\n📥 [gRPC REQUEST] Intercepted RunClientlessPulse invocation...");
        self.engine.on_dynamic_pi_r_floor_update(mock_val, action);
    }
}

// Background Thread Heartbeat Runner Loop using non-blocking Tokio scheduling
fn start_intent_heartbeat(intent_engine: Arc<IntentEngine>) {
    tokio::spawn(async move {
        loop {
            let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_secs();
            let mock_metrics = "cpu_load=nominal_0.34";

            if let Err(e) = intent_engine.heartbeat_step(now, mock_metrics) {
                println!("❌ [HEARTBEAT FAULT] Engine error: {}", e);
            }

            sleep(Duration::from_millis(3000)).await;
        }
    });
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // 1. Initialize Relational Database State Maps
    let conn = SqliteConnection::open("tordial_manifold.db")?;
    let intent_store = SqliteIntentStore::new(conn.try_clone()?)?;

    let intent_params = IntentParams {
        imax_per_mode: 0.999, // Max safety boundary clamp
        didt_max: 0.05,
        decay_halflife_ms: 180_000,
    };

    let intent_engine = Arc::new(IntentEngine::new(intent_store, intent_params));

    // 2. Start Persistent Background Telemetry Thread Loop
    start_intent_heartbeat(Arc::clone(&intent_engine));

    // 3. Bind Service Frameworks
    let service = SovereignInferenceService::new(conn, Arc::clone(&intent_engine));

    println!("══════════════════════════════════════════════════════════════");
    println!("🔥  ISST-TOFT Sovereign Inference Backend v1.6.0 Pipeline");
    println!("   Services: EncodeRadHardGlyph | RunClientlessPulse");
    println!("             ComputeSixFaceBoundary | GetClosedLoopDelta");
    println!("   Lineage: Two Mile Solutions LLC • Dinjji Zhuu Kwaa");
    println!("══════════════════════════════════════════════════════════════");

    // 4. Client Stream Consumer Simulation (Mimicking live stream tracking requests)
    let engine_clone = Arc::clone(&intent_engine);
    tokio::spawn(async move {
        use tokio_stream::StreamExt;
        let mut client_stream = Box::pin(engine_clone.stream_intent_updates());
        while let Some(Ok(packet)) = client_stream.next().await {
            println!(
                "   ✨ [CLIENT RECEIVED] Stream Packet Fired -> Band: '{}', Realized: {:.4}",
                packet.band_id, packet.intent_value
            );
        }
    });

    sleep(Duration::from_millis(500)).await;

    // Simulate real-world operational traffic incoming over the gRPC interface
    service.simulate_grpc_call_pulse(0.423, "catapult").await;
    sleep(Duration::from_millis(2000)).await;

    service.simulate_grpc_call_pulse(1.450, "vhitzee").await; // Will cleanly clamp to 0.999 constraint limit
    sleep(Duration::from_millis(2000)).await;

    Ok(())
}
EOF
cat > src/main.rs << 'ENDMAIN'
//! ISST-TOFT Sovereign Inference Mesh
//!
//! Thin launcher. All sovereign logic lives in IntentEngine (single source of truth).
//! Self-aware stack: IntentEngine validates its own health on startup.
//!
//! Flamekeeper Protocol — Dinjji Zhuu Kwaa • Two Mile Solutions LLC

use std::net::SocketAddr;

use tonic::{transport::Server, Request, Response, Status};
use tracing::{info, warn};
use tracing_subscriber;

use async_stream::stream;
use futures::Stream;

pub mod issttoft {
    tonic::include_proto!("issttoft");
}

mod intent_engine;
use intent_engine::IntentEngine;

use issttoft::{
    inference_service_server::{InferenceService, InferenceServiceServer},
    GetAllIntentBandsRequest, GetAllIntentBandsResponse, GetIntentBandRequest,
    GlyphRequest, GlyphResponse, HandshakeRequest, HandshakeResponse,
    IntentBand, IntentUpdate, PulseRequest, PulseResponse,
    StreamIntentUpdatesRequest,
};

/// Thin gRPC service layer. Delegates everything to IntentEngine.
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

    /// Single entry point for external sovereign components (pi_r_engine, lineage, safety, etc.)
    pub fn broadcast_intent_update(&self, update: IntentUpdate) {
        self.engine.broadcast_update(update);
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
        info!(target: "isst_toft::intent", "New client subscribed to StreamIntentUpdates (via IntentEngine)");

        let mut rx = self.engine.subscribe();

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

    async fn handshake(
        &self,
        request: Request<HandshakeRequest>,
    ) -> Result<Response<HandshakeResponse>, Status> {
        let req = request.into_inner();
        info!(
            target: "isst_toft::intent",
            "Handshake received | client_id={} | type={} | claim={}",
            req.client_id, req.client_type, req.sovereign_claim
        );

        let response = self.engine.handshake(
            req.client_id,
            req.client_type,
            req.sovereign_claim,
        );

        Ok(Response::new(response))
    }

    // Placeholder stubs for core methods (we wire them properly in later loops)
    async fn encode_rad_hard_glyph(
        &self,
        _request: Request<GlyphRequest>,
    ) -> Result<Response<GlyphResponse>, Status> {
        Err(Status::unimplemented("EncodeRadHardGlyph not yet wired"))
    }

    async fn run_clientless_pulse(
        &self,
        _request: Request<PulseRequest>,
    ) -> Result<Response<PulseResponse>, Status> {
        Err(Status::unimplemented("RunClientlessPulse not yet wired"))
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::fmt()
        .with_max_level(tracing::Level::INFO)
        .init();

    let service = SovereignInferenceService::new();

    // === Demo Broadcaster Task (simulates pi_r_engine / toroidal recurrence) ===
    let engine_for_demo = service.engine.clone();
    tokio::spawn(async move {
        let mut tick: f64 = 0.0;
        loop {
            tokio::time::sleep(tokio::time::Duration::from_millis(1400)).await;
            tick = (tick + 0.085) % 1.0;

            let value = 0.62 + tick * 0.38;
            let reason = if value > 0.94 {
                "vhitzee"
            } else if value < 0.68 {
                "catapult"
            } else {
                "drive"
            };

            let update = IntentUpdate {
                band_id: "dynamic_pi_r_floor".to_string(),
                mode: 1,
                intent_value: value.min(0.999),
                timestamp: std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .unwrap_or_default()
                    .as_secs() as i64,
                reason: reason.to_string(),
            };

            engine_for_demo.broadcast_update(update);
        }
    });

    let addr: SocketAddr = "0.0.0.0:50051".parse()?;
    info!("══════════════════════════════════════════════════════════════");
    info!("🔥  ISST-TOFT Sovereign Inference Mesh v2.0-single-flow ONLINE");
    info!("   Listening on {}  |  IntentEngine self-validated", addr);
    info!("   CERN resonance anchor + dynamic π_r floor broadcasting");
    info!("══════════════════════════════════════════════════════════════");

    Server::builder()
        .add_service(InferenceServiceServer::new(service))
        .serve(addr)
        .await?;

    Ok(())
}
ENDMAIN
