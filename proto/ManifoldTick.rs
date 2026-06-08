#[derive(Clone, PartialEq, ::prost::Message)]
pub struct ManifoldTick {
    #[prost(string, tag="1")]
    pub vector_id: String,

    #[prost(message, optional, tag="2")]
    pub economic_vector: Option<EconomicVector>,

    #[prost(message, optional, tag="3")]
    pub sap_flux_vector: Option<SapFluxVector>,

    #[prost(message, optional, tag="4")]
    pub magnetic_vector: Option<MagneticVector>,

    #[prost(double, tag="5")]
    pub vault_depth: f64,

    #[prost(double, tag="6")]
    pub liquidity_coupling: f64,

    #[prost(int64, tag="7")]
    pub ts_utc: i64,
}