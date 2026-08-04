use std::pin::Pin;
use std::time::Instant;
use tokio_stream::{Stream, StreamExt};
use tonic::{Request, Response, Status, Streaming};
use rayon::prelude::*;

pub mod manifold_proto {
    tonic::include_proto!("tordial.manifold.v1");
}

use manifold_proto::manifold_inference_service_server::ManifoldInferenceService;
use manifold_proto::{DriftBatchRequest, DriftBatchResponse};

#[derive(Default)]
pub struct ManifoldInferenceServerImpl;

#[tonic::async_trait]
impl ManifoldInferenceService for ManifoldInferenceServerImpl {
    type StreamDriftBatchStream = Pin<
        Box<dyn Stream<Item = Result<DriftBatchResponse, Status>> + Send + 'static>
    >;

    async fn StreamDriftBatch(
        &self,
        request: Request<Streaming<DriftBatchRequest>>,
    ) -> Result<Response<Self::StreamDriftBatchStream>, Status> {
        let mut in_stream = request.into_inner();

        let output_stream = async_stream::try_stream! {
            while let Some(req) = in_stream.next().await {
                let req = req?;
                let batch_id = req.batch_id;
                let threshold = req.threshold;
                let mut input_data = req.input_buffer;
                let total_iterations = input_data.len() as u64;

                if total_iterations == 0 {
                    continue;
                }

                // Offload synchronous Rayon parallel computation off the async event loop
                let (violations, batch_time_ms) = tokio::task::spawn_blocking(move || {
                    let start = Instant::now();

                    let violations = input_data
                        .par_iter_mut()
                        .map(|val| {
                            let mutated = *val * 1.0001;
                            *val = mutated;
                            if mutated.abs() > threshold { 1u64 } else { 0u64 }
                        })
                        .sum::<u64>();

                    let elapsed = start.elapsed();
                    let ms = elapsed.as_secs_f64() * 1000.0;
                    (violations, ms)
                })
                .await
                .map_err(|e| Status::internal(format!("Compute task panicked: {}", e)))?;

                let per_pass_ns = (batch_time_ms * 1_000_000.0) / (total_iterations as f64);
                let throughput = (total_iterations as f64) / (batch_time_ms / 1000.0);

                yield DriftBatchResponse {
                    batch_id,
                    total_iterations,
                    batch_time_ms,
                    per_pass_ns,
                    throughput_iters_per_sec: throughput,
                    out_of_bounds_trips: violations,
                };
            }
        };

        Ok(Response::new(Box::pin(output_stream)))
    }
}
