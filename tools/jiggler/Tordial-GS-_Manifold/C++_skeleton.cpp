#include <vector>
#include <complex>
#include <cmath>

struct Grid {
    int Nθ, Nφ;
    double R, r;
};

struct PID {
    double Kp, Ki, Kd;
    double integral;
    double prev_error;
};

struct RealField {
    std::vector<double> f; // size Nθ*Nφ
};

struct SpectralField {
    std::vector<std::complex<double>> a; // size Nθ*Nφ
};

struct LaplacianSpectrum {
    std::vector<double> eig; // size Nθ*Nφ
};

struct FFTBackend {
    virtual void forward(const RealField& in, SpectralField& out) = 0;
    virtual void inverse(const SpectralField& in, RealField& out) = 0;
    virtual ~FFTBackend() = default;
};

inline LaplacianSpectrum build_laplacian_spectrum(const Grid& grid) {
    int Nθ = grid.Nθ, Nφ = grid.Nφ;
    LaplacianSpectrum spec;
    spec.eig.resize(Nθ * Nφ);

    auto freq = [](int k, int n) -> int {
        return (k <= n/2) ? k : k - n;
    };

    for (int i = 0; i < Nθ; ++i) {
        int m = freq(i, Nθ);
        for (int j = 0; j < Nφ; ++j) {
            int n = freq(j, Nφ);
            int idx = i * Nφ + j;
            spec.eig[idx] = -(
                (double)m * m / (grid.R * grid.R) +
                (double)n * n / (grid.r * grid.r)
            );
        }
    }
    return spec;
}

inline RealField tordial_gs_step(
    const Grid& grid,
    FFTBackend& fft,
    const RealField& phi,
    const RealField& rho_gs,
    const RealField& kappa,
    const LaplacianSpectrum& eig,
    PID& pid,
    double alpha,
    double beta,
    double lambda,
    double dt,
    double phi_target_mean
) {
    int Nθ = grid.Nθ, Nφ = grid.Nφ;
    int N = Nθ * Nφ;

    // F = α ρGS - β κ
    RealField F;
    F.f.resize(N);
    for (int i = 0; i < N; ++i) {
        F.f[i] = alpha * rho_gs.f[i] - beta * kappa.f[i];
    }

    // FFT
    SpectralField phi_hat, F_hat;
    phi_hat.a.resize(N);
    F_hat.a.resize(N);
    fft.forward(phi, phi_hat);
    fft.forward(F, F_hat);

    // steady-state Φss
    SpectralField phi_ss;
    phi_ss.a.assign(N, std::complex<double>(0.0, 0.0));
    for (int i = 0; i < N; ++i) {
        if (eig.eig[i] != 0.0) {
            phi_ss.a[i] = F_hat.a[i] / eig.eig[i];
        }
    }

    // deviation Ψ
    SpectralField psi;
    psi.a.resize(N);
    for (int i = 0; i < N; ++i) {
        psi.a[i] = phi_hat.a[i] - phi_ss.a[i];
    }

    // relax nonzero modes
    for (int i = 0; i < N; ++i) {
        double e = eig.eig[i];
        if (e != 0.0) {
            double decay = std::exp(-lambda * -e * dt);
            psi.a[i] *= decay;
        }
    }

    // PID on zero mode
    double a00 = phi_hat.a[0].real();
    double E = a00 - phi_target_mean;
    pid.integral += E * dt;
    double u = pid.Kp * E + pid.Ki * pid.integral + pid.Kd * (E - pid.prev_error) / dt;
    pid.prev_error = E;
    phi_hat.a[0] += std::complex<double>(u * dt, 0.0);

    // reconstruct Φ̂
    for (int i = 0; i < N; ++i) {
        phi_hat.a[i] = phi_ss.a[i] + psi.a[i];
    }

    // inverse FFT
    RealField phi_new;
    phi_new.f.resize(N);
    fft.inverse(phi_hat, phi_new);
    return phi_new;
}