use pyo3::prelude::*;
use numpy::{PyArray2, IntoPyArray};
use num_complex::Complex64;

use tordial_gs_spectral::*;
use tordial_gs_spectral::fft_backend::RustFFTBackend;


/// ------------------------------
/// Python-exposed Tordial Node
/// ------------------------------
#[pyclass]
pub struct TordialNodePy {
    grid: Grid,
    fft: RustFFTBackend,
    eig: LaplacianSpectrum,
    phi: RealField,
    rho: RealField,
    kap: RealField,
    pid: PID,
}

#[pymethods]
impl TordialNodePy {
    #[new]
    fn new(n_theta: usize, n_phi: usize, r_major: f64, r_minor: f64) -> Self {
        let grid = Grid::new(n_theta, n_phi, r_major, r_minor);
        let eig = build_laplacian_spectrum(&grid);
        let fft = RustFFTBackend::new(&grid);

        Self {
            grid,
            fft,
            eig,
            phi: RealField::zeros(&grid),
            rho: RealField::zeros(&grid),
            kap: RealField::zeros(&grid),
            pid: PID::new(0.1, 0.0, 0.0),
        }
    }

    fn set_fields(&mut self, phi: &PyArray2<f64>, rho: &PyArray2<f64>, kap: &PyArray2<f64>) {
        let nθ = self.grid.n_theta;
        let nφ = self.grid.n_phi;

        let phi_r = phi.readonly();
        let rho_r = rho.readonly();
        let kap_r = kap.readonly();

        for i in 0..nθ {
            for j in 0..nφ {
                let idx = i * nφ + j;
                self.phi.data[idx] = phi_r[[i, j]];
                self.rho.data[idx] = rho_r[[i, j]];
                self.kap.data[idx] = kap_r[[i, j]];
            }
        }
    }

    fn step(&mut self, alpha: f64, beta: f64, lambda: f64, dt: f64, target: f64) {
        self.phi = tordial_gs_step(
            &self.grid,
            &self.fft,
            &self.phi,
            &self.rho,
            &self.kap,
            &self.eig,
            &mut self.pid,
            alpha,
            beta,
            lambda,
            dt,
            target,
        );
    }

    fn get_phi<'py>(&self, py: Python<'py>) -> &'py PyArray2<f64> {
        let nθ = self.grid.n_theta;
        let nφ = self.grid.n_phi;

        let mut out = ndarray::Array2::<f64>::zeros((nθ, nφ));
        for i in 0..nθ {
            for j in 0..nφ {
                out[[i, j]] = self.phi.data[i * nφ + j];
            }
        }
        out.into_pyarray(py)
    }

    fn low_modes(&self, k: usize) -> Vec<(usize, usize, Complex64)> {
        let mut phi_hat = SpectralField::zeros(&self.grid);
        self.fft.forward(&self.grid, &self.phi, &mut phi_hat);

        let mut out = Vec::new();
        for m in 0..k {
            for n in 0..k {
                out.push((m, n, phi_hat.data[m * self.grid.n_phi + n]));
            }
        }
        out
    }

    fn apply_low_modes(&mut self, modes: Vec<(usize, usize, Complex64)>) {
        let mut phi_hat = SpectralField::zeros(&self.grid);
        self.fft.forward(&self.grid, &self.phi, &mut phi_hat);

        for (m, n, val) in modes {
            phi_hat.data[m * self.grid.n_phi + n] = val;
        }

        self.fft.inverse(&self.grid, &phi_hat, &mut self.phi);
    }
}


/// ------------------------------
/// Python-exposed Tordial Cluster
/// ------------------------------
#[pyclass]
pub struct TordialClusterPy {
    nodes: Vec<TordialNodePy>,
}

#[pymethods]
impl TordialClusterPy {
    #[new]
    fn new(num_nodes: usize, n_theta: usize, n_phi: usize, r_major: f64, r_minor: f64) -> Self {
        let nodes = (0..num_nodes)
            .map(|_| TordialNodePy::new(n_theta, n_phi, r_major, r_minor))
            .collect();

        Self { nodes }
    }

    fn set_fields_all(&mut self, phi: &PyArray2<f64>, rho: &PyArray2<f64>, kap: &PyArray2<f64>) {
        for node in self.nodes.iter_mut() {
            node.set_fields(phi, rho, kap);
        }
    }

    fn step_all(&mut self, alpha: f64, beta: f64, lambda: f64, dt: f64, target: f64) {
        for node in self.nodes.iter_mut() {
            node.step(alpha, beta, lambda, dt, target);
        }
    }

    fn sync_low_modes(&mut self, k: usize) {
        let mut accum: Vec<(usize, usize, Complex64)> = Vec::new();
        let mut count = 0;

        for node in self.nodes.iter() {
            let modes = node.low_modes(k);
            if accum.is_empty() {
                accum = modes;
            } else {
                for (i, (_, _, v)) in modes.iter().enumerate() {
                    accum[i].2 += *v;
                }
            }
            count += 1;
        }

        for (_, _, v) in accum.iter_mut() {
            *v /= count as f64;
        }

        for node in self.nodes.iter_mut() {
            node.apply_low_modes(accum.clone());
        }
    }

    fn get_phi<'py>(&self, py: Python<'py>, idx: usize) -> &'py PyArray2<f64> {
        self.nodes[idx].get_phi(py)
    }
}


/// ------------------------------
/// Single-step convenience function
/// ------------------------------
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
    let phi_r = phi.readonly();
    let rho_r = rho_gs.readonly();
    let kap_r = kappa.readonly();

    let (nθ, nφ) = (phi_r.shape()[0], phi_r.shape()[1]);

    let grid = Grid::new(nθ, nφ, 2.0, 0.5);
    let eig = build_laplacian_spectrum(&grid);
    let fft = RustFFTBackend::new(&grid);
    let mut pid = PID::new(0.1, 0.0, 0.0);

    let mut phi_field = RealField::zeros(&grid);
    let mut rho_field = RealField::zeros(&grid);
    let mut kap_field = RealField::zeros(&grid);

    for i in 0..nθ {
        for j in 0..nφ {
            let idx = i * nφ + j;
            phi_field.data[idx] = phi_r[[i, j]];
            rho_field.data[idx] = rho_r[[i, j]];
            kap_field.data[idx] = kap_r[[i, j]];
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

    let mut out = ndarray::Array2::<f64>::zeros((nθ, nφ));
    for i in 0..nθ {
        for j in 0..nφ {
            out[[i, j]] = phi_new.data[i * nφ + j];
        }
    }

    Ok(out.into_pyarray(py))
}


/// ------------------------------
/// PyO3 module definition
/// ------------------------------
#[pymodule]
fn tordial_gs_py(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<TordialNodePy>()?;
    m.add_class::<TordialClusterPy>()?;
    m.add_function(wrap_pyfunction!(tordial_gs_step_py, m)?)?;
    Ok(())
}