// tests/integration_test.rs

use tordial_gs_spectral::*;
use num_complex::Complex64;

#[test]
fn test_rust_matches_python() {
    let grid = Grid::new(64, 64, 2.0, 0.5);
    let eig = build_laplacian_spectrum(&grid);

    let mut phi = RealField::zeros(&grid);
    let mut rho = RealField::zeros(&grid);
    let mut kap = RealField::zeros(&grid);

    // Build θ, φ grids
    let nθ = grid.n_theta;
    let nφ = grid.n_phi;

    let mut theta = vec![0.0; nθ];
    let mut phi_ang = vec![0.0; nφ];

    for i in 0..nθ { theta[i] = 2.0 * std::f64::consts::PI * (i as f64) / (nθ as f64); }
    for j in 0..nφ { phi_ang[j] = 2.0 * std::f64::consts::PI * (j as f64) / (nφ as f64); }

    // ρGS = 1 + 0.2 cosθ cosφ
    for i in 0..nθ {
        for j in 0..nφ {
            let idx = i * nφ + j;
            rho.data[idx] = 1.0 + 0.2 * theta[i].cos() * phi_ang[j].cos();
            kap.data[idx] = 0.5;
        }
    }

    let mut pid = PID::new(0.1, 0.0, 0.0);
    let fft = RustFFTBackend::new(&grid);

    let α = 1.0;
    let β = 1.0;
    let λ = 1.0;
    let dt = 0.01;
    let target = 0.0;

    for _ in 0..200 {
        phi = tordial_gs_step(
            &grid, &fft, &phi, &rho, &kap,
            &eig, &mut pid,
            α, β, λ, dt, target,
        );
    }

    // Check mean(Φ) is near zero (Python result)
    let mean_phi: f64 = phi.data.iter().sum::<f64>() / (nθ * nφ) as f64;
    assert!(mean_phi.abs() < 1e-6);
}