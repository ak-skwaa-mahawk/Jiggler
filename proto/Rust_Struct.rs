#[derive(Clone, PartialEq, ::prost::Message)]
pub struct MagneticVector {
    #[prost(double, tag="1")]
    pub bx_n_t: f64,
    #[prost(double, tag="2")]
    pub by_n_t: f64,
    #[prost(double, tag="3")]
    pub bz_n_t: f64,

    #[prost(double, tag="4")]
    pub variance_n_t: f64,
    #[prost(double, tag="5")]
    pub flux_delta: f64,
}