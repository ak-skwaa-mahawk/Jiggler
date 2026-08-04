use pyo3::prelude::*;
use std::sync::{Arc, Mutex};
use std::sync::atomic::{AtomicBool, Ordering};
use std::thread::{self, JoinHandle};
use std::time::Duration;

use crate::core::actor::SovereignEconomicActor;
use crate::core::substrate_bus::PySubstrateMeshBus;

#[pyclass]
pub struct PyCombiner {
    inner: Arc<Mutex<SovereignEconomicActor>>,
    pub actor_id: u64,
    daemon_flag: Arc<AtomicBool>,
    daemon_handle: Option<JoinHandle<()>>,
}

#[pymethods]
impl PyCombiner {
    #[new]
    pub fn new(actor_id: u64, initial_forcing: f64) -> Self {
        PyCombiner {
            inner: Arc::new(Mutex::new(SovereignEconomicActor::new(actor_id, initial_forcing))),
            actor_id,
            daemon_flag: Arc::new(AtomicBool::new(false)),
            daemon_handle: None,
        }
    }

    pub fn register_to_bus(&mut self, bus: &PySubstrateMeshBus) {
        if let Ok(mut actor) = self.inner.lock() {
            actor.register_bus(bus.clone());
        }
    }

    pub fn get_alpha_forcing(&self) -> f64 {
        if let Ok(actor) = self.inner.lock() {
            actor.alpha_forcing
        } else {
            0.0
        }
    }

    pub fn get_max_compute(&self) -> f64 {
        if let Ok(actor) = self.inner.lock() {
            actor.max_compute
        } else {
            0.0
        }
    }

    pub fn push_manifold_tick(&mut self, timestamp: u64, _velocity_vector: Vec<f64>) {
        if let Ok(mut actor) = self.inner.lock() {
            actor.push_update(crate::core::actor::SubstrateUpdate::ManifoldTick {
                timestamp,
                velocity_vector: vec![0.0, 0.0, 0.0],
            });
        }
    }

    /* ==========================================================================
       CLI / FFI PORTABILITY EXPANSIONS
       ========================================================================== */

    /// Fetches current immutable block count on the registered substrate mesh bus
    pub fn get_chain_height(&self) -> PyResult<usize> {
        if let Ok(actor) = self.inner.lock() {
            if let Some(bus) = &actor.registered_bus {
                return Ok(bus.get_event_count());
            }
        }
        Ok(0)
    }

    /// Exposes delta streaming capability directly over PyO3 boundary line
    pub fn export_delta_stream(&self, from_index: usize) -> PyResult<String> {
        if let Ok(actor) = self.inner.lock() {
            if let Some(bus) = &actor.registered_bus {
                return bus.export_portable_delta(from_index);
            }
        }
        Err(pyo3::exceptions::PyRuntimeError::new_err("Mesh substrate bus unattached or locked."))
    }

    /// Exposes secure delta ingestion capability directly over PyO3 boundary line
    pub fn import_delta_stream(&self, payload: String) -> PyResult<bool> {
        if let Ok(actor) = self.inner.lock() {
            if let Some(bus) = &actor.registered_bus {
                return bus.import_portable_delta(payload);
            }
        }
        Err(pyo3::exceptions::PyRuntimeError::new_err("Mesh substrate bus unattached or locked."))
    }

    pub fn start_autonomous_daemon(&mut self, heartbeat_ms: u64) {
        if self.daemon_flag.load(Ordering::SeqCst) {
            return;
        }

        self.daemon_flag.store(true, Ordering::SeqCst);
        let run_flag = self.daemon_flag.clone();
        let actor_inner = self.inner.clone();
        let current_actor_id = self.actor_id;

        println!("🚀 [DAEMON LAYER]: Initializing background thread for Actor {} (Heartbeat: {}ms)...", current_actor_id, heartbeat_ms);

        self.daemon_handle = Some(thread::spawn(move || {
            while run_flag.load(Ordering::SeqCst) {
                if let Ok(mut actor) = actor_inner.lock() {
                    actor.scan_and_adapt_to_mesh();
                }
                thread::sleep(Duration::from_millis(heartbeat_ms));
            }
            println!("🛑 [DAEMON LAYER]: Background processing loop terminated cleanly for Actor {}.", current_actor_id);
        }));
    }

    pub fn stop_autonomous_daemon(&mut self) {
        if !self.daemon_flag.load(Ordering::SeqCst) {
            return;
        }

        println!("🛑 [DAEMON LAYER]: Sending shutdown signal to background thread for Actor {}...", self.actor_id);
        self.daemon_flag.store(false, Ordering::SeqCst);

        if let Some(handle) = self.daemon_handle.take() {
            let _ = handle.join();
        }
    }
}

impl Drop for PyCombiner {
    fn drop(&mut self) {
        self.daemon_flag.store(false, Ordering::SeqCst);
    }
}
