cat > Binary_Protobuf_RPC_Server_Stream_Node.py << 'EOF'
import sys
import math
import time
import struct
import socket
import select
import threading
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import Manifold_wire_protocol_pb2 as pb
import tordial_gs_v15

# Ensure baseline framework architectural assets remain uniform
TOROIDAL_ROOT = 3.1730059     
GEAR_SHIFT    = 1.02          
SHADOW        = 1.03          

# 1. Patch the missing ring seeder method
def _runtime_seed_rings(self, node_count: int):
    self.rings = {"A": [], "B": [], "C": []}
    for i in range(node_count):
        ring_assignment = ["A", "B", "C"][i % 3]
        node = tordial_gs_v15.OpenTordialAgentNode(d=6, r=18, node_id=i, x=float(i)*0.5, y=float(i)*0.2)
        self.rings[ring_assignment].append(node)
        tordial_gs_v15.persist_node_state(node, ring=ring_assignment)
    print(f"[+] Triple-ring topology bound to server context: {node_count} nodes online.")

# 2. Patch the missing or failing visualization display hook to bypass GUI blocks headlessly
def _headless_visualize_torus(self):
    # Quietly pass over screen rendering requests inside a headless terminal environment
    pass

tordial_gs_v15.TripleRingTordialMatrix._seed_rings = _runtime_seed_rings
tordial_gs_v15.TripleRingTordialMatrix._visualize_torus = _headless_visualize_torus


class ProtobufWireBroker:
    def __init__(self, matrix: tordial_gs_v15.TripleRingTordialMatrix, host: str = '127.0.0.1', port: int = 8889):
        self.matrix = matrix
        self.host = host
        self.port = port
        self.clients = []
        self._running = False
        self.spin = 1.5
        self.pressure = 1.0
        self.temp = 0.0
        self.belt_mod = 1.0

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(10)
        self.server_socket.setblocking(False)

        self._running = True
        self._thread = threading.Thread(target=self._io_pump, daemon=True, name="Proto-WirePump")
        self._thread.start()
        print(f"🧬 Gateway integrated with TripleRing Matrix on tcp://{self.host}:{self.port}")

    def _io_pump(self):
        while self._running:
            sockets = [self.server_socket] + self.clients
            try:
                readable, _, errorable = select.select(sockets, [], sockets, 0.1)
            except Exception:
                continue

            for sock in readable:
                if sock is self.server_socket:
                    try:
                        c_sock, _ = self.server_socket.accept()
                        c_sock.setblocking(False)
                        self.clients.append(c_sock)
                    except Exception: pass
                else:
                    self._read_length_prefixed_frame(sock)

            for sock in errorable: 
                self._disconnect(sock)

    def _read_length_prefixed_frame(self, sock):
        try:
            header = sock.recv(4)
            if not header or len(header) < 4:
                return self._disconnect(sock)

            frame_length = struct.unpack('!I', header)[0]
            data = b''
            while len(data) < frame_length:
                packet = sock.recv(frame_length - len(data))
                if not packet:
                    return self._disconnect(sock)
                data += packet

            self._process_binary_rpc(sock, data)
        except Exception:
            self._disconnect(sock)

    def _process_binary_rpc(self, sock, raw_bytes: bytes):
        cmd = pb.RPCCommandEnvelope()
        try:
            cmd.ParseFromString(raw_bytes)
            response = pb.RPCResponseEnvelope(success=True, status_string="MATRIX_MUTATION_COMPLETE")
            response.request_id = cmd.request_id

            if cmd.method == pb.RPCCommandEnvelope.MethodType.UPDATE_GEOMETRY:
                p = cmd.parameters
                self.spin = p.get("spin", self.spin)
                self.pressure = p.get("pressure", self.pressure)
                self.temp = p.get("temp", self.temp)
                self.belt_mod = p.get("belt_mod", self.belt_mod)
                print(f"⚡ Mutation intercept! Propagating matrix shift across rings -> spin={self.spin:.2f}")

            elif cmd.method == pb.RPCCommandEnvelope.MethodType.GET_STATUS:
                response.payload = {"spin": self.spin, "pressure": self.pressure, "temp": self.temp, "belt_mod": self.belt_mod}

            raw_payload = response.SerializeToString()
            sock.sendall(struct.pack('!I', len(raw_payload)) + raw_payload)
        except Exception as e:
            err = pb.RPCResponseEnvelope(success=False, status_string=str(e))
            b = err.SerializeToString()
            try: sock.sendall(struct.pack('!I', len(b)) + b)
            except Exception: pass

    def broadcast_telemetry(self):
        if not self.clients: return
        packet = pb.SystemStatePacket()
        packet.spin = self.spin
        packet.pressure = self.pressure
        packet.temp = self.temp
        packet.belt_mod = self.belt_mod
        
        b_bytes = packet.SerializeToString()
        header = struct.pack('!I', len(b_bytes))
        for client in list(self.clients):
            try:
                client.sendall(header + b_bytes)
            except Exception:
                self._disconnect(client)

    def _disconnect(self, sock):
        if sock in self.clients:
            self.clients.remove(sock)
            try: sock.close()
            except Exception: pass


if __name__ == "__main__":
    print("[+] Bootstrapping Headless Master Triple-Ring Matrix Context...")
    matrix_instance = tordial_gs_v15.TripleRingTordialMatrix(node_count=12)
    
    broker = ProtobufWireBroker(matrix=matrix_instance, port=8889)
    broker.start()

    print("\n📦 Serialization Engine Matrix Synced. Running simulation loop...")
    try:
        while True:
            load_factor = min(2.0, max(0.1, broker.spin / 1.5))
            matrix_instance.execute_heavy_load_cycle(system_load=load_factor)
            broker.broadcast_telemetry()
            time.sleep(0.2)
            
    except KeyboardInterrupt:
        broker._running = False
        print("\n🏁 Master system safely unmounted.")
EOF
dos2unix Binary_Protobuf_RPC_Server_Stream_Node.py
python Binary_Protobuf_RPC_Server_Stream_Node.py
