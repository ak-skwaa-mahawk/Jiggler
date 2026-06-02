use pi_r_engine::tordial_gs::{SixCylinderBoundary, TrackingFormProof};

async fn compute_six_face_boundary(&self, req: Request<SixFaceRequest>) 
    -> Result<Response<SixFaceResponse>, Status> 
{
    let solver = SixCylinderBoundary::new(60.0);
    let state = solver.compute(req.spin, req.pressure, req.temp, req.belt_mod);
    let metrics = solver.to_toroidal_metrics(&state);
    let delta = solver.closed_loop_delta(&state);

    Ok(Response::new(SixFaceResponse {
        core_curvature: state.core.curvature,
        belt_curvature: state.belt.curvature,
        cap_curvature: state.cap.curvature,
        closed_loop_delta: delta,
        gs_density: metrics.gs_density,
        closed_loop_stability: metrics.closed_loop_stability,
    }))
}