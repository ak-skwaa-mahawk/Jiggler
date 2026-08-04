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
use std::collections::HashMap;

use crate::{
    identity::{Sigma, AuthProvider},
    frame::{Frame, MsgType},
    sct::SovereignCapabilityToken,
    dbu::{DriftBoundedUpdate, DbuResponse},
    ha::HolonomyAttestation,
    ic::IntentContract,
};

/// Backend interface for integrating the protocol with the
/// Tordial–GS manifold, planner–walker–critic, and safety logic.
pub trait SovereignAgentBackend: Send + Sync {
    fn current_tick(&self) -> u64;

    fn critic_handle_dbu(&self, dbu: &DriftBoundedUpdate) -> DbuResponse;

    fn critic_handle_ic_propose(&self, ic: &IntentContract) -> bool;

    fn critic_handle_ic_exit(&self, ic: &IntentContract);

    fn planner_handle_ha(&self, ha: &HolonomyAttestation);

    /// Optional: allow backend to ingest SCTs (e.g., into critic registry).
    fn ingest_sct(&self, _sct: &SovereignCapabilityToken) {
        // default: no-op
    }
}

/// High‑level node wrapper that processes frames.
pub struct AgentNode<'a> {
    pub sigma: Sigma,
    pub backend: &'a dyn SovereignAgentBackend,
    pub auth: &'a dyn AuthProvider,

    /// Local SCT registry keyed by hash (e.g., blake3 of serialized SCT).
    pub sct_registry: HashMap<[u8; 32], SovereignCapabilityToken>,
}

impl<'a> AgentNode<'a> {
    /// Compute a stable hash for an SCT (you can swap in your preferred hash).
    fn hash_sct(&self, sct: &SovereignCapabilityToken) -> [u8; 32] {
        use blake3::Hasher;
        let mut hasher = Hasher::new();
        let bytes = bincode::serialize(sct).expect("sct serialize");
        hasher.update(&bytes);
        *hasher.finalize().as_bytes()
    }

    /// Helper to build a response frame with signed auth_tag.
    fn build_response_frame<T: serde::Serialize>(
        &self,
        msg_type: MsgType,
        to_sigma: Sigma,
        payload_struct: &T,
    ) -> Frame {
        let payload = bincode::serialize(payload_struct).expect("payload serialize");
        let tick = self.backend.current_tick();
        let nonce = rand::random::<u64>();

        let mut frame = Frame {
            version: 1,
            msg_type,
            from_sigma: self.sigma,
            to_sigma,
            tick,
            nonce,
            payload,
            auth_tag: [0u8; 32],
        };

        // sign header+payload
        let bytes = frame.encode_without_auth();
        frame.auth_tag = self.auth.sign(&self.sigma, &bytes);
        frame
    }

    /// Variant of encode that omits auth_tag from the signed region.
    /// Add this method to `Frame` if you want a cleaner separation.
    fn verify_incoming(&self, frame: &Frame) -> bool {
        // For now, sign/verify over the entire serialized frame minus auth_tag,
        // or define a dedicated method on Frame to get the signed bytes.
        let mut clone = frame.clone();
        clone.auth_tag = [0u8; 32];
        let bytes = clone.encode();
        self.auth.verify(&frame.from_sigma, &bytes, &frame.auth_tag)
    }

