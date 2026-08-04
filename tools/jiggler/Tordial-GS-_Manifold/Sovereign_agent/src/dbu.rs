use crate::identity::Sigma;
use crate::sct::Bounds;
use serde::{Serialize, Deserialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CurvatureDelta {
    pub compressed: Vec<u8>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct HolonomyDelta {
    pub compressed: Vec<u8>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct IntentDelta {
    pub vector: Vec<f32>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct GsBoundProof {
    pub curvature_norm: f32,
    pub holonomy_norm: f32,
    pub intent_norm: f32,
    pub proof_blob: Vec<u8>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct DriftBoundedUpdate {
    pub from_sigma: Sigma,
    pub to_sigma: Sigma,
    pub tick_start: u64,
    pub tick_end: u64,
    pub curvature_delta: Option<CurvatureDelta>,
    pub holonomy_delta: Option<HolonomyDelta>,
    pub intent_delta: Option<IntentDelta>,
    pub sct_ref: [u8; 32],
    pub gs_bound_proof: GsBoundProof,
}

#[repr(u8)]
#[derive(Clone, Copy, Debug, Serialize, Deserialize)]
pub enum DbuStatus {
    Accept    = 0x01,
    Reject    = 0x02,
    Negotiate = 0x03,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct DbuResponse {
    pub from_sigma: Sigma,
    pub to_sigma: Sigma,
    pub status: DbuStatus,
    pub applied_delta_digest: Option<[u8; 32]>,
    pub counter_bounds: Option<Bounds>,
}