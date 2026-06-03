use std::fmt;

/// Intent Band Identifier (e.g. "safety.checkpoints", "resonance.drive")
#[derive(Clone, Debug, Hash, Eq, PartialEq)]
pub struct IntentBandId(pub String);

impl fmt::Display for IntentBandId {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}

/// Mode index ω
#[derive(Clone, Copy, Debug, Hash, Eq, PartialEq)]
pub struct ModeId(pub i32);

/// Reason for an intent delta
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum IntentReason {
    Drive,
    Decay,
    Safety,
}

impl IntentReason {
    pub fn as_str(&self) -> &'static str {
        match self {
            IntentReason::Drive => "drive",
            IntentReason::Decay => "decay",
            IntentReason::Safety => "safety",
        }
    }
}

/// Current state of one band × mode
#[derive(Clone, Debug)]
pub struct IntentBandState {
    pub band: IntentBandId,
    pub mode: ModeId,
    pub intent_value: f64,
    pub lastupdatets: i64,
    pub source: String,
}

/// Tunable parameters for the Intent Engine
#[derive(Clone, Debug)]
pub struct IntentParams {
    pub imax_per_mode: f64,
    pub didt_max: f64,
    pub decay_halflife_ms: i64,
}

/// Metrics coming from the Tordial-GS / decision plane (Medium coupling)
#[derive(Clone, Debug, Default)]
pub struct SystemMetrics {
    pub gs_curvature: f64,
    pub load_factor: f64,
    pub error_rate: f64,
    pub energy_level: f64,
    pub node_count: usize,
}