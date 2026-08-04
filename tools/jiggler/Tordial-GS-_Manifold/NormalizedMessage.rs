#[derive(Debug, Clone)]
pub struct NormalizedMessage {
    pub intent: String,              // e.g. "continue_protocol", "switch_to_code"
    pub details: HashMap<String, String>, // arbitrary key/value
}