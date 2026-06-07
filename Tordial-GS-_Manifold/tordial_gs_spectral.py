"""
tordial_gs_spectral.py

Spectral Tordial–GS solver (prototype):
- Thin torus geometry
- Fourier spectral relaxation for Φ
- GS pressure + curvature forcing
- Global PID on mean(Φ)
"""

from __future__ import annotations
import numpy as np
from dataclasses import dataclass


# ---------- Core data structures ----------

@dataclass
class Grid:
    Nθ: int
    Nφ: int
    R: float   # major radius
    r: float   # minor radius

    @property
    def shape(self) -> tuple[int, int]:
        return (self.Nθ, self.Nφ)


@dataclass
class PID:
    Kp: float
    Ki: float
    Kd: float
    integral: float = 0.0
    prev_error: float = 0.0


@dataclass
class RealField:
    f: np.ndarray  # shape (Nθ, Nφ), dtype float64


@dataclass
class SpectralField:
    a: np.ndarray  # shape (Nθ, Nφ), dtype complex128


# ---------- Spectral operators ----------

def build_laplacian_spectrum(grid: Grid) -> np.ndarray:
    """
    eig[m,n] = -(m^2/R^2 + n^2/r^2)
    using FFT frequency ordering.
    """
    Nθ, Nφ = grid.shape
    m = np.fft.fftfreq(Nθ, 1.0 / Nθ).astype(int)
    n = np.fft.fftfreq(Nφ, 1.0 / Nφ).astype(int)

    eig = np.zeros((Nθ, Nφ), dtype=np.float64)
    for i, mi in enumerate(m):
        for j, nj in enumerate(n):
            eig[i, j] = -(mi**2 / grid.R**2 + nj**2 / grid.r**2)
    return eig


def forward_fft(field: RealField) -> SpectralField:
    return SpectralField(a=np.fft.fft2(field.f))


def inverse_fft(sf: SpectralField) -> RealField:
    return RealField(f=np.fft.ifft2(sf.a).real)


# ---------- One Tordial–GS time step ----------

def tordial_gs_step(
    grid: Grid,
    Φ: RealField,
    ρGS: RealField,
    κ: RealField,
    eig: np.ndarray,
    pid: PID,
    α: float,
    β: float,
    λ: float,
    dt: float,
    Φ_target_mean: float,
) -> RealField:
    """
    One explicit spectral relaxation step for Φ:
        ∂Φ/∂t = λ(Δ_g Φ - (α ρGS - β κ)) + u(t)
    with global PID u(t) acting on mean(Φ).
    """

    # 1) Forcing field F = α ρGS - β κ
    F = RealField(f=α * ρGS.f - β * κ.f)

    # 2) FFT Φ and F
    Φ̂ = forward_fft(Φ)
    F̂ = forward_fft(F)

    # 3) Steady-state spectral solution Φ̂_ss
    Φss = SpectralField(a=np.zeros_like(Φ̂.a))
    mask = eig != 0.0
    Φss.a[mask] = F̂.a[mask] / eig[mask]  # Φ̂_ss = F̂ / λ_Δ

    # 4) Deviation Ψ̂ = Φ̂ - Φ̂_ss
    Ψ = SpectralField(a=Φ̂.a - Φss.a)

    # 5) Relax nonzero modes: Ψ̂_{m,n} *= exp(-λ * (m^2/R^2 + n^2/r^2) * dt)
    decay = np.ones_like(eig)
    decay[mask] = np.exp(-λ * (-eig[mask]) * dt)  # -eig = m^2/R^2 + n^2/r^2
    Ψ.a *= decay

    # 6) Global PID on zero mode (mean of Φ)
    a00 = Φ̂.a[0, 0].real
    E = a00 - Φ_target_mean
    pid.integral += E * dt
    u = pid.Kp * E + pid.Ki * pid.integral + pid.Kd * (E - pid.prev_error) / dt
    pid.prev_error = E
    Φ̂.a[0, 0] += u * dt  # uniform forcing → only zero mode

    # 7) Reconstruct Φ̂ = Φ̂_ss + Ψ̂
    Φ̂.a = Φss.a + Ψ.a

    # 8) Inverse FFT → physical Φ
    Φ_new = inverse_fft(Φ̂)
    return Φ_new


# ---------- Drift field (optional) ----------

def compute_drift(
    grid: Grid,
    Φ̂: SpectralField,
) -> tuple[RealField, RealField]:
    """
    Compute drift components v_θ, v_φ via spectral differentiation:
        v = -∇_g Φ
    """
    Nθ, Nφ = grid.shape
    m = np.fft.fftfreq(Nθ, 1.0 / Nθ).astype(int)
    n = np.fft.fftfreq(Nφ, 1.0 / Nφ).astype(int)

    M, N = np.meshgrid(m, n, indexing="ij")

    dΦ_dθ_hat = 1j * M * Φ̂.a
    dΦ_dφ_hat = 1j * N * Φ̂.a

    dΦ_dθ = np.fft.ifft2(dΦ_dθ_hat).real
    dΦ_dφ = np.fft.ifft2(dΦ_dφ_hat).real

    vθ = - (1.0 / grid.R**2) * dΦ_dθ
    vφ = - (1.0 / grid.r**2) * dΦ_dφ

    return RealField(f=vθ), RealField(f=vφ)


# ---------- Minimal usage example ----------

if __name__ == "__main__":
    # Grid + geometry
    grid = Grid(Nθ=64, Nφ=64, R=2.0, r=0.5)
    eig = build_laplacian_spectrum(grid)

    # Fields
    Φ = RealField(f=np.zeros(grid.shape))
    ρGS = RealField(f=np.zeros(grid.shape))
    κ = RealField(f=np.zeros(grid.shape))

    # Example GS pressure + curvature
    θ = np.linspace(0, 2 * np.pi, grid.Nθ, endpoint=False)
    φ = np.linspace(0, 2 * np.pi, grid.Nφ, endpoint=False)
    Θ, Φang = np.meshgrid(θ, φ, indexing="ij")

    ρGS.f = 1.0 + 0.2 * np.cos(Θ) * np.cos(Φang)   # ρ0 + ρ1 cosθ cosφ
    κ.f = np.ones_like(ρGS.f) * 0.5               # constant curvature

    # PID + parameters
    pid = PID(Kp=0.1, Ki=0.0, Kd=0.0)
    α, β, λ = 1.0, 1.0, 1.0
    dt = 0.01
    Φ_target_mean = 0.0

    # Time loop (prototype)
    for step in range(1000):
        Φ = tordial_gs_step(
            grid=grid,
            Φ=Φ,
            ρGS=ρGS,
            κ=κ,
            eig=eig,
            pid=pid,
            α=α,
            β=β,
            λ=λ,
            dt=dt,
            Φ_target_mean=Φ_target_mean,
        )

    # At this point Φ.f is the relaxed drift potential on the torus grid.