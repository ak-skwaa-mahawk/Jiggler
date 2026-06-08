cat << 'EOF' > target/release/build/tordial_gs_manifold-0556f1729b90eeb3/out/combined_manifold.rs
#[allow(clippy::derive_partial_eq_without_eq)]
#[derive(Clone, PartialEq, ::prost::Message)]
pub struct GetIntentBandRequest {
    #[prost(string, tag = "1")]
    pub band_id: ::prost::alloc::string::String,
}
#[allow(clippy::derive_partial_eq_without_eq)]
#[derive(Clone, PartialEq, ::prost::Message)]
pub struct GetAllIntentBandsRequest {}
#[allow(clippy::derive_partial_eq_without_eq)]
#[derive(Clone, PartialEq, ::prost::Message)]
pub struct GetAllIntentBandsResponse {
    #[prost(message, repeated, tag = "1")]
    pub bands: ::prost::alloc::vec::Vec<IntentBand>,
}
#[allow(clippy::derive_partial_eq_without_eq)]
#[derive(Clone, PartialEq, ::prost::Message)]
pub struct StreamIntentUpdatesRequest {}
#[allow(clippy::derive_partial_eq_without_eq)]
#[derive(Clone, PartialEq, ::prost::Message)]
pub struct IntentUpdate {
    #[prost(string, tag = "1")]
    pub update_id: ::prost::alloc::string::String,
    #[prost(string, tag = "2")]
    pub payload: ::prost::alloc::string::String,
}
#[allow(clippy::derive_partial_eq_without_eq)]
#[derive(Clone, PartialEq, ::prost::Message)]
pub struct HandshakeRequest {
    #[prost(string, tag = "1")]
    pub client_id: ::prost::alloc::string::String,
    #[prost(string, tag = "2")]
    pub client_type: ::prost::alloc::string::String,
    #[prost(bool, tag = "3")]
    pub sovereign_claim: bool,
}
#[allow(clippy::derive_partial_eq_without_eq)]
#[derive(Clone, PartialEq, ::prost::Message)]
pub struct HandshakeResponse {
    #[prost(string, tag = "1")]
    pub status: ::prost::alloc::string::String,
    #[prost(string, tag = "2")]
    pub version: ::prost::alloc::string::String,
    #[prost(string, tag = "3")]
    pub mesh_status: ::prost::alloc::string::String,
    #[prost(string, tag = "4")]
    pub flamekeeper_note: ::prost::alloc::string::String,
}
#[allow(clippy::derive_partial_eq_without_eq)]
#[derive(Clone, PartialEq, ::prost::Message)]
pub struct IntentBand {
    #[prost(string, tag = "1")]
    pub band_id: ::prost::alloc::string::String,
    #[prost(double, tag = "2")]
    pub energy_delta: f64,
    #[prost(double, tag = "3")]
    pub spin: f64,
    #[prost(double, tag = "4")]
    pub temp: f64,
}
#[allow(clippy::derive_partial_eq_without_eq)]
#[derive(Clone, PartialEq, ::prost::Message)]
pub struct Vector3D {
    #[prost(double, tag = "1")]
    pub x: f64,
    #[prost(double, tag = "2")]
    pub y: f64,
    #[prost(double, tag = "3")]
    pub z: f64,
}
#[allow(clippy::derive_partial_eq_without_eq)]
#[derive(Clone, PartialEq, ::prost::Message)]
pub struct VectorPayload {
    #[prost(string, tag = "1")]
    pub vector_id: ::prost::alloc::string::String,
    #[prost(message, optional, tag = "2")]
    pub velocity_vector: ::core::option::Option<Vector3D>,
    #[prost(double, tag = "3")]
    pub throat_radius: f64,
    #[prost(double, tag = "4")]
    pub magnetic_coupling: f64,
}
#[allow(clippy::derive_partial_eq_without_eq)]
#[derive(Clone, PartialEq, ::prost::Message)]
pub struct SubstrateMetricsResponse {
    #[prost(string, tag = "1")]
    pub status: ::prost::alloc::string::String,
    #[prost(string, tag = "2")]
    pub version: ::prost::alloc::string::String,
    #[prost(string, tag = "3")]
    pub mesh_status: ::prost::alloc::string::String,
    #[prost(bool, tag = "4")]
    pub processing_stable: bool,
    #[prost(uint64, tag = "5")]
    pub execution_ticks: u64,
}

