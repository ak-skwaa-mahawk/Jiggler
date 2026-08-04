#[derive(Clone)]
pub struct GsCurvatureConfig {
    pub n_bands: usize,
    pub diag_stiffness: Vec<f64>,   // D diagonal
    pub coupling: Vec<Vec<f64>>,    // C matrix
    pub dt_seconds: f64,
}

#[derive(Clone)]
pub struct CurvatureState {
    pub x: Vec<f64>, // current band values
}
impl CurvatureState {
    pub fn step(&mut self, cfg: &GsCurvatureConfig, forcing: &[f64]) {
        let n = cfg.n_bands;
        let mut dx = vec![0.0; n];

        for i in 0..n {
            // -D * x
            dx[i] -= cfg.diag_stiffness[i] * self.x[i];

            // C * x
            for j in 0..n {
                dx[i] += cfg.coupling[i][j] * self.x[j];
            }

            // add forcing
            dx[i] += forcing[i];
        }

        for i in 0..n {
            self.x[i] += cfg.dt_seconds * dx[i];
        }
    }
}
pub fn heartbeat_step(&self, now: u64) -> Result<(), String> {
    let mut state = self.curvature_state.lock().unwrap();
    let mut forcing = self.forcing_accumulator.lock().unwrap();

    state.step(&self.curvature_cfg, &forcing);

    // clear forcing for next tick
    forcing.iter_mut().for_each(|f| *f = 0.0);

    // emit updated bands as IntentUpdate packets
    for (band_idx, value) in state.x.iter().enumerate() {
        let update = IntentUpdate {
            band_id: format!("band_{}", band_idx),
            mode: 0,
            intent_value: *value,
            timestamp: now as i64,
            reason: "gs_curvature_step".to_string(),
        };
        self.persist_and_broadcast(update);
    }

    Ok(())
}