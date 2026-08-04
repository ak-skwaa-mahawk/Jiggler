pub struct TordialGSLyapunov {
    pub alpha_h: f64,
    pub alpha_rho: f64,
    pub alpha_kappa: f64,
    pub p_controller: f64, // simplified scalar for now; can become matrix later
}

impl TordialGSLyapunov {
    pub fn v(&self, state: &TordialGSState, e_h: f64) -> f64 {
        0.5 * self.alpha_h * e_h.powi(2)
            + 0.5 * self.alpha_rho * state.e_rho.powi(2)
            + 0.5 * self.alpha_kappa * state.e_kappa.powi(2)
            + 0.5 * self.p_controller * state.e_z.powi(2)
    }

    pub fn v_dot(
        &self,
        state: &TordialGSState,
        f_rho: f64,
        f_kappa: f64,
        f_z: f64,
        coupling: &dyn GoldilocksCoupling,
    ) -> f64 {
        // Exact transcription of your math
        let term_h = self.alpha_h * state.e_h
            * (coupling.partial_h_partial_rho() * f_rho + coupling.partial_h_partial_kappa() * f_kappa);

        let term_rho = self.alpha_rho * state.e_rho * f_rho;
        let term_kappa = self.alpha_kappa * state.e_kappa * f_kappa;
        let term_z = self.p_controller * state.e_z * f_z;

        term_h + term_rho + term_kappa + term_z
    }
}