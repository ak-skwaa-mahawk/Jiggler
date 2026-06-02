use pi_r_engine::tordial_gs::{SixCylinderBoundary, TrackingFormProof};

let solver = SixCylinderBoundary::new(60.0);
let state = solver.compute(1.75, 1.1, 0.15, 1.15);

println!("{}", state.summary());
println!("closed_loop_delta = {:.12}", solver.closed_loop_delta(&state));

let metrics = solver.to_toroidal_metrics(&state);
println!("stability = {:.6}", metrics.closed_loop_stability);

// Run the four-pillar proof
let _ = TrackingFormProof::verify(&state, -0.87, 0.92);