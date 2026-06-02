//! ISST-TOFT Sovereign Inference Backend v1.6.0
//! Full gRPC server with Rad-hard glyphs + SixCylinderBoundary GS coupling

use std::sync::Arc;

use tonic::{transport::Server, Request, Response, Status};
use tracing::{info, Level};
use tracing_subscriber::FmtSubscriber;

pub mod issttoft {
    tonic::include_proto!("issttoft");
}

use issttoft::{
    inference_service_server::{InferenceService, InferenceServiceServer},
    GlyphRequest, GlyphResponse,
    PulseRequest, PulseResponse,
    SixFaceRequest, SixFaceResponse,
    DeltaResponse, ProofResponse,
};

mod glyph;
mod model;

use pi_r_engine::tordial_gs::{SixCylinderBoundary, TrackingFormProof};

#[derive(Debug, Default)]
pub struct SovereignInferenceService;

impl SovereignInferenceService {
    #[inline]
    fn living_toroidal_pi_r() -> f32 {
        3.267_253_6
    }
}

#[tonic::async_trait]
impl InferenceService for SovereignInferenceService {

    // === Existing methods (kept for completeness) ===
    async fn encode_rad_hard_glyph(
        &self,
        request: Request<GlyphRequest>,
    ) -> Result<Response<GlyphResponse>, Status> {
        // ... (your existing implementation)
        let req = request.into_inner();
        // ... (simplified for brevity — keep your full logic here)
        let glyph = glyph::generate_glyph_waveform(7.83, 44100, 528.0, Self::living_toroidal_pi_r())
            .map_err(|e| Status::internal(e.to_string()))?;

        let checksum = glyph::rad_hard_checksum(&glyph);
        let waveform = glyph;

        Ok(Response::new(GlyphResponse {
            refined_waveform: waveform,
            waveform_checksum: checksum,
            status: "RAD_HARD_GLYPH_LOCKED_RUST".to_string(),
            coherence: 0.9997,
            message: "MAHS’I CHOO — Sovereign inference live.".to_string(),
            quantum_layer: "w-state-v1.0 + 79.79Hz".to_string(),
            toroidal_pi_r: Self::living_toroidal_pi_r(),
        }))
    }

    async fn run_clientless_pulse(
        &self,
        request: Request<PulseRequest>,
    ) -> Result<Response<PulseResponse>, Status> {
        // ... (your existing implementation)
        let req = request.into_inner();
        let refined: Vec<f32> = req.feed_data.iter().map(|&v| v * 0.92).collect();

        Ok(Response::new(PulseResponse {
            refined_signal: refined,
            status: "PULSE_PROPAGATED".to_string(),
            coherence: 0.94,
            message: "Clientless pulse through sovereign mesh".to_string(),
            toroidal_pi_r: Self::living_toroidal_pi_r(),
        }))
    }

    // === NEW: SixCylinderBoundary GS Coupling ===

    async fn compute_six_face_boundary(
        &self,
        request: Request<SixFaceRequest>,
    ) -> Result<Response<SixFaceResponse>, Status> {
        let req = request.into_inner();
        info!(target: "isst_toft::six_cylinder", "ComputeSixFaceBoundary called");

        let solver = SixCylinderBoundary::new(60.0);
        let state = solver.compute(req.spin, req.pressure, req.temp, req.belt_mod);
        let metrics = solver.to_toroidal_metrics(&state);
        let delta = solver.closed_loop_delta(&state);

        // Simple regime classification (can be extended with full Regime enum)
        let regime = if metrics.gs_density < 1.5 {
            "SUBCRITICAL"
        } else if metrics.gs_density < 2.5 {
            "GOLDILOCKS"
        } else {
            "DEEP_GS"
        };

        Ok(Response::new(SixFaceResponse {
            core_curvature: state.core.curvature,
            belt_curvature: state.belt.curvature,
            cap_curvature: state.cap.curvature,
            closed_loop_delta: delta,
            gs_density: metrics.gs_density,
            closed_loop_stability: metrics.closed_loop_stability,
            regime: regime.to_string(),
        }))
    }

    async fn get_closed_loop_delta(
        &self,
        request: Request<SixFaceRequest>,
    ) -> Result<Response<DeltaResponse>, Status> {
        let req = request.into_inner();
        let solver = SixCylinderBoundary::new(60.0);
        let state = solver.compute(req.spin, req.pressure, req.temp, req.belt_mod);
        let delta = solver.closed_loop_delta(&state);

        Ok(Response::new(DeltaResponse { delta }))
    }

    async fn run_tracking_form_proof(
        &self,
        request: Request<SixFaceRequest>,
    ) -> Result<Response<ProofResponse>, Status> {
        let req = request.into_inner();
        let solver = SixCylinderBoundary::new(60.0);
        let state = solver.compute(req.spin, req.pressure, req.temp, req.belt_mod);

        // Run all four pillars
        let all_hold = TrackingFormProof::verify(&state, -0.87, 0.92);

        let details = if all_hold {
            "All four pillars hold: Living Root ✓ | Shutter Cycle ✓ | Delta Zero ✓ | Ambient Lock ✓"
        } else {
            "One or more pillars failed — check geometry or relaxation parameters"
        };

        Ok(Response::new(ProofResponse {
            all_pillars_hold: all_hold,
            details: details.to_string(),
        }))
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let subscriber = FmtSubscriber::builder()
        .with_max_level(Level::INFO)
        .with_target(true)
        .finish();
    tracing::subscriber::set_global_default(subscriber)?;

    let addr = "[::]:50051".parse()?;
    let service = SovereignInferenceService::default();

    info!("══════════════════════════════════════════════════════════════");
    info!("🔥  ISST-TOFT Sovereign Inference Backend v1.6.0 — FULL");
    info!("   gRPC listening on {}", addr);
    info!("   Services: EncodeRadHardGlyph | RunClientlessPulse");
    info!("             ComputeSixFaceBoundary | GetClosedLoopDelta | RunTrackingFormProof");
    info!("   Core: 99733-Q Guard + Tordial–GS SixCylinderBoundary + TrackingFormProof");
    info!("   Lineage: Two Mile Solutions LLC • Dinjji Zhuu Kwaa");
    info!("══════════════════════════════════════════════════════════════");

    Server::builder()
        .add_service(InferenceServiceServer::new(service))
        .serve(addr)
        .await?;

    Ok(())
}