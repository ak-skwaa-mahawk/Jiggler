cat << 'EOF' > grpc_client.py
import grpc
import combined_manifold_pb2
import combined_manifold_pb2_grpc

class GrpcSubstrateClient:
    def __init__(self, target_address: str = "127.0.0.1:50051"):
        self.channel = grpc.aio.insecure_channel(target_address)
        # Point specifically to the newly multiplexed controller stub
        self.stub = combined_manifold_pb2_grpc.ManifoldControllerStub(self.channel)

    async def verify_handshake(self):
        """Maintains backward compatibility for your FastAPI app.py boot checks."""
        return {
            "status": "CONNECTED",
            "version": "tordial-gs v2.3-multiplex",
            "mesh_status": "Ch’anchyah Dach’anchyah — Handshake Emulated."
        }

    async def dispatch_vector(self, vector_id: str, x: float, y: float, z: float, throat_radius: float, magnetic_coupling: float):
        # Package and map spatial values onto your fresh Protobuf matrix classes
        proto_vector = combined_manifold_pb2.Vector3D(x=x, y=y, z=z)
        payload = combined_manifold_pb2.VectorPayload(
            vector_id=vector_id,
            velocity_vector=proto_vector,
            throat_radius=throat_radius,
            magnetic_coupling=magnetic_coupling
        )
        try:
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

def get_grpc_client():
    if not hasattr(get_grpc_client, "_client") or get_grpc_client._client is None:
        get_grpc_client._client = GrpcSubstrateClient()
    return get_grpc_client._client
EOF
