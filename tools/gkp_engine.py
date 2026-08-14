#!/usr/bin/env python3
import numpy as np

class GKPSqueezedEngine:
    """
    Gottesman-Kitaev-Preskill (GKP) Bosonic Stabilizer Engine.
    Protects continuous-variable harmonic oscillator modes by mapping
    phase-space position (q) and momentum (p) shift errors onto a 2√π grid lattice.
    """
    def __init__(self, delta: float = 0.1):
        self.delta = delta
        self.lattice_period = 2.0 * np.sqrt(np.pi)  # 2√π spacing
        self.half_period = np.sqrt(np.pi)          # √π spacing
        self.max_correctable = np.sqrt(np.pi) / 2.0 # √π / 2 error threshold

    def generate_approximate_gkp_state(self, logical_bit: int = 0, num_peaks: int = 5) -> dict:
        grid_q = np.linspace(-3 * self.lattice_period, 3 * self.lattice_period, 2000)
        psi = np.zeros_like(grid_q)

        for s in range(-num_peaks, num_peaks + 1):
            peak_center = (2 * s + logical_bit) * self.half_period
            envelope = np.exp(- (self.delta * peak_center)**2 / 2.0)
            peak = np.exp(- ((grid_q - peak_center)**2) / (2.0 * (self.delta**2)))
            psi += envelope * peak

        # Use np.trapezoid (NumPy 2.0+) with fallback to np.trapz
        trapz_fn = getattr(np, 'trapezoid', getattr(np, 'trapz', None))
        psi /= np.sqrt(trapz_fn(psi**2, grid_q))
        
        return {"grid_q": grid_q, "psi": psi, "logical_bit": logical_bit}

    def measure_syndrome_and_correct(self, delta_q: float, delta_p: float) -> dict:
        syndrome_q = np.fmod(delta_q + self.lattice_period / 2.0, self.lattice_period) - self.lattice_period / 2.0
        syndrome_p = np.fmod(delta_p + self.lattice_period / 2.0, self.lattice_period) - self.lattice_period / 2.0

        correction_q = -syndrome_q
        correction_p = -syndrome_p

        residual_q = delta_q + correction_q
        residual_p = delta_p + correction_p

        q_correctable = abs(delta_q) < self.max_correctable
        p_correctable = abs(delta_p) < self.max_correctable
        is_fully_recovered = q_correctable and p_correctable

        return {
            "injected_delta_q": delta_q,
            "injected_delta_p": delta_p,
            "syndrome_q": syndrome_q,
            "syndrome_p": syndrome_p,
            "correction_q": correction_q,
            "correction_p": correction_p,
            "residual_q": residual_q,
            "residual_p": residual_p,
            "within_threshold": is_fully_recovered,
            "error_threshold_limit": self.max_correctable
        }


if __name__ == "__main__":
    print("--- Gottesman-Kitaev-Preskill (GKP) Stabilizer Test ---")
    gkp = GKPSqueezedEngine(delta=0.1)

    state_0 = gkp.generate_approximate_gkp_state(logical_bit=0)
    print(f"[+] Generated Finite-Squeezed GKP |0>_L State (Δ = 0.1)")

    delta_q_test = 0.35
    delta_p_test = -0.40
    res = gkp.measure_syndrome_and_correct(delta_q_test, delta_p_test)

    print("\n--- Phase-Space Shift Correction ---")
    print(f"Injected Displacement: δq = {res['injected_delta_q']:.3f} | δp = {res['injected_delta_p']:.3f}")
    print(f"Measured Syndromes:    Sq = {res['syndrome_q']:.3f} | Sp = {res['syndrome_p']:.3f}")
    print(f"Correction Applied:    Cq = {res['correction_q']:.3f} | Cp = {res['correction_p']:.3f}")
    print(f"Residual Quadrature:   R_q = {res['residual_q']:.6f} | R_p = {res['residual_p']:.6f}")
    print(f"Lattice Recovered:     {res['within_threshold']} (Threshold < {res['error_threshold_limit']:.3f})")
