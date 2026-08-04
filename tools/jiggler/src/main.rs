use tonic::{transport::Server, Request, Response, Status};
use std::net::SocketAddr;
use std::sync::Mutex;

pub mod tordial {
    tonic::include_proto!("tordial");
}

use tordial::*;
use tordial::inference_service_server::*;

#[derive(Debug)]
pub struct GsBandRegulator {
    pub target_curvature: f64,
    pub current_belt: f64,
    pub current_throat: f64,
    pub integrated_error: f64,
    pub internal_fluid_pressure: f64,
    pub last_live_curvature: f64,
}

impl Default for GsBandRegulator {
    fn default() -> Self {
        Self {
            target_curvature: 1.4,
            current_belt: 90.576,
            current_throat: 21.857,
            integrated_error: 0.0,
            internal_fluid_pressure: 100.0,
            last_live_curvature: 1.4,
        }
    }
}

impl GsBandRegulator {
    fn evaluate_and_regulate(&mut self, flux: f64, friction: f64, mass: f64) -> f64 {
        let density_factor = self.internal_fluid_pressure / 100.0;
        let live_variance = (flux * mass) / ((1.0 + friction) * density_factor);
        let error = self.target_curvature - live_variance;
        
        self.integrated_error += error * 0.036;
        let delta_adjustment = (error * 1.5) + (self.integrated_error * 0.2);
        
        self.current_throat -= delta_adjustment * 2.0;
        self.current_belt += delta_adjustment * 5.0;
        
        self.last_live_curvature = live_variance;
        live_variance
    }

    fn compute_score(&self) -> f64 {
        let dev = (self.last_live_curvature - self.target_curvature).abs();
        (1.0 - dev / 2.0).clamp(0.0, 1.0)
    }

    fn classify_band(&self) -> GsBand {
        let score = self.compute_score();
        if score < 0.25 {
            GsBand::Subcritical
        } else if score < 0.5 {
            GsBand::Marginal
        } else if score < 0.85 {
            GsBand::Goldilocks
        } else {
            GsBand::DeepGs
        }
    }

    fn emit_state(&self) -> GsBandState {
        GsBandState {
            band: self.classify_band() as i32,
            score: self.compute_score(),
            live_curvature: self.last_live_curvature,
            target_curvature: self.target_curvature,
            belt_tension: self.current_belt,
            throat_radius: self.current_throat,
        }
    }

    fn log_state(&self, vector_id: &str) {
        let band = self.classify_band();
        let score = self.compute_score();
        let band_str = match band {
            GsBand::Subcritical => "SUBCRITICAL",
            GsBand::Marginal => "MARGINAL",
            GsBand::Goldilocks => "GOLDILOCKS",
            GsBand::DeepGs => "DEEP_GS",
            GsBand::Unknown => "UNKNOWN",
        };

        println!("📡 [GS-STATE] Tick: {}", vector_id);
        println!(
            "   GS[BAND={:<11} | S={:.3} | Curv={:.3} | Target={:.3} | Belt={:.3} | Throat={:.3}]",
            band_str, score, self.last_live_curvature, self.target_curvature, self.current_belt, self.current_throat
        );
        println!("-----------------------------------------------------------------");
    }
}

#[derive(Debug, Default)]
pub struct SovereignManifoldSubstrate {
    pub regulator: Mutex<GsBandRegulator>,
}

#[tonic::async_trait]
impl InferenceService for SovereignManifoldSubstrate {
    async fn synchronize(
        &self,
        request: Request<ManifoldTick>,
    ) -> Result<Response<SyncAck>, Status> {
        let tick = request.into_inner();
        let mut reg = self.regulator.lock().unwrap();

        if let Some(sf) = &tick.sap_flux_vector {
            reg.internal_fluid_pressure = sf.pressure_kpa;
        }

        let gs_state = if let Some(matrix) = &tick.economic_vector {
            reg.evaluate_and_regulate(
                matrix.capital_velocity,
                matrix.regulatory_drag,
                matrix.yield_generation
            );
            reg.log_state(&tick.vector_id);
            Some(reg.emit_state())
        } else {
            Some(reg.emit_state())
        };

        let reply = SyncAck {
            status: "ok".to_string(),
            gs_state,
        };

        Ok(Response::new(reply))
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let addr: SocketAddr = "127.0.0.1:50055".parse()?;
    let service = SovereignManifoldSubstrate::default();

    println!("══════════════════════════════════════════════════════════════");
    println!("🚀 [SOVEREIGN SUBSTRATE] De-Duplicated State Core Engaged: {}", addr);
    println!("══════════════════════════════════════════════════════════════");

    Server::builder()
        .add_service(InferenceServiceServer::new(service))
        .serve(addr)
        .await?;

    Ok(())
}
