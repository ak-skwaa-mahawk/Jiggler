cd \~/Tordial-GS-_Manifold
cat > manifold_client.py << 'CLIENT_EOF'
#!/usr/bin/env python3
"""
Minimal client to interface with Binary_Protobuf_RPC_Server_Stream_Node.py
"""
import socket
import struct
import time

try:
    import manifold_wire_protocol_pb2 as pb
except ImportError:
    print("ERROR: manifold_wire_protocol_pb2.py not found. Run the protoc steps first.")
    exit(1)

HOST = '127.0.0.1'
PORT = 8889

def send_rpc(method, parameters=None, request_id=1):
    """Send an RPC command and get response."""
    cmd = pb.RPCCommandEnvelope()
    cmd.request_id = request_id
    cmd.method = method
    if parameters:
        cmd.parameters.update(parameters)

    payload = cmd.SerializeToString()
    header = struct.pack('!I', len(payload))

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(header + payload)

        # Read response
        header = s.recv(4)
        if len(header) < 4:
            return None
        length = struct.unpack('!I', header)[0]
        data = b''
        while len(data) < length:
            chunk = s.recv(length - len(data))
            if not chunk:
                break
            data += chunk

        resp = pb.RPCResponseEnvelope()
        resp.ParseFromString(data)
        return resp

def listen_telemetry(duration=10):
    """Listen for broadcast SystemStatePacket messages."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        print(f"[Client] Connected to {HOST}:{PORT} for telemetry...")
        start = time.time()
        while time.time() - start < duration:
            try:
                header = s.recv(4)
                if len(header) < 4:
                    continue
                length = struct.unpack('!I', header)[0]
                data = b''
                while len(data) < length:
                    chunk = s.recv(length - len(data))
                    if not chunk:
                        break
                    data += chunk

                packet = pb.SystemStatePacket()
                packet.ParseFromString(data)
                print(f"[Telemetry] spin={packet.spin:.3f} pressure={packet.pressure:.3f} "
                      f"temp={packet.temp:.3f} belt_mod={packet.belt_mod:.3f}")
            except Exception as e:
                print(f"[Client] Error: {e}")
                break

if __name__ == "__main__":
    print("=== Manifold Protobuf Client ===")
    print("1. Get current status")
    resp = send_rpc(pb.RPCCommandEnvelope.MethodType.GET_STATUS)
    if resp:
        print(f"Status: success={resp.success}, {resp.status_string}")

    print("\n2. Update geometry (example)")
    params = {"spin": 2.0, "pressure": 1.2, "temp": 0.3, "belt_mod": 1.1}
    resp = send_rpc(pb.RPCCommandEnvelope.MethodType.UPDATE_GEOMETRY, params)
    if resp:
        print(f"Update result: {resp.status_string}")

    print("\n3. Listening for telemetry for 8 seconds...")
    listen_telemetry(duration=8)
CLIENT_EOF