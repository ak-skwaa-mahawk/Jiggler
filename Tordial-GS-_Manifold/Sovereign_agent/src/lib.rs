//! Sovereign Agent Protocol
//!
//! Wire‑level primitives for sovereign agents operating on the
//! Tordial–GS manifold substrate. This crate defines:
//!   - Sovereign identity (σ)
//!   - Message frames
//!   - Capability tokens (SCT)
//!   - Drift‑bounded updates (DBU)
//!   - Holonomy attestations (HA)
//!   - Intent contracts (IC)
//!
//! Policy is implemented externally via the SovereignAgentBackend trait.

pub mod identity;
pub mod frame;
pub mod sct;
pub mod dbu;
pub mod ha;
pub mod ic;
pub mod backend;

pub use identity::*;
pub use frame::*;
pub use sct::*;
pub use dbu::*;
pub use ha::*;
pub use ic::*;
pub use backend::*;