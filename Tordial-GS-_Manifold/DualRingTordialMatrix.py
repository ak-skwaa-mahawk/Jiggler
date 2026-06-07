Class CurvatureField:
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
    def compute_native_algebraic_drift(self) -> tuple:
        """
        Natively evaluates path-dependent non-commutative surface friction
        by taking cross-ring snapshot matrix variations.
        """
        # Extract mean phases as base group coordinates
        phase_a = np.mean([s["telemetry"]["raw_phase_rads"] for s in self.current_snapshots]) or 0.1
        phase_b = self.current_filtered_frequency_hz / 79.0
        
        # Calculate dynamic Lie field commutator states [A, B]
        # Mirroring the Rust edge-friction profiles natively
        c_1_5 = -0.010835 * math.sin(phase_a) * (self.node_count / 10.0)
        c_2_5 = -0.010835 * math.cos(phase_b) * (self.node_count / 10.0)
        
        # Total Frobenius-style norm proxy for global holonomy
        global_h = math.sqrt(c_1_5**2 + c_2_5**2) * 7.07
        
        return c_1_5, c_2_5, global_h