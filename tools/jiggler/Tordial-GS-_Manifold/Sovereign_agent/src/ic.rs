use crate::identity::Sigma;
use serde::{Serialize, Deserialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct IntentVector {
    pub components: Vec<f32>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct IntentContract {
    pub contract_id: [u8; 32],
    pub participants: Vec<Sigma>,
    pub shared_intent: IntentVector,
    pub tick_start: u64,
    pub tick_end: u64,
    pub tolerance: f32,
    pub exit_clause_digest: [u8; 32],
    pub settlement_rule_digest: [u8; 32],
}