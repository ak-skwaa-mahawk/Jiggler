// src/metrics.rs  (or put it near your heartbeat code)

use crate::intent::SystemMetrics;
use crate::tordial_gs::{TordialGSState, GlobalEnergy}; // adjust paths as needed

/// Collects current system metrics from the Tordial-GS manifold
/// to feed into the Intent Engine.
pub fn collect_current_system_metrics(
    gs_state: &TordialGSState,
    global_energy: &GlobalEnergy,
    node_count: usize,
) -> SystemMetrics {
    SystemMetrics {
        gs_curvature: gs_state.curvature_mean,
        load_factor: gs_state.load_factor(),
        error_rate: gs_state.error_rate(),
        energy_level: global_energy.current(),
        node_count,
    }
}