use serde::{Serialize, Deserialize};

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct Sigma(pub [u8; 32]);

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct GenesisRecord {
    pub sigma: Sigma,
    pub genesis_tick: u64,
    pub curvature_digest: [u8; 32],
    pub holonomy_digest: [u8; 32],
}

pub trait AuthProvider: Send + Sync {
    fn sign(&self, from: &Sigma, msg: &[u8]) -> [u8; 32];
    fn verify(&self, from: &Sigma, msg: &[u8], tag: &[u8; 32]) -> bool;
}