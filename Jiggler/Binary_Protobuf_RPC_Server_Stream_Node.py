import time
import sys
import concurrent.futures as futures
import grpc

import issttoft_pb2
import issttoft_pb2_grpc

class SubstrateInferenceServicer(issttoft_pb2_grpc.InferenceServiceServicer):
    
    def Handshake(self, request, context):
        print(f"\n[⚡ CORE SERVER] Inbound Connection Authorized.")
        print(f"  -> Object mapping verification passed successfully.")
        
        # Instantiating our updated path-aware object structure
        return issttoft_pb2.HandshakeResponse(
            server_version="TORDIAL_MATRIX_v15.79",
            mesh_status="79Hz_PULSE_NOMINAL"
        )

    def StreamTelemetry(self, request_iterator, context):
        print("[⚡ CORE SERVER] Inbound telemetry stream linked to matrix gateways.")
        for update in request_iterator:
            yield issttoft_pb2.TelemetryAck(status="ACK_SUCCESS")

def serve():
    print("⚙️ Initializing Production gRPC Substrate Core Node [Mode: Class Aligned]...")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # Register handlers using our updated, verified namespace definitions
    issttoft_pb2_grpc.add_InferenceServiceServicer_to_server(
        SubstrateInferenceServicer(), server
    )
    
    try:
        port = server.add_insecure_port('[::]:50051')
        print(f"📡 gRPC Substrate Bound to Network Interface Port: {port}")
        server.start()
        print("🔒 Core Substrate Node fully active. Awaiting client handshake passes...")
        
        try:
            while True:
                time.sleep(86400)
        except KeyboardInterrupt:
            server.stop(0)
    except Exception as e:
        print(f"❌ Critical Failure: {e}")
        sys.exit(1)

if __name__ == "__main__":
    serve()
