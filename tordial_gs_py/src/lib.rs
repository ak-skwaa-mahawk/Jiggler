// tordial_gs_py/src/lib.rs

use numpy::{PyArray2, IntoPyArray};
use pyo3::prelude::*;
use tordial_gs_spectral::*;
use tordial_gs_spectral::fft_backend::RustFFTBackend;

/// Python-exposed solver step:
/// Φ_next = step(Φ, ρGS, κ, α, β, λ, dt, Φ_target_mean)
#[pyfunction]
fn tordial_gs_step_py<'py>(
    py: Python<'py>,
    phi: &PyArray2<f64>,
    rho_gs: &PyArray2<f64>,
    kappa: &PyArray2<f64>,
    alpha: f64,
    beta: f64,
    lambda: f64,
    dt: f64,
    phi_target_mean: f64,
) -> PyResult<&'py PyArray2<f64>> {
    let phi = phi.readonly();
    let rho_gs = rho_gs.readonly();
    let kappa = kappa.readonly();

    let shape = phi.shape();
    let (n_theta, n_phi) = (shape[0], shape[1]);

    let grid = Grid::new(n_theta, n_phi, 2.0, 0.5);
    let eig = build_laplacian_spectrum(&grid);
    let fft = RustFFTBackend::new(&grid);
    let mut pid = PID::new(0.1, 0.0, 0.0);

    let mut phi_field = RealField::zeros(&grid);
    let mut rho_field = RealField::zeros(&grid);
    let mut kap_field = RealField::zeros(&grid);

    for i in 0..n_theta {
        for j in 0..n_phi {
            let idx = i * n_phi + j;
            phi_field.data[idx] = phi[[i, j]];
            rho_field.data[idx] = rho_gs[[i, j]];
            kap_field.data[idx] = kappa[[i, j]];
        }
    }

    let phi_new = tordial_gs_step(
        &grid,
        &fft,
        &phi_field,
        &rho_field,
        &kap_field,
        &eig,
        &mut pid,
        alpha,
        beta,
        lambda,
        dt,
        phi_target_mean,
    );

    let mut out = ndarray::Array2::<f64>::zeros((n_theta, n_phi));
    for i in 0..n_theta {
        for j in 0..n_phi {
            let idx = i * n_phi + j;
            out[[i, j]] = phi_new.data[idx];
        }
    }

    Ok(out.into_pyarray(py))
}

#[pymodule]
fn tordial_gs_py(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(tordial_gs_step_py, m)?)?;
    Ok(())
}