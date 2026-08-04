def execute_heavy_load_cycle(self, system_load: float = 1.0):
    self.current_tick += 1

    # --- compute global GS stats BEFORE node updates ---
    if self.nodes_a:
        sigmas = [getattr(n, 'sigma_T', 0.0) for n in self.nodes_a if hasattr(n, 'sigma_T')]
        avg_sigma = float(np.mean(sigmas)) if sigmas else 0.0
        avg_kappa = float(np.mean([
            gs_sweep.compute_gs(n.d, n.r).get("kappa_GS_T", 0.0)
            for n in self.nodes_a
        ]))
    else:
        avg_sigma = 0.0
        avg_kappa = 0.0

    # global curvature field
    curvature_pressure, resonance = self.curvature_field.compute(
        avg_sigma=avg_sigma,
        avg_kappa=avg_kappa,
        global_energy=self.global_energy,
        logical_error_rate=self.logical_error_rate,
        node_count=len(self.nodes_a),
    )

    # --- node GS updates using curvature field ---
    for node in self.nodes_a:
        if isinstance(node, OpenTordialAgentNode):
            sigma = node.compute_and_update_gs(curvature_pressure, resonance)
            node.sigma_T = sigma

        if getattr(node, 'sigma_T', 0.0) < -450:
            self._perform_node_fission(node)

    # Dynamic spawning (enhanced loophole)
    self._attempt_node_spawning()

    # Surface Code
    self.corrections_made = self.apply_error_correction()

    # Anyon tracking
    self.anyons = [
        Anyon(s[1], s[0], self.nodes_a[s[0]].drift_phase)
        for s in self.measure_syndromes()
    ]
    for a in self.anyons:
        a.lifetime += 1

    wrapped = sum(1 for a in self.anyons if a.lifetime > 25)
    self.logical_error_rate = (
        min(1.0, wrapped / max(1, len(self.anyons)) * 0.7)
        if self.anyons else 0.0
    )

    # κ-boosted energy recovery (now using updated κ)
    avg_kappa = float(np.mean([
        gs_sweep.compute_gs(n.d, n.r).get("kappa_GS_T", 0.0)
        for n in self.nodes_a
    ])) if self.nodes_a else 0.0
    self.global_energy += 12.0 + 0.8 * avg_kappa - len(self.nodes_a) * 0.11

    health = self.compute_manifold_health_score()
    print(
        f"[CYCLE {self.current_tick:3d}] Nodes: {len(self.nodes_a):3d} | Rings: {self.rings} | "
        f"Energy: {self.global_energy:7.1f} | LER: {self.logical_error_rate:.4f} | "
        f"CurvP: {curvature_pressure:4.2f} | Res: {resonance:4.2f} | Health: {health:5.1f}"
    )