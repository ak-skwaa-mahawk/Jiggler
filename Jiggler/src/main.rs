use tonic::{transport::Server, Request, Response, Status};
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;
use std::time::Instant;
use rayon::prelude::*;

pub mod manifold {
    tonic::include_proto!("tordial.manifold.v1");
}

use manifold::manifold_inference_service_server::{ManifoldInferenceService, ManifoldInferenceServiceServer};
use manifold::{DriftBatchRequest, DriftBatchResponse};

pub struct SovereignManifoldSubstrate {
    processed_count: Arc<AtomicU64>,
}

impl SovereignManifoldSubstrate {
    pub fn new() -> Self {
        Self {
            processed_count: Arc::new(AtomicU64::new(0)),
        }
    }
}

#[tonic::async_trait]
impl ManifoldInferenceService for SovereignManifoldSubstrate {
    type StreamDriftBatchStream = tokio_stream::wrappers::ReceiverStream<Result<DriftBatchResponse, Status>>;

    async fn stream_drift_batch(
        &self,
        request: Request<tonic::Streaming<DriftBatchRequest>>,
    ) -> Result<Response<Self::StreamDriftBatchStream>, Status> {
        let mut stream = request.into_inner();
        let (tx, rx) = tokio::sync::mpsc::channel(128);
        let counter = Arc::clone(&self.processed_count);

        tokio::spawn(async move {
            while let Ok(Some(batch)) = stream.message().await {
                let start = Instant::now();
                let threshold = batch.threshold as f32;

                let raw_bytes = &batch.input_buffer[..];
                let floats: &[f32] = unsafe {
                    std::slice::from_raw_parts(
                        raw_bytes.as_ptr() as *const f32,
                        raw_bytes.len() / std::mem::size_of::<f32>(),
                    )
                };

                let len = floats.len();

                let out_of_bounds = floats
                    .par_iter()
                    .filter(|&&v| v.abs() > threshold)
                    .count() as u64;

                let elapsed_ms = start.elapsed().as_secs_f64() * 1000.0;
                let per_pass_ns = if len > 0 { (elapsed_ms * 1_000_000.0) / len as f64 } else { 0.0 };
                let throughput = if elapsed_ms > 0.0 { (len as f64) / (elapsed_ms / 1000.0) } else { 0.0 };

                counter.fetch_add(len as u64, Ordering::Relaxed);

                let response = DriftBatchResponse {
                    batch_id: batch.batch_id,
                    total_iterations: len as u64,
                    batch_time_ms: elapsed_ms,
                    per_pass_ns,
                    throughput_iters_per_sec: throughput,
                    out_of_bounds_trips: out_of_bounds,
                };

                if tx.send(Ok(response)).await.is_err() {
                    break;
                }
            }
        });

        Ok(Response::new(tokio_stream::wrappers::ReceiverStream::new(rx)))
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let addr = "127.0.0.1:50051".parse()?;
    let substrate = SovereignManifoldSubstrate::new();

    println!("⚡ [gRPC SERVER] Sovereign Manifold Substrate (Zero-Copy) active on {}", addr);

    Server::builder()
        .add_service(ManifoldInferenceServiceServer::new(substrate))
        .serve(addr)
        .await?;

    Ok(())
}
