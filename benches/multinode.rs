use criterion::{criterion_group, criterion_main, Criterion, black_box};
use tordial_gs_spectral::*;
use tordial_gs_spectral::fft_backend::RustFFTBackend;
use num_complex::Complex64;

/// A synthetic "node" in the Tordial–GS cluster.
struct Node<'a, B: FFTBackend> {
    grid: &'a Grid,
    fft: &'a B,
    phi: RealField,
    rho: RealField,
    kap: RealField,
    eig: &'a LaplacianSpectrum,
    pid: PID,
}

impl<'a, B: FFTBackend> Node<'a, B> {
    fn new(grid: &'a Grid, fft: &'a B, eig: &'a LaplacianSpectrum) -> Self {
        let mut rho = RealField::zeros(grid);
        let mut kap = RealField::zeros(grid);

        // Same GS + curvature fields as Python prototype
        let nθ = grid.n_theta;
        let nφ = grid.n_phi;

        let mut theta = vec![0.0; nθ];
        let mut phi_ang = vec![0.0; nφ];

        for i in 0..nθ {
            theta[i] = 2.0 * std::f64::consts::PI * (i as f64) / (nθ as f64);
        }
        for j in 0..nφ {
            phi_ang[j] = 2.0 * std::f64::consts::PI * (j as f64) / (nφ as f64);
        }

        for i in 0..nθ {
            for j in 0..nφ {
                let idx = i * nφ + j;
                rho.data[idx] = 1.0 + 0.2 * theta[i].cos() * phi_ang[j].cos();
                kap.data[idx] = 0.5;
            }
        }

        Self {
            grid,
            fft,
            phi: RealField::zeros(grid),
            rho,
            kap,
            eig,
            pid: PID::new(0.1, 0.0, 0.0),
        }
    }

    /// One Tordial–GS update step
    fn step(&mut self, α: f64, β: f64, λ: f64, dt: f64, target: f64) {
        self.phi = tordial_gs_step(
            self.grid,
            self.fft,
            &self.phi,
            &self.rho,
            &self.kap,
            self.eig,
            &mut self.pid,
            α,
            β,
            λ,
            dt,
            target,
        );
    }

    /// Extract low-frequency modes for cross-node sync
    fn low_modes(&self, k: usize) -> Vec<Complex64> {
        let mut out = Vec::new();
        let nθ = self.grid.n_theta;
        let nφ = self.grid.n_phi;

        // FFT of phi
        let mut phi_hat = SpectralField::zeros(self.grid);
        self.fft.forward(self.grid, &self.phi, &mut phi_hat);

        for m in 0..k {
            for n in 0..k {
                out.push(phi_hat.data[m * nφ + n]);
            }
        }
        out
    }

    /// Apply averaged low-frequency modes from cluster
    fn apply_low_modes(&mut self, modes: &[Complex64], k: usize) {
        let nθ = self.grid.n_theta;
        let nφ = self.grid.n_phi;

        let mut phi_hat = SpectralField::zeros(self.grid);
        self.fft.forward(self.grid, &self.phi, &mut phi_hat);

        let mut idx = 0;
        for m in 0..k {
            for n in 0..k {
                phi_hat.data[m * nφ + n] = modes[idx];
                idx += 1;
            }
        }

        self.fft.inverse(self.grid, &phi_hat, &mut self.phi);
    }
}

/// Benchmark a cluster of N nodes
fn bench_cluster(c: &mut Criterion, nodes: usize) {
    let grid = Grid::new(64, 64, 2.0, 0.5);
    let eig = build_laplacian_spectrum(&grid);
    let fft = RustFFTBackend::new(&grid);

    let mut cluster: Vec<Node<RustFFTBackend>> =
        (0..nodes).map(|_| Node::new(&grid, &fft, &eig)).collect();

    let α = 1.0;
    let β = 1.0;
    let λ = 1.0;
    let dt = 0.01;
    let target = 0.0;

    let label = format!("tordial_cluster_{}nodes", nodes);

    c.bench_function(&label, |b| {
        b.iter(|| {
            // 1) Each node performs local spectral update
            for node in cluster.iter_mut() {
                node.step(α, β, λ, dt, target);
            }

            // 2) Exchange low-frequency modes (k=4)
            let k = 4;
            let mut accum = vec![Complex64::new(0.0, 0.0); k * k];

            for node in cluster.iter() {
                let modes = node.low_modes(k);
                for (i, v) in modes.iter().enumerate() {
                    accum[i] += v;
                }
            }

            // Average
            for v in accum.iter_mut() {
                *v /= nodes as f64;
            }

            // 3) Apply averaged modes back to each node
            for node in cluster.iter_mut() {
                node.apply_low_modes(&accum, k);
            }
        })
    });
}

fn multinode_benchmarks(c: &mut Criterion) {
    for &n in &[4, 8, 16, 32, 64] {
        bench_cluster(c, n);
    }
}

criterion_group!(benches, multinode_benchmarks);
criterion_main!(benches);