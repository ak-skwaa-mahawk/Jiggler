// In your main application (not inside the gRPC crate)

use rusqlite::Connection;
use std::thread;
use std::time::Duration;

use crate::intent::{
    IntentEngine, IntentParams, SqliteIntentStore, seed_initial_intent_bands,
};

fn main() -> anyhow::Result<()> {
    // ============================================
    // 1. Initialize Database + Intent System
    // ============================================
    let conn = Connection::open("tordial_manifold.db")?;

    // Initialize Intent tables and seed the 7 core bands
    let intent_store = SqliteIntentStore::new(conn.try_clone()?)?;
    seed_initial_intent_bands(&conn)?;

    let intent_params = IntentParams {
        imax_per_mode: 1.0,
        didt_max: 0.05,
        decay_halflife_ms: 180_000, // 3 minutes
    };

    let intent_engine = IntentEngine::new(intent_store, intent_params);

    // ============================================
    // 2. Start Intent Heartbeat (background thread)
    // ============================================
    start_intent_heartbeat(intent_engine.clone()); // clone if needed for ownership

    // ============================================
    // 3. Start gRPC Server (your existing code)
    // ============================================
    let addr = "[::]:50051".parse()?;
    let service = SovereignInferenceService::default();

    tracing::info!("Starting ISST-TOFT gRPC server on {}", addr);

    tokio::runtime::Builder::new_multi_thread()
        .enable_all()
        .build()?
        .block_on(async {
            tonic::transport::Server::builder()
                .add_service(InferenceServiceServer::new(service))
                .serve(addr)
                .await
        })?;

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
            let metrics = collect_current_system_metrics(); // ← implement this

            if let Err(e) = intent_engine.heartbeat_step(now, &metrics) {
                log::error!("Intent heartbeat error: {:?}", e);
            }

            thread::sleep(Duration::from_millis(5000)); // every 5 seconds
        }
    });
}