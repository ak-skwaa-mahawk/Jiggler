use crate::intent_engine::IntentEngine;
use crate::issttoft::IntentUpdate;

pub struct PiRIntegrationExample {
    intent_engine: IntentEngine,
}

impl PiRIntegrationExample {
    pub fn on_dynamic_pi_r_floor_update(&self, new_floor_value: f64, reason: &str) {
        let update = IntentUpdate {
            band_id: "dynamic_pi_r_floor".to_string(),
            mode: 1,
            intent_value: new_floor_value.min(0.999),
            timestamp: current_unix_timestamp(),
            reason: reason.to_string(), // "catapult" | "vhitzee" | "drive" | ...
        };

        // === THE SINGLE INTEGRATION POINT ===
        self.intent_engine.broadcast_update(update);
    }
}