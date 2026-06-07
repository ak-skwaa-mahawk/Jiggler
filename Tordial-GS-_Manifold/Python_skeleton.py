import numpy as np

class Grid:
    def __init__(self, Nθ, Nφ, R, r):
        self.Nθ = Nθ
        self.Nφ = Nφ
        self.R = R
        self.r = r
        self.dθ = 2 * np.pi / Nθ
        self.dφ = 2 * np.pi / Nφ

class PID:
    def __init__(self, Kp, Ki, Kd):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.integral = 0.0
        self.prev_error = 0.0

class SpectralField:
    def __init__(self, Nθ, Nφ):
        self.a = np.zeros((Nθ, Nφ), dtype=np.complex128)

class RealField:
    def __init__(self, Nθ, Nφ):
        self.f = np.zeros((Nθ, Nφ), dtype=np.float64)

def build_laplacian_spectrum(grid: Grid):
    Nθ, Nφ = grid.Nθ, grid.Nφ
    m = np.fft.fftfreq(Nθ, 1.0 / Nθ).astype(int)
    n = np.fft.fftfreq(Nφ, 1.0 / Nφ).astype(int)
    eig = np.zeros((Nθ, Nφ))
    for i, mi in enumerate(m):
        for j, nj in enumerate(n):
            eig[i, j] = -(mi**2 / grid.R**2 + nj**2 / grid.r**2)
    return eig

def forward_fft(field: RealField) -> SpectralField:
    sf = SpectralField(*field.f.shape)
    sf.a = np.fft.fft2(field.f)
    return sf

def inverse_fft(sf: SpectralField) -> RealField:
    rf = RealField(*sf.a.shape)
    rf.f = np.fft.ifft2(sf.a).real
    return rf

def tordial_gs_step(grid: Grid,
                    Φ: RealField,
                    ρGS: RealField,
                    κ: RealField,
                    eig: np.ndarray,
                    pid: PID,
                    α: float,
                    β: float,
                    λ: float,
                    dt: float,
                    Φ_target_mean: float) -> RealField:
    # 1) F = α ρGS - β κ
    F = RealField(grid.Nθ, grid.Nφ)
    F.f = α * ρGS.f - β * κ.f

    # 2) FFT
    Φ̂ = forward_fft(Φ)
    F̂ = forward_fft(F)

    # 3) steady-state Φss
    Φss = SpectralField(grid.Nθ, grid.Nφ)
    Φss.a[:] = 0.0
    mask = eig != 0.0
    Φss.a[mask] = F̂.a[mask] / eig[mask]

    # 4) deviation Ψ
    Ψ = SpectralField(grid.Nθ, grid.Nφ)
    Ψ.a = Φ̂.a - Φss.a

    # 5) relax nonzero modes
    decay = np.exp(-λ * (-eig) * dt)
    decay[~mask] = 1.0  # zero mode untouched here
    Ψ.a *= decay

    # 6) PID on zero mode
    a00 = Φ̂.a[0, 0].real
    E = a00 - Φ_target_mean
    pid.integral += E * dt
    u = pid.Kp * E + pid.Ki * pid.integral + pid.Kd * (E - pid.prev_error) / dt
    pid.prev_error = E
    Φ̂.a[0, 0] += u * dt

    # 7) reconstruct Φ̂
    Φ̂.a = Φss.a + Ψ.a

    # 8) inverse FFT
    Φ_new = inverse_fft(Φ̂)
    return Φ_new