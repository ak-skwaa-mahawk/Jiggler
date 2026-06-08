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