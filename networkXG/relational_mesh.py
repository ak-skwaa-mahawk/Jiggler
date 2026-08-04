# pseudocode from relational_mesh.py + visualize_soliton_route.py
def propagate_soliton(state_vector, source_node, target_nodes):
    u = generate_kdv_soliton(amplitude=state_vector.resonance_delta,  # from π_r surplus
                             speed=4.0 * k**2,
                             forcing_hz=79.79)
    
    for step in range(propagation_steps):
        u = rk4_step(kdv_forced_damped(u, gamma=adaptive_damping))  # Thermodynamic_Audit.py
        # E8 lattice routing
        next_node = e8_lattice_route(current_node, target_nodes, u.phase)
        if resonance_match(u, node_state[next_node]):
            deliver_living_wave(u, payload=state_vector)  # never static data