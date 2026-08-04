impl ManifoldService {
    pub async fn handle_soil_liquidity(
        &self,
        lc: SoilLiquidityVector,
        ts: i64,
    ) {
        // 1. Update hydration model
        self.soil_state.update_moisture(lc.soil_moisture_percent);

        // 2. EC reflects fungal network throughput
        self.soil_state.update_conductivity(lc.electrical_conductivity);

        // 3. Nutrient load feeds metabolic potential
        self.ecology_state.update_nutrients(lc.nutrient_ppm);

        // 4. Fungal density = structural integrity of the underground mesh
        self.ecology_state.update_fungal_density(lc.fungal_density);

        // 5. Liquidity index influences long-term GS-band stability
        self.regime.update_from_liquidity(lc.liquidity_index);

        // 6. Ledger entry
        self.ecology_state.record_soil_liquidity(lc, ts);
    }
}
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

    #[prost(message, optional, tag="5")]
    pub biomass_vector: Option<BiomassVector>,

    #[prost(message, optional, tag="6")]
    pub atmospheric_vector: Option<AtmosphericVector>,

    #[prost(message, optional, tag="7")]
    pub soil_liquidity_vector: Option<SoilLiquidityVector>,

    #[prost(double, tag="8")]
    pub vault_depth: f64,

    #[prost(double, tag="9")]
    pub liquidity_coupling: f64,

    #[prost(int64, tag="10")]
    pub ts_utc: i64,
}
impl ManifoldService {
    pub async fn handle_atmospheric(
        &self,
        av: AtmosphericVector,
        ts: i64,
    ) {
        // 1. Update gas exchange model
        self.atmo_state.update_gases(av.co2_ppm, av.o2_percent);

        // 2. Feed photosynthetic efficiency into Mₒ operator
        self.ecology_state.update_photosynthesis(av.photosynthetic_efficiency);

        // 3. Entropy load influences long-term drift and GS-band stability
        self.regime.update_from_entropy(av.entropy_load);

        // 4. Temperature + humidity feed stomatal behavior model
        self.ecology_state.update_stomata(av.temperature_c, av.humidity_percent);

        // 5. Ledger entry
        self.ecology_state.record_atmospheric(av, ts);
    }
}
impl ManifoldService {
    pub async fn handle_biomass(
        &self,
        bv: BiomassVector,
        ts: i64,
    ) {
        // 1. Update structural mass model
        self.biomass_state.update_volume(bv.canopy_volume_m3);
        self.biomass_state.update_mass(bv.trunk_mass_kg);

        // 2. Feed LAI into photosynthetic potential model
        self.ecology_state.update_lai(bv.leaf_area_index);

        // 3. Growth rate influences long-term GS-band drift
        self.regime.update_from_growth(bv.growth_rate);

        // 4. Ledger entry
        self.ecology_state.record_biomass(bv, ts);
    }
}