#[derive(Clone, PartialEq, ::prost::Message)]
pub struct AtmosphericVector {
    #[prost(double, tag="1")]
    pub co2_ppm: f64,
    #[prost(double, tag="2")]
    pub o2_percent: f64,
    #[prost(double, tag="3")]
    pub humidity_percent: f64,
    #[prost(double, tag="4")]
    pub temperature_c: f64,
    #[prost(double, tag="5")]
    pub pressure_hpa: f64,

    #[prost(double, tag="6")]
    pub photosynthetic_efficiency: f64,
    #[prost(double, tag="7")]
    pub entropy_load: f64,
}
#[derive(Clone, PartialEq, ::prost::Message)]
pub struct BiomassVector {
    #[prost(double, tag="1")]
    pub canopy_volume_m3: f64,
    #[prost(double, tag="2")]
    pub trunk_mass_kg: f64,
    #[prost(double, tag="3")]
    pub leaf_area_index: f64,
    #[prost(double, tag="4")]
    pub growth_rate: f64,
    #[prost(double, tag="5")]
    pub lidar_confidence: f64,
}
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