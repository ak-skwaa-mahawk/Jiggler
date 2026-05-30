import sys
import math
import time
import struct
import socket
import select
import threading
from dataclasses import dataclass, field
from typing import List, Dict, Optional

# Import compiled protocol specifications generated via protoc
try:
    import manifold_wire_protocol_pb2 as pb
except ImportError:
    print("❌ Error: Missing generated code extensions. Run 'protoc --python_out=. manifold_wire_protocol.proto'")
    sys.exit(1)

# Ensure baseline framework architectural assets remain uniform
TOROIDAL_ROOT = 3.1730059     
GEAR_SHIFT    = 1.02          
SHADOW        = 1.03          

@dataclass
class FaceGeometry:
    axis: str; label: str; role: str
    curvature: float; radius: float; throat: float

@dataclass
class SystemState:
    spin: float; pressure: float; temp: float; belt_mod: float
    core: FaceGeometry = field(default=None)
    belt: FaceGeometry = field(default=None)
    cap: FaceGeometry = field(default=None)
    timestamp: float = field(default_factory=time.time)


class SixCylinderBoundary:
    def __init__(self, base_radius: float = 60.0):
        self.base_radius = base_radius
        self._lock = threading.Lock()
        self._last_state: Optional[SystemState] = None

    def compute(self, spin=1.5, pressure=1.0, temp=0.0, belt_mod=1.0) -> SystemState:
        spin = max(0.01, spin); pressure = max(0.01, pressure)
        temp = max(0.0, min(1.0, temp)); belt_mod = max(0.1, belt_mod)

        core_curv = (TOROIDAL_ROOT / math.pi) * spin * SHADOW
        core_r = (self.base_radius * pressure) / core_curv
        core_throat = core_r * (1.0 - 0.15 * temp)
        core = FaceGeometry('core', 'FRONT / REAR', 'Intake · Exhaust', core_curv, core_r, core_throat)

        belt_curv = core_curv * GEAR_SHIFT * belt_mod
        belt_r = core_r * belt_curv
        belt = FaceGeometry('belt', 'LEFT / RIGHT', 'Expansion Belt', belt_curv, belt_r, belt_r)

        cap_curv = 1.0 / (belt_curv * SHADOW)
        cap_r = belt_r * cap_curv
        cap = FaceGeometry('cap', 'TOP / BOTTOM', 'Containment Caps', cap_curv, cap_r, cap_r)

        state = SystemState(spin, pressure, temp, belt_mod, core, belt, cap)
        with self._lock: self._last_state = state
        return state

    def closed_loop_delta(self, state: SystemState) -> float:
        return state.belt.curvature * state.cap.curvature * SHADOW - 1.0


# ── Binary Wire Protocol Network Implementation ──────────────────────────────

