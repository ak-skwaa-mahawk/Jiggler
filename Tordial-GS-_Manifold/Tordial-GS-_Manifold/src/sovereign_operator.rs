// src/sovereign_operator.rs

use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::intent_engine::{IntentEngine, IntentUpdate, BasinValidator};

#[pyclass]
#[derive(Clone)]
pub struct SovereignOperator {
    engine: IntentEngine,
}

#[pymethods]
impl SovereignOperator {
    #[new]
    fn new() -> Self {
        Self {
            engine: IntentEngine::new(),
        }
    }

    /// Main sovereign steering method — called from Python PWC loop
    fn apply_intent(
        &self,
        band_id: String,
        intent_value: f64,
        d: f64,
        r: f64,
        sigma_t: f64,
        rho: f64,
        reason: String,
    ) -> PyResult<PyObject> {
        let update = IntentUpdate {
            band_id: band_id.clone(),
            intent_value,
            reason: reason.clone(),
            timestamp: crate::intent_engine::current_unix_timestamp(),
            ..Default::default()
        };

        self.engine.broadcast_update(update, d, r, sigma_t, rho);

        let distance = BasinValidator::distance_to_ridge(d, r, sigma_t, rho);
        let damped_value = BasinValidator::apply_damping(intent_value, distance);
        let regime = BasinValidator::classify_regime(d, r, sigma_t, rho);

        Python::with_gil(|py| {
            let dict = PyDict::new(py);
            dict.set_item("original_value", intent_value)?;
            dict.set_item("damped_value", damped_value)?;
            dict.set_item("distance", distance)?;
            dict.set_item("regime", format!("{:?}", regime))?;
            dict.set_item("band_id", band_id)?;
            dict.set_item("reason", reason)?;
            Ok(dict.into())
        })
    }

    /// Observe current manifold state (called by Critic)
    fn observe_manifold(&self, d: f64, r: f64, sigma_t: f64, rho: f64) -> PyResult<PyObject> {
        let distance = BasinValidator::distance_to_ridge(d, r, sigma_t, rho);
        let regime = BasinValidator::classify_regime(d, r, sigma_t, rho);

        Python::with_gil(|py| {
            let dict = PyDict::new(py);
            dict.set_item("distance_to_ridge", distance)?;
            dict.set_item("regime", format!("{:?}", regime))?;
            dict.set_item("d", d)?;
            dict.set_item("r", r)?;
            dict.set_item("sigma_t", sigma_t)?;
            dict.set_item("rho", rho)?;
            Ok(dict.into())
        })
    }

    fn set_gs_pressure(&self, pressure: f64) {
        // Future: store and use in damping calculation
        tracing::info!(target: "sovereign::operator", gs_pressure = pressure, "GS pressure set from Python");
    }
}