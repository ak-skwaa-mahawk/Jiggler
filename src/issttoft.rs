cat << 'EOF' > src/issttoft.rs
// ISST-TOFT Shared State Type Definition Layout
#[derive(Debug, Clone)]
pub enum GSMode {
    Subcritical = 0,
    Marginal = 1,
    Goldilocks = 2,
    DeepGs = 3,
}

#[derive(Debug, Clone)]
pub struct IntentUpdate {
    pub band_id: String,
    pub mode: i32,
    pub intent_value: f64,
    pub timestamp: i64,
    pub reason: String,
}
EOF
echo "✅ Core issttoft types initialized inside src/issttoft.rs."
