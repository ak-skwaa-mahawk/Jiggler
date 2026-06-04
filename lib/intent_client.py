# intent_client.py
# Simple Python client for the Sovereign Intent Engine

import grpc
from google.protobuf import empty_pb2

# Import the generated protobuf files
# Generate with: python -m grpc_tools.protoc -Iproto --python_out=. --grpc_python_out=. proto/isst_toft.proto
import issttoft_pb2
import issttoft_pb2_grpc


class IntentClient:
    def __init__(self, host: str = "localhost", port: int = 50051):
        self.channel = grpc.insecure_channel(f"{host}:{port}")
        self.stub = issttoft_pb2_grpc.InferenceServiceStub(self.channel)

    def get_all_intent_bands(self):
        """Get all current intent bands."""
        try:
            response = self.stub.GetAllIntentBands(empty_pb2.Empty())
            return response.bands
        except grpc.RpcError as e:
            print(f"gRPC error: {e.code()} - {e.details()}")
            raise

    def get_intent_band(self, band_id: str, mode: int = 0):
        """Get a specific intent band by ID and mode."""
        try:
            request = issttoft_pb2.GetIntentBandRequest(
                band_id=band_id,
                mode=mode
            )
            return self.stub.GetIntentBand(request)
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                return None  # Band does not exist
            print(f"gRPC error: {e.code()} - {e.details()}")
            raise

    def close(self):
        """Close the gRPC channel."""
        self.channel.close()


# ======================
# Example Usage
# ======================
if __name__ == "__main__":
    client = IntentClient(host="127.0.0.1")  # Change to your server IP

    try:
        # Get all intent bands
        print("Fetching all intent bands...\n")
        bands = client.get_all_intent_bands()

        print(f"Total bands: {len(bands)}\n")
        for band in bands:
            print(f"  {band.band_id} (mode {band.mode}) = {band.intent_value:.4f}  | source: {band.source}")

        print("\n" + "=" * 50 + "\n")

        # Get one specific band
        safety = client.get_intent_band("safety.checkpoints")
        if safety:
            print(f"Safety Checkpoints Intent: {safety.intent_value:.4f}")
        else:
            print("Safety Checkpoints band not found.")

    finally:
        client.close()
        print("\nConnection closed.")