# intent_client.py

import grpc
from google.protobuf import empty_pb2

import issttoft_pb2
import issttoft_pb2_grpc


class IntentClient:
    def __init__(self, host="localhost", port=50051):
        self.channel = grpc.insecure_channel(f"{host}:{port}")
        self.stub = issttoft_pb2_grpc.InferenceServiceStub(self.channel)

    # === Existing methods remain the same ===

    def stream_intent_updates(self):
        """Returns an iterator for real-time intent updates."""
        return self.stub.StreamIntentUpdates(empty_pb2.Empty())

    def close(self):
        self.channel.close()


# Example usage
if __name__ == "__main__":
    client = IntentClient(host="127.0.0.1")

    print("Listening for intent updates...\n")
    try:
        for update in client.stream_intent_updates():
            print(f"[{update.timestamp}] {update.band_id} → {update.intent_value:.4f} ({update.reason})")
    except KeyboardInterrupt:
        print("\nStopped streaming.")
    finally:
        client.close()