pub mod inference_service_server {
    use tonic::codegen::*;
    #[tonic::async_trait]
    pub trait InferenceService: Send + Sync + 'static {
        async fn handshake(&self, request: tonic::Request<super::HandshakeRequest>) -> Result<tonic::Response<super::HandshakeResponse>, tonic::Status>;
        async fn get_intent_band(&self, request: tonic::Request<super::GetIntentBandRequest>) -> Result<tonic::Response<super::IntentBand>, tonic::Status>;
        async fn get_all_intent_bands(&self, request: tonic::Request<super::GetAllIntentBandsRequest>) -> Result<tonic::Response<super::GetAllIntentBandsResponse>, tonic::Status>;
        type StreamIntentUpdatesStream: futures_core::Stream<Item = Result<super::IntentUpdate, tonic::Status>> + Send + 'static;
        async fn stream_intent_updates(&self, request: tonic::Request<super::StreamIntentUpdatesRequest>) -> Result<tonic::Response<Self::StreamIntentUpdatesStream>, tonic::Status>;
    }
    #[derive(Debug)]
    pub struct InferenceServiceServer<T: InferenceService> { inner: Arc<T> }
    impl<T: InferenceService> InferenceServiceServer<T> {
        pub fn new(inner: T) -> Self { Self { inner: Arc::new(inner) } }
    }
    impl<T: InferenceService, B: Body> tonic::codegen::Service<http::Request<B>> for InferenceServiceServer<T> where B: Send + 'static, B::Error: Into<StdError> + Send + 'static {
        type Response = http::Response<tonic::body::BoxBody>;
        type Error = std::convert::Infallible;
        type Future = BoxFuture<Self::Response, Self::Error>;
        fn poll_ready(&mut self, _cx: &mut Context<'_>) -> Poll<Result<(), Self::Error>> { Poll::Ready(Ok(())) }
        fn call(&mut self, req: http::Request<B>) -> Self::Future {
            let inner = self.inner.clone();
            match req.uri().path() {
                "/combined_manifold.InferenceService/Handshake" => {
                    struct HandshakeSvc<T: InferenceService>(pub Arc<T>);
                    impl<T: InferenceService> tonic::server::UnaryService<super::HandshakeRequest> for HandshakeSvc<T> {
                        type Response = super::HandshakeResponse;
                        type Future = BoxFuture<tonic::Response<Self::Response>, tonic::Status>;
                        fn call(&mut self, request: tonic::Request<super::HandshakeRequest>) -> Self::Future {
                            let inner = self.0.clone();
                            Box::pin(async move { (*inner).handshake(request).await })
                        }
                    }
                    let accept_compression_encodings = tonic::codec::CompressionEncodings::default();
                    let send_compression_encodings = tonic::codec::CompressionEncodings::default();
                    let mut grpc = tonic::server::Grpc::new(tonic::codec::ProstCodec::default()).with_interceptor(std::convert::Infallible::from).with_accept_compression_encodings(accept_compression_encodings).with_send_compression_encodings(send_compression_encodings);
                    let res = grpc.unary(HandshakeSvc(inner), req);
                    Box::pin(async move { Ok(res.await) })
                }
                "/combined_manifold.InferenceService/GetIntentBand" => {
                    struct GetIntentBandSvc<T: InferenceService>(pub Arc<T>);
                    impl<T: InferenceService> tonic::server::UnaryService<super::GetIntentBandRequest> for GetIntentBandSvc<T> {
                        type Response = super::IntentBand;
                        type Future = BoxFuture<tonic::Response<Self::Response>, tonic::Status>;
                        fn call(&mut self, request: tonic::Request<super::GetIntentBandRequest>) -> Self::Future {
                            let inner = self.0.clone();
                            Box::pin(async move { (*inner).get_intent_band(request).await })
                        }
                    }
                    let accept_compression_encodings = tonic::codec::CompressionEncodings::default();
                    let send_compression_encodings = tonic::codec::CompressionEncodings::default();
                    let mut grpc = tonic::server::Grpc::new(tonic::codec::ProstCodec::default()).with_interceptor(std::convert::Infallible::from).with_accept_compression_encodings(accept_compression_encodings).with_send_compression_encodings(send_compression_encodings);
                    let res = grpc.unary(GetIntentBandSvc(inner), req);
                    Box::pin(async move { Ok(res.await) })
                }
                _ => Box::pin(async move {
                    Ok(http::Response::builder().status(200).header("grpc-status", "12").header("content-type", "application/grpc").body(empty_body()).unwrap())
                }),
            }
        }
    }
}

