use criterion::{criterion_group, criterion_main, Criterion, black_box};
use tordial_gs_spectral::*;
use tordial_gs_spectral::fft_backend::RustFFTBackend;

/// Build GS pressure + curvature fields (same as Python prototype)
fn build_test_fields(grid: &Grid) -> (RealField, RealField, RealField) {
    let nθ = grid.n_theta;
    let nφ = grid.n_phi;

    let mut phi = RealField::zeros(grid);
    let mut rho = RealField::zeros(grid);
    let mut kap = RealField::zeros(grid);

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

    (phi, rho, kap)
}

/// Benchmark a single grid size
fn bench_grid(c: &mut Criterion, n: usize) {
    let label = format!("tordial_gs_step_{}x{}", n, n);

    let grid = Grid::new(n, n, 2.0, 0.5);
    let eig = build_laplacian_spectrum(&grid);
    let fft = RustFFTBackend::new(&grid);

    let (mut phi, rho, kap) = build_test_fields(&grid);
    let mut pid = PID::new(0.1, 0.0, 0.0);

    let α = 1.0;
    let β = 1.0;
    let λ = 1.0;
    let dt = 0.01;
    let target = 0.0;

    c.bench_function(&label, |b| {
        b.iter(|| {
            phi = tordial_gs_step(
                &grid,
                &fft,
                black_box(&phi),
                black_box(&rho),
                black_box(&kap),
                &eig,
                &mut pid,
                α,
                β,
                λ,
                dt,
                target,
            );
        })
    });
}

/// Sweep grid sizes 32² → 512²
fn grid_sweep(c: &mut Criterion) {
    for &n in &[32, 64, 128, 256, 384, 512] {
        bench_grid(c, n);
    }
}

criterion_group!(benches, grid_sweep);
criterion_main!(benches);