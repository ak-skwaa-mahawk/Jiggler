// ====================== main.rs ======================

use rusqlite::Connection;
use std::thread;
use std::time::Duration;

use crate::intent::{
    IntentEngine, IntentParams, SqliteIntentStore, seed_initial_intent_bands,
};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // ============================================
    // 1. Initialize Database + Intent System
    // ============================================
    let conn = Connection::open("tordial_manifold.db")?;

    // Seed tables + initial 7 intent bands
    let intent_store = SqliteIntentStore::new(conn.try_clone()?)?;
    seed_initial_intent_bands(&conn)?;

    let intent_params = IntentParams {
        imax_per_mode: 1.0,
        didt_max: 0.05,
        decay_halflife_ms: 180_000,
    };

    let intent_engine = IntentEngine::new(intent_store, intent_params);

    // ============================================
    // 2. Start Intent Heartbeat in Background
    // ============================================
    start_intent_heartbeat(intent_engine);

    // ============================================
    // 3. Start gRPC Server
    // ============================================
    let addr = "[::]:50051".parse()?;
    let service = SovereignInferenceService::new(conn); // ← pass connection

    tracing::info!("══════════════════════════════════════════════════════════════");
    tracing::info!("🔥  ISST-TOFT Sovereign Inference Backend v1.6.0");
    tracing::info!("   gRPC listening on {}", addr);
    tracing::info!("   Services: EncodeRadHardGlyph | RunClientlessPulse");
    tracing::info!("             ComputeSixFaceBoundary | GetClosedLoopDelta | RunTrackingFormProof");
    tracing::info!("             GetIntentBand | GetAllIntentBands");
    tracing::info!("   Lineage: Two Mile Solutions LLC • Dinjji Zhuu Kwaa");
    tracing::info!("══════════════════════════════════════════════════════════════");

    tonic::transport::Server::builder()
        .add_service(InferenceServiceServer::new(service))
        .serve(addr)
        .await?;

    Ok(())
}

// ============================================
// Background Intent Heartbeat
// ============================================
fn start_intent_heartbeat<D>(intent_engine: IntentEngine<D>)
where
    D: IntentStorage + Send + Sync + 'static,
{
    thread::spawn(move || {
        loop {
            let now = current_time_millis();
            let metrics = collect_current_system_metrics(); // implement this

            if let Err(e) = intent_engine.heartbeat_step(now, &metrics) {
                log::error!("Intent heartbeat error: {:?}", e);
            }

            thread::sleep(Duration::from_millis(5000));
        }
    });
}