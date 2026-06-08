import grpc
import tordial_manifold_pb2
import tordial_manifold_pb2_grpc

class GrpcSubstrateClient:
    def __init__(self, target_address: str = "127.0.0.1:50051"):
        self.channel = grpc.aio.insecure_channel(target_address)
        self.stub = tordial_manifold_pb2_grpc.ManifoldControllerStub(self.channel)

    async def dispatch_vector(self, vector_id: str, x: float, y: float, z: float, throat_radius: float, magnetic_coupling: float):
        # 1. Structure the nested 3D coordinate proto message
        proto_vector = tordial_manifold_pb2.Vector3D(x=x, y=y, z=z)
        
        # 2. Compile the parent master payload package
        payload = tordial_manifold_pb2.VectorPayload(
            vector_id=vector_id,
            velocity_vector=proto_vector,
            throat_radius=throat_radius,
            magnetic_coupling=magnetic_coupling
        )
        
        try:
            # 3. Stream across the HTTP/2 lane asynchronously
            response = await self.stub.SynchronizeVector(payload)
            return {
                "status": response.status,
                "version": response.version,
                "mesh_status": response.mesh_status,
                "processing_stable": response.processing_stable,
                "execution_ticks": response.execution_ticks
            }
        except grpc.RpcError as e:
            return {"status": "DISCONNECTED", "error": str(e.details())}

    async def close(self):
        await self.channel.close()


import sys
import grpc
import proto.issttoft_pb2 as issttoft_pb2
import proto.issttoft_pb2_grpc as issttoft_pb2_grpc

class GrpcSubstrateClient:
    def __init__(self, target="localhost:50051"):
        self.target = target
        # Create an async gRPC channel loop to prevent thread blocks in FastAPI
        self.channel = grpc.aio.insecure_channel(self.target)
        self.stub = issttoft_pb2_grpc.InferenceServiceStub(self.channel)

    async def verify_handshake(self) -> dict:
        """Dispatches an initialization ping straight to the Rust microservice."""
        request = issttoft_pb2.HandshakeRequest(
            client_id="FastAPI_Resonance_Mesh",
            client_type="DASHBOARD_CONTROLLER",
            sovereign_claim="FLAMEKEEPER_EXEC_2026"
        )
        try:
            response = await self.stub.Handshake(request)
            return {
                "status": "CONNECTED",
                "version": response.server_version,
                "mesh_status": response.mesh_status,
                "flamekeeper_note": response.flamekeeper_note
            }
        except grpc.RpcError as e:
            return {
                "status": "UNAVAILABLE",
                "detail": f"Code: {e.code()} | Details: {e.details()}"
            }

    async def close(self):
        await self.channel.close()

# Singleton instance placeholder for application lifecycle mounting
client = None

def get_grpc_client() -> GrpcSubstrateClient:
    global client
    if client is None:
        client = GrpcSubstrateClient()
    return client
