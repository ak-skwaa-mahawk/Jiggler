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