    /// Main entry point: handle an incoming frame and optionally return a response frame.
    pub fn handle_frame(&mut self, frame: Frame) -> Option<Frame> {
        // 1) Basic auth check (optional but recommended)
        if !self.verify_incoming(&frame) {
            // Fail closed: ignore unauthenticated frames
            return None;
        }

        // 2) Ignore frames not addressed to us (unless broadcast)
        let is_broadcast = frame.to_sigma.0 == crate::frame::BROADCAST_SIGMA;
        if !is_broadcast && frame.to_sigma != self.sigma {
            return None;
        }

        match frame.msg_type {
            MsgType::HelloSovereign => {
                // You can parse a HELLO payload here if you define one.
                // For now, we just ACK with a HelloAck (no payload).
                let resp = Frame {
                    version: 1,
                    msg_type: MsgType::HelloAck,
                    from_sigma: self.sigma,
                    to_sigma: frame.from_sigma,
                    tick: self.backend.current_tick(),
                    nonce: rand::random::<u64>(),
                    payload: Vec::new(),
                    auth_tag: [0u8; 32],
                };
                let mut resp = resp;
                let bytes = {
                    let mut clone = resp.clone();
                    clone.auth_tag = [0u8; 32];
                    clone.encode()
                };
                resp.auth_tag = self.auth.sign(&self.sigma, &bytes);
                Some(resp)
            }

            MsgType::HelloAck => {
                // Typically no response needed; you might update local peer state.
                None
            }

            MsgType::SctIssue => {
                // 3) Decode SCT, store in registry, and forward to backend if desired.
                let sct: SovereignCapabilityToken =
                    match bincode::deserialize(&frame.payload) {
                        Ok(v) => v,
                        Err(_) => return None,
                    };

                let hash = self.hash_sct(&sct);
                self.sct_registry.insert(hash, sct.clone());
                self.backend.ingest_sct(&sct);

                // No protocol‑level response required by default.
                None
            }

            MsgType::DbuPropose => {
                // 4) Decode DBU, optionally enrich with SCT lookup, and route to critic.
                let mut dbu: DriftBoundedUpdate =
                    match bincode::deserialize(&frame.payload) {
                        Ok(v) => v,
                        Err(_) => return None,
                    };

                // Optional: verify that referenced SCT exists locally.
                if !self.sct_registry.contains_key(&dbu.sct_ref) {
                    // Critic will likely reject anyway, but we can short‑circuit.
                    let resp = DbuResponse {
                        from_sigma: self.sigma,
                        to_sigma: frame.from_sigma,
                        status: crate::dbu::DbuStatus::Reject,
                        applied_delta_digest: None,
                        counter_bounds: None,
                    };
                    return Some(self.build_response_frame(
                        MsgType::DbuResponse,
                        frame.from_sigma,
                        &resp,
                    ));
                }

                let resp = self.backend.critic_handle_dbu(&dbu);

                // 5) Build DBU_RESPONSE frame back to proposer.
                Some(self.build_response_frame(
                    MsgType::DbuResponse,
                    frame.from_sigma,
                    &resp,
                ))
            }

            MsgType::DbuResponse => {
                // 6) DBU responses are usually consumed by the planner/initiator.
                // You can decode and forward to backend if you want.
                // For now, we just decode and drop.
                let _resp: DbuResponse =
                    match bincode::deserialize(&frame.payload) {
                        Ok(v) => v,
                        Err(_) => return None,
                    };
                None
            }

            MsgType::HaPublish => {
                // 7) Decode HA and pass to planner via backend.
                let ha: HolonomyAttestation =
                    match bincode::deserialize(&frame.payload) {
                        Ok(v) => v,
                        Err(_) => return None,
                    };

                self.backend.planner_handle_ha(&ha);
                None
            }

            MsgType::IcPropose => {
                // 8) Decode IC and ask critic whether to join.
                let ic: IntentContract =
                    match bincode::deserialize(&frame.payload) {
                        Ok(v) => v,
                        Err(_) => return None,
                    };

                let accept = self.backend.critic_handle_ic_propose(&ic);

                if accept {
                    // Send IC_ACCEPT back to proposer (payload = same IC or minimal ack).
                    Some(self.build_response_frame(
                        MsgType::IcAccept,
                        frame.from_sigma,
                        &ic,
                    ))
                } else {
                    // Decline silently or define an explicit decline message type if you want.
                    None
                }
            }

            MsgType::IcAccept => {
                // 9) Another agent accepted our IC; planner/critic may want to know.
                // For now, decode and ignore.
                let _ic: IntentContract =
                    match bincode::deserialize(&frame.payload) {
                        Ok(v) => v,
                        Err(_) => return None,
                    };
                None
            }

            MsgType::IcExit => {
                // 10) Another agent exits an IC; inform critic.
                let ic: IntentContract =
                    match bincode::deserialize(&frame.payload) {
                        Ok(v) => v,
                        Err(_) => return None,
                    };

                self.backend.critic_handle_ic_exit(&ic);
                None
            }
        }
    }
}

/// Small extension to Frame to get bytes without auth_tag in the signed region.
/// Add this to `frame.rs` if you want to keep signing logic consistent.
impl Frame {
    pub fn encode_without_auth(&self) -> Vec<u8> {
        let mut clone = self.clone();
        clone.auth_tag = [0u8; 32];
        bincode::serialize(&clone).expect("frame encode_without_auth")
    }
}