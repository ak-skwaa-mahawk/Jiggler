#[derive(Clone, PartialEq, ::prost::Message)]
pub struct EconomicVector {
    #[prost(double, tag="1")]
    pub capital_velocity: f64,
    #[prost(double, tag="2")]
    pub regulatory_drag: f64,
    #[prost(double, tag="3")]
    pub yield_generation: f64,
}

#[derive(Clone, PartialEq, ::prost::Message)]
pub struct SapFluxVector {
    #[prost(double, tag="1")]
    pub fm_norm: f64,
    #[prost(double, tag="2")]
    pub raw_velocity_mm_s: f64,
    #[prost(double, tag="3")]
    pub temp_c: f64,
    #[prost(double, tag="4")]
    pub pressure_kpa: f64,
}

#[derive(Clone, PartialEq, ::prost::Message)]
pub struct ManifoldTick {
    #[prost(string, tag="1")]
    pub vector_id: String,

    #[prost(message, optional, tag="2")]
    pub economic_vector: Option<EconomicVector>,

    #[prost(message, optional, tag="3")]
    pub sap_flux_vector: Option<SapFluxVector>,

    #[prost(double, tag="4")]
    pub vault_depth: f64,

    #[prost(double, tag="5")]
    pub liquidity_coupling: f64,

    #[prost(int64, tag="6")]
    pub ts_utc: i64,
}