pub mod manifold_controller_server {
    use tonic::codegen::*;
    #[tonic::async_trait]
    pub trait ManifoldController: Send + Sync + 'static {
        async fn synchronize_vector(&self, request: tonic::Request<super::VectorPayload>) -> Result<tonic::Response<super::SubstrateMetricsResponse>, tonic::Status>;
    }
    #[derive(Debug)]
    pub struct ManifoldControllerServer<T: ManifoldController> { inner: Arc<T> }
    impl<T: ManifoldController> ManifoldControllerServer<T> {
        pub fn new(inner: T) -> Self { Self { inner: Arc::new(inner) } }
    }
    impl<T: ManifoldController, B: Body> tonic::codegen::Service<http::Request<B>> for ManifoldControllerServer<T> where B: Send + 'static, B::Error: Into<StdError> + Send + 'static {
        type Response = http::Response<tonic::body::BoxBody>;
        type Error = std::convert::Infallible;
        type Future = BoxFuture<Self::Response, Self::Error>;
        fn poll_ready(&mut self, _cx: &mut Context<'_>) -> Poll<Result<(), Self::Error>> { Poll::Ready(Ok(())) }
        fn call(&mut self, req: http::Request<B>) -> Self::Future {
            let inner = self.inner.clone();
            match req.uri().path() {
                "/combined_manifold.ManifoldController/SynchronizeVector" => {
                    struct SynchronizeVectorSvc<T: ManifoldController>(pub Arc<T>);
                    impl<T: ManifoldController> tonic::server::UnaryService<super::VectorPayload> for SynchronizeVectorSvc<T> {
                        type Response = super::SubstrateMetricsResponse;
                        type Future = BoxFuture<tonic::Response<Self::Response>, tonic::Status>;
                        fn call(&mut self, request: tonic::Request<super::VectorPayload>) -> Self::Future {
                            let inner = self.0.clone();
                            Box::pin(async move { (*inner).synchronize_vector(request).await })
                        }
                    }
                    let accept_compression_encodings = tonic::codec::CompressionEncodings::default();
                    let send_compression_encodings = tonic::codec::CompressionEncodings::default();
                    let mut grpc = tonic::server::Grpc::new(tonic::codec::ProstCodec::default()).with_interceptor(std::convert::Infallible::from).with_accept_compression_encodings(accept_compression_encodings).with_send_compression_encodings(send_compression_encodings);
                    let res = grpc.unary(SynchronizeVectorSvc(inner), req);
                    Box::pin(async move { Ok(res.await) })
                }
                _ => Box::pin(async move {
                    Ok(http::Response::builder().status(200).header("grpc-status", "12").header("content-type", "application/grpc").body(empty_body()).unwrap())
                }),
            }
        }
    }
}
EOF
