use crate::identity::Sigma;
use serde::{Serialize, Deserialize};

pub const BROADCAST_SIGMA: [u8; 32] = [0xFF; 32];

#[repr(u8)]
#[derive(Clone, Copy, Debug, Serialize, Deserialize)]
pub enum MsgType {
    HelloSovereign = 0x01,
    HelloAck       = 0x02,
    SctIssue       = 0x03,
    DbuPropose     = 0x04,
    DbuResponse    = 0x05,
    HaPublish      = 0x06,
    IcPropose      = 0x07,
    IcAccept       = 0x08,
    IcExit         = 0x09,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Frame {
    pub version: u8,
    pub msg_type: MsgType,
    pub from_sigma: Sigma,
    pub to_sigma: Sigma,
    pub tick: u64,
    pub nonce: u64,
    pub payload: Vec<u8>,
    pub auth_tag: [u8; 32],
}

impl Frame {
    pub fn encode(&self) -> Vec<u8> {
        bincode::serialize(self).expect("frame encode")
    }

    pub fn decode(bytes: &[u8]) -> Result<Self, bincode::Error> {
        bincode::deserialize(bytes)
    }
}