class ProtobufWireBroker:
    """
    Manages low-overhead async network communication using length-prefixed 
    binary framing to transmit and receive protocol messages.
    """
    def __init__(self, solver: SixCylinderBoundary, host: str = '127.0.0.1', port: int = 8889):
        self.solver = solver
        self.host = host
        self.port = port
        self.clients = []
        self._running = False

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(10)
        self.server_socket.setblocking(False)
        
        self._running = True
        self._thread = threading.Thread(target=self._io_pump, daemon=True, name="Proto-WirePump")
        self._thread.start()
        print(f"🧬 Protobuf Binary Wire Gateway operational on tcp://{self.host}:{self.port}")

    def _io_pump(self):
        while self._running:
            sockets = [self.server_socket] + self.clients
            try:
                readable, _, errorable = select.select(sockets, [], sockets, 0.1)
            except (ValueError, socket.error):
                continue

            for sock in readable:
                if sock is self.server_socket:
                    try:
                        c_sock, _ = self.server_socket.accept()
                        c_sock.setblocking(False)
                        self.clients.append(c_sock)
                    except socket.error: pass
                else:
                    self._read_length_prefixed_frame(sock)

            for sock in errorable: 
                self._disconnect(sock)

    def _read_length_prefixed_frame(self, sock):
        """Extracts length-prefixed bytes from the network stream buffer."""
        try:
            # 4-byte big-endian integer length prefix header
            header = sock.recv(4)
            if not header or len(header) < 4:
                self._disconnect(sock)
                return
                
            frame_length = struct.unpack('!I', header)[0]
            
            # Read complete remaining message sequence length
            data = b''
            while len(data) < frame_length:
                packet = sock.recv(frame_length - len(data))
                if not packet:
                    self._disconnect(sock)
                    return
                data += packet
                
            self._process_binary_rpc(sock, data)
        except socket.error:
            self._disconnect(sock)

    def _process_binary_rpc(self, sock, raw_bytes: bytes):
        """Unpacks incoming commands using proto definitions."""
        cmd = pb.RPCCommandEnvelope()
        try:
            cmd.ParseFromString(raw_bytes)
            
            response = pb.RPCResponseEnvelope()
            response.request_id = cmd.request_id
            
            if cmd.method == pb.RPCCommandEnvelope.MethodType.UPDATE_GEOMETRY:
                curr = self.solver.last_state or self.solver.compute()
                
                # Fetch dictionary elements from protobuf structural map
                p = cmd.parameters
                self.solver.compute(
                    spin=p.get("spin", curr.spin),
                    pressure=p.get("pressure", curr.pressure),
                    temp=p.get("temp", curr.temp),
                    belt_mod=p.get("belt_mod", curr.belt_mod)
                )
                
                response.status_string = "PROTO_MUTATION_COMPLETE"
                response.success = True
                
            elif cmd.method == pb.RPCCommandEnvelope.MethodType.GET_STATUS:
                curr = self.solver.last_state or self.solver.compute()
                response.success = True
                response.payload["spin"] = curr.spin
                response.payload["pressure"] = curr.pressure
                response.payload["temp"] = curr.temp
                
            else:
                response.status_string = "METHOD_REJECTED"
                response.success = False
                
            self._send_length_prefixed_msg(sock, response)
        except Exception as e:
            err = pb.RPCResponseEnvelope(success=False, status_string=f"Malformed frame: {str(e)}")
            self._send_length_prefixed_msg(sock, err)

    def broadcast_telemetry(self, state: SystemState, drift_delta: float):
        """Serializes and streams system states out to connected clients."""
        if not self.clients: return

        # Instantiate protobuf state tracking schemas
        packet = pb.SystemStatePacket()
        packet.timestamp = state.timestamp
        packet.spin = state.spin
        packet.pressure = state.pressure
        packet.temp = state.temp
        packet.belt_mod = state.belt_mod

        # Compile sub-message object entities 
        for dest, src in [(packet.core, state.core), (packet.belt, state.belt), (packet.cap, state.cap)]:
            dest.axis = src.axis
            dest.label = src.label
            dest.role = src.role
            dest.curvature = src.curvature
            dest.radius = src.radius
            dest.throat = src.throat

        packet.stability_metrics.gs_density = abs(drift_delta) * 100 + 1.0
        packet.stability_metrics.curvature_mean = (state.core.curvature + state.belt.curvature + state.cap.curvature) / 3.0
        packet.stability_metrics.closed_loop_stability = 1.0 - abs(drift_delta)

        serialized_bytes = packet.SerializeToString()
        
        # Dispatch serialized bytes across active interface connections
        for client in list(self.clients):
            try:
                # Prefix payload size header blocks to enforce framing boundaries
                header = struct.pack('!I', len(serialized_bytes))
                client.sendall(header + serialized_bytes)
            except socket.error:
                self._disconnect(client)

    def _send_length_prefixed_msg(self, sock, message):
        raw_payload = message.SerializeToString()
        header = struct.pack('!I', len(raw_payload))
        try: 
            sock.sendall(header + raw_payload)
        except socket.error: 
            self._disconnect(sock)

    def _disconnect(self, sock):
        if sock in self.clients:
            self.clients.remove(sock)
            try: sock.close()
            except socket.error: pass


# ── Verification Execution Pipeline Loop ──────────────────────────────────────

if __name__ == "__main__":
    print("🚀 Initializing TGS Binary Protobuf Loop...")
    solver_instance = SixCylinderBoundary(base_radius=50.0)
    broker = ProtobufWireBroker(solver=solver_instance, port=8889)
    broker.start()

    print("\n📦 Serialization Engine Synced. Inter-Manifold network nodes can now parse data.")
    print("Press Ctrl+C to unmount the system node.\n")

    try:
        while True:
            # Recompute localized manifold dimensions
            current_state = solver_instance.last_state or solver_instance.compute(spin=1.5, pressure=1.0)
            delta_deviation = solver_instance.closed_loop_delta(current_state)
            
            # Pack, serialize, and broadcast the binary payload
            broker.broadcast_telemetry(current_state, delta_deviation)
            
            time.sleep(0.01266)  # Track repository target 79 Hz window updates
            
    except KeyboardInterrupt:

print("\n⚡ Unmounting communication node...")finally:broker._running = Falseprint("🏁 Protocols safely unmounted.")