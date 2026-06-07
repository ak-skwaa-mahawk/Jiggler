class CurvatureField:
    """
    Global curvature field C(t) driven by:
      - avg sigma_T
      - avg kappa
      - global energy
      - logical error rate
    Produces:
      - curvature_pressure in [0, 1.2]
      - resonance in [0, 1.0]
    """
    def __init__(self):
        self.last_pressure = 0.0
        self.last_resonance = 0.0

    def compute(
        self,
        avg_sigma: float,
        avg_kappa: float,
        global_energy: float,
        logical_error_rate: float,
        node_count: int,
    ) -> tuple[float, float]:
        # Normalize inputs
        kappa_norm = max(0.0, min(1.0, avg_kappa / 12.0))          # κ ~ [0,12]
        energy_norm = max(0.0, min(1.0, global_energy / 3000.0))   # energy ~ [0,3000]
        sigma_norm = max(-1.0, min(1.0, avg_sigma / 500.0))        # σ_T ~ [-500,500]
        ler = max(0.0, min(1.0, logical_error_rate))

        # Base curvature: high κ + high energy + positive σ_T → more pressure
        base_pressure = 0.45 * kappa_norm + 0.35 * energy_norm + 0.20 * max(0.0, sigma_norm)

        # Error dampening: high LER reduces effective curvature
        pressure = base_pressure * (1.0 - 0.6 * ler)

        # Node crowding: too many nodes slightly increase curvature (packing pressure)
        crowding = max(0.0, min(0.3, (node_count - 24) / 80.0))
        pressure += crowding

        # Resonance: more sensitive to κ and σ_T, but strongly damped by errors
        resonance = (0.55 * kappa_norm + 0.35 * max(0.0, sigma_norm) + 0.10 * energy_norm)
        resonance *= (1.0 - 0.8 * ler)

        # Clamp ranges
        pressure = max(0.0, min(1.2, pressure))
        resonance = max(0.0, min(1.0, resonance))

        # Light smoothing
        alpha = 0.35
        pressure = alpha * pressure + (1 - alpha) * self.last_pressure
        resonance = alpha * resonance + (1 - alpha) * self.last_resonance

        self.last_pressure = pressure
        self.last_resonance = resonance
        return pressure, resonance