use crate::identity::Sigma;
use serde::{Serialize, Deserialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PathDescriptor {
    pub compressed: Vec<u8>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct HolonomyAttestation {
    pub agent_sigma: Sigma,
    pub path_descriptor: PathDescriptor,
    pub holonomy_digest: [u8; 32],
    pub context_tags: Vec<String>,
    pub valid_from_tick: u64,
    pub valid_until_tick: u64,
}