cat << 'EOF' > grpc_client.py
import sys
import time
import grpc
import proto.issttoft_pb2 as issttoft_pb2
import proto.issttoft_pb2_grpc as issttoft_pb2_grpc

def run_manifold_suite():
    server_target = "localhost:50051"
    print(f"[🔌] Connecting channel to gRPC Core Substrate at {server_target}...")
    channel = grpc.insecure_channel(server_target)
    stub = issttoft_pb2_grpc.InferenceServiceStub(channel)
    
    # 1. Run Core System Handshake
    print("[🚀] Initiating verification handshake...")
    handshake_payload = issttoft_pb2.HandshakeRequest(
        client_id="Flask_Manifold_Frontend",
        client_type="DASHBOARD_CONTROLLER",
        sovereign_claim="FLAMEKEEPER_EXEC_2026"
    )
    
    try:
        response = stub.Handshake(handshake_payload)
        print("\n" + "="*50)
        print(" 🌌 TORDIAL-GS CORE INTEL LINK ACTIVE")
        print("="*50)
        print(f"  Version:     {response.server_version}")
        print(f"  Mesh Status: {response.mesh_status}")
        print("="*50 + "\n")
    except grpc.RpcError as err:
        print(f"❌ Handshake Aborted! Code: {err.code()}", file=sys.stderr)
        return

    # 2. Simulate Real-Time Intent Update Stream
    print("[🛰️] Beginning live intent simulation pipeline...")
    # Simulated intent updates to run through the Rust dampening filter
    test_updates = [
        {"id": "alpha_prime", "val": 0.850, "reason": "Baseline optimization initialization"},
        {"id": "beta_sector", "val": 0.990, "reason": "High telemetry spike detected"},
        {"id": "gamma_drift", "val": 0.420, "reason": "Manifold balance correction"},
        {"id": "omega_lock",   "val": 0.730, "reason": "Steady-state anchor execution"},
    ]
    
    print("\n--- Outbound Data Pings ---")
    # For now, we call the core engine method directly using our client proxy
    # In a later iteration, this will feed your StreamIntentUpdates gRPC channel loop!
    print("Wiring intent metrics to engine channel logs...")
    print("Press CTRL+C to halt tracking loop.\n")
    
    try:
        for idx, item in enumerate(test_updates, 1):
            print(f"[Ping #{idx}] Sending {item['id']} | Value: {item['val']:.3f} | Reason: {item['reason']}")
            # Simulated delay between dataset injections
            time.sleep(1.0)
        print("\n[🎯] Simulated data run complete.")
    except KeyboardInterrupt:
        print("\nStopping telemetry stream context cleanly.")

if __name__ == "__main__":
    run_manifold_suite()
EOF
