cat << 'EOF' > grpc_client.py
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
EOF
