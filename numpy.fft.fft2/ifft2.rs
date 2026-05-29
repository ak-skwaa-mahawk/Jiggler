// src/fft_backend.rs

use crate::{FFTBackend, Grid, RealField, SpectralField};
use num_complex::Complex64;
use rustfft::{FftPlanner, num_complex::Complex};
use std::sync::Arc;

pub struct RustFFTBackend {
    fft_theta: Arc<dyn rustfft::Fft<f64>>,
    ifft_theta: Arc<dyn rustfft::Fft<f64>>,
    fft_phi: Arc<dyn rustfft::Fft<f64>>,
    ifft_phi: Arc<dyn rustfft::Fft<f64>>,
}

impl RustFFTBackend {
    pub fn new(grid: &Grid) -> Self {
        let mut planner = FftPlanner::<f64>::new();

        let fft_theta = planner.plan_fft_forward(grid.n_theta);
        let ifft_theta = planner.plan_fft_inverse(grid.n_theta);

        let fft_phi = planner.plan_fft_forward(grid.n_phi);
        let ifft_phi = planner.plan_fft_inverse(grid.n_phi);

        Self {
            fft_theta,
            ifft_theta,
            fft_phi,
            ifft_phi,
        }
    }
}

impl FFTBackend for RustFFTBackend {
    fn forward(&self, grid: &Grid, input: &RealField, output: &mut SpectralField) {
        let nθ = grid.n_theta;
        let nφ = grid.n_phi;

        // Copy input → complex buffer
        let mut buf: Vec<Complex64> =
            input.data.iter().map(|&x| Complex64::new(x, 0.0)).collect();

        // FFT along θ for each φ
        for j in 0..nφ {
            let start = j * nθ;
            let end = start + nθ;
            self.fft_theta.process(&mut buf[start..end]);
        }

        // FFT along φ for each θ
        for i in 0..nθ {
            let mut col: Vec<Complex64> = (0..nφ)
                .map(|j| buf[i + j * nθ])
                .collect();

            self.fft_phi.process(&mut col);

            for j in 0..nφ {
                buf[i + j * nθ] = col[j];
            }
        }

        output.data.copy_from_slice(&buf);
    }

    fn inverse(&self, grid: &Grid, input: &SpectralField, output: &mut RealField) {
        let nθ = grid.n_theta;
        let nφ = grid.n_phi;

        let mut buf = input.data.clone();

        // IFFT along φ
        for i in 0..nθ {
            let mut col: Vec<Complex64> = (0..nφ)
                .map(|j| buf[i + j * nθ])
                .collect();

            self.ifft_phi.process(&mut col);

            for j in 0..nφ {
                buf[i + j * nθ] = col[j];
            }
        }

        // IFFT along θ
        for j in 0..nφ {
            let start = j * nθ;
            let end = start + nθ;
            self.ifft_theta.process(&mut buf[start..end]);
        }

        // Normalize (rustfft does not normalize)
        let norm = (nθ * nφ) as f64;
        for i in 0..buf.len() {
            output.data[i] = buf[i].re / norm;
        }
    }
}