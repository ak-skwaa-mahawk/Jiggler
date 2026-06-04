// From pi_r_engine, lineage events, safety monitors, etc.
let engine = IntentEngine::new();

engine.broadcast_update(IntentUpdate {
    band_id: "sovereign_floor".into(),
    mode: 1,
    intent_value: 0.8742,
    timestamp: current_unix_timestamp(),
    reason: "drive".into(),
});

// Or from the service (already wired)
service.broadcast_intent_update(update);

// Streaming clients
let mut rx = engine.subscribe();
while let Ok(update) = rx.recv().await { ... }