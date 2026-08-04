def _attempt_node_spawning(self):
    """Enhanced κ-driven spawning with energy floor + curvature bias."""
    MIN_ENERGY_FLOOR = 420.0
    SPAWN_KAPPA_THRESHOLD = 8.0
    SPAWN_HEALTH_THRESHOLD = 62.0
    MIN_TICKS_ABOVE = 3

    spawned = 0
    avg_kappa = np.mean([
        gs_sweep.compute_gs(n.d, n.r).get("kappa_GS_T", 0.0)
        for n in self.nodes_a
    ]) if self.nodes_a else 0.0

    curvature_pressure = self.curvature_field.last_pressure
    resonance = self.curvature_field.last_resonance

    for node in self.nodes_a[:]:
        if not isinstance(node, OpenTordialAgentNode):
            continue

        gs_data = gs_sweep.compute_gs(node.d, node.r)
        current_kappa = gs_data.get("kappa_GS_T", 0.0)

        if current_kappa > SPAWN_KAPPA_THRESHOLD:
            node.high_kappa_streak += 1
        else:
            node.high_kappa_streak = 0

        health = self.compute_manifold_health_score()

        if (
            node.high_kappa_streak >= MIN_TICKS_ABOVE
            and health > SPAWN_HEALTH_THRESHOLD
            and self.global_energy > MIN_ENERGY_FLOOR
        ):
            base_prob = 0.25 + 0.06 * (current_kappa - 8.0)
            curv_boost = 0.15 * curvature_pressure + 0.10 * resonance
            prob = min(0.95, base_prob + curv_boost)

            if random.random() < prob:
                self._perform_node_fission(node)
                spawned += 1

    if spawned > 0:
        print(f"[SPAWN] {spawned} new nodes (κ+curvature boosted)")

    # Ring-level hierarchical spawning (unchanged, but now curvature-aware if you want)
    if (
        len(self.nodes_a) > 35
        and self.global_energy > 800
        and avg_kappa > 9.5
        and random.random() < 0.18
    ):
        print(f"[RING SPAWN] New ring created! Total rings: {self.rings + 1}")
        self.rings += 1