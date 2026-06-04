use crate::{
    Sigma,
    DriftBoundedUpdate,
    DbuResponse,
    HolonomyAttestation,
    IntentContract,
};

/// Backend interface for integrating the protocol with the
/// Tordial–GS manifold, planner–walker–critic, and safety logic.
pub trait SovereignAgentBackend: Send + Sync {
    fn current_tick(&self) -> u64;

    fn critic_handle_dbu(&self, dbu: &DriftBoundedUpdate) -> DbuResponse;

    fn critic_handle_ic_propose(&self, ic: &IntentContract) -> bool;

    fn critic_handle_ic_exit(&self, ic: &IntentContract);

    fn planner_handle_ha(&self, ha: &HolonomyAttestation);
}

/// High‑level node wrapper that processes frames.
pub struct AgentNode<'a> {
    pub sigma: Sigma,
    pub backend: &'a dyn SovereignAgentBackend,
    pub auth: &'a dyn crate::AuthProvider,
}

impl<'a> AgentNode<'a> {
    pub fn handle_frame(&self, frame: crate::Frame) -> Option<crate::Frame> {
        // decode payload by msg_type, dispatch to backend,
        // construct response frame if needed.
        //
        // This is intentionally left unimplemented so you can
        // wire it to your mesh transport and manifold logic.
        unimplemented!()
    }
}