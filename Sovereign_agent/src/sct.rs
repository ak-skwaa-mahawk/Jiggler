use crate::identity::{Sigma, AuthProvider};
use serde::{Serialize, Deserialize};
use bitflags::bitflags;

bitflags! {
    #[derive(Serialize, Deserialize)]
    pub struct CurvatureScope: u32 {
        const NONE   = 0;
        const LOCAL  = 1 << 0;
        const GLOBAL = 1 << 1;
        const BAND_0 = 1 << 2;
        const BAND_1 = 1 << 3;
    }
}

bitflags! {
    #[derive(Serialize, Deserialize)]
    pub struct HolonomyScope: u32 {
        const NONE      = 0;
        const READ_PATH = 1 << 0;
        const READ_SUM  = 1 << 1;
    }
}

bitflags! {
    #[derive(Serialize, Deserialize)]
    pub struct IntentScope: u32 {
        const NONE      = 0;
        const SUGGEST   = 1 << 0;
        const NUDGE     = 1 << 1;
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Bounds {
    pub max_curvature_delta: f32,
    pub max_holonomy_delta: f32,
    pub max_intent_delta: f32,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct SovereignCapabilityToken {
    pub issuer_sigma: Sigma,
    pub subject_sigma: Sigma,
    pub curvature_scope: CurvatureScope,
    pub holonomy_scope: HolonomyScope,
    pub intent_scope: IntentScope,
    pub bounds: Bounds,
    pub expiry_tick: u64,
    pub token_nonce: u64,
    pub signature: [u8; 64],
}

impl SovereignCapabilityToken {
    pub fn sign(&mut self, auth: &dyn AuthProvider) {
        let bytes = bincode::serialize(self).unwrap();
        self.signature = auth.sign(&self.issuer_sigma, &bytes);
    }

    pub fn verify(&self, auth: &dyn AuthProvider) -> bool {
        let bytes = bincode::serialize(self).unwrap();
        auth.verify(&self.issuer_sigma, &bytes, &self.signature)
    }

    pub fn is_expired(&self, tick: u64) -> bool {
        tick > self.expiry_tick
    }
}