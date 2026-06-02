pub trait GoldilocksCoupling {
    fn h(&self, rho_gs: f64, kappa: f64) -> f64;
    fn partial_h_partial_rho(&self) -> f64;
    fn partial_h_partial_kappa(&self) -> f64;
}

#[derive(Clone, Copy, Debug)]
pub struct LinearGoldilocks {
    pub scale: f64, // κ scaling factor that defines the desired coupling slope
}

impl GoldilocksCoupling for LinearGoldilocks {
    #[inline]
    fn h(&self, rho_gs: f64, kappa: f64) -> f64 {
        rho_gs - self.scale * kappa
    }
    // ... partial derivatives
}