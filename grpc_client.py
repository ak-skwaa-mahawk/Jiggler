import sys
import grpc
import proto.issttoft_pb2 as issttoft_pb2
import proto.issttoft_pb2_grpc as issttoft_pb2_grpc

def fire_core_handshake():
    print("[🔌] Spinning up HTTP/2 network channel to local Rust substrate...")
    server_target = "localhost:50051"
    channel = grpc.insecure_channel(server_target)
    stub = issttoft_pb2_grpc.InferenceServiceStub(channel)
    
    handshake_payload = issttoft_pb2.HandshakeRequest(
        client_id="Flask_Manifold_Frontend",
        client_type="DASHBOARD_CONTROLLER",
        sovereign_claim="FLAMEKEEPER_EXEC_2026"
    )
    
    try:
        print(f"[🚀] Routing HandshakeRequest vectors to {server_target}...")
        response = stub.Handshake(handshake_payload)
        print("\n==========================================================")
        print(" 🌌 TORDIAL-GS SUBSTRATE VECTOR HANDSHAKE CONFIRMED")
        print("==========================================================")
        print(f"  Server Version:  {response.server_version}")
        print(f"  Server Time:     {response.server_time}")
        print(f"  Mesh Status:     {response.mesh_status}")
        print(f"  Flamekeeper Msg: {response.flamekeeper_note}")
        print("==========================================================\n")
    except grpc.RpcError as err:
        print(f"❌ Handshake Aborted! Code: {err.code()} | Detail: {err.details()}", file=sys.stderr)

if __name__ == "__main__":
    fire_core_handshake()
