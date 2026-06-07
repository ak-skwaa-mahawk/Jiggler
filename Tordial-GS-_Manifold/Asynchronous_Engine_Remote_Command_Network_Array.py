import sys
import math
import time
import json
import struct
import random
import asyncio
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

# ── Global Repository Constants ──────────────────────────────────────────────
TOROIDAL_ROOT = 3.1730059     
GEAR_SHIFT    = 1.02          
SHADOW        = 1.03          


# ── Core Geometric Architecture ───────────────────────────────────────────────

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
        return SystemState(spin, pressure, temp, belt_mod, core, belt, cap)

    def closed_loop_delta(self, state: SystemState) -> float:
        return state.belt.curvature * state.cap.curvature * SHADOW - 1.0


# ── 6D Fluid Kinematics Engine ────────────────────────────────────────────────

@dataclass
class Particle6D:
    x: float = 0.0; y: float = 0.0; z: float = 0.0
    w: float = 0.0; v: float = 0.0; u: float = 0.0
    dx: float = 0.0; dy: float = 0.0; dz: float = 0.0
    dw: float = 0.0; dv: float = 0.0; du: float = 0.0
    phase: int = 0            # 0=INTAKE, 1=TRANSIT, 2=EXHAUST, 3=RETURN
    life: int = 0
    max_life: int = 280

class PhysicsEngine6D:
    def __init__(self, count: int = 200):
        self.count = count
        self.particles: List[Particle6D] = []
        self._rng = random.Random(42)

    def _spawn(self, radius: float) -> Particle6D:
        theta = self._rng.uniform(0, 2 * math.pi)
        return Particle6D(
            x=radius * self._rng.uniform(0.6, 0.98) * math.cos(theta),
            y=radius * self._rng.uniform(0.6, 0.98) * math.sin(theta),
            z=self._rng.uniform(-radius * 0.5, radius * 0.5),
            w=self._rng.uniform(-1.0, 1.0), v=self._rng.uniform(-1.0, 1.0)
        )

    def step(self, state: SystemState, dt: float = 0.05):
        throat = state.core.throat * 0.5
        belt_r = state.belt.radius

        while len(self.particles) < self.count:
            self.particles.append(self._spawn(belt_r))

        live = []
        for p in self.particles:
            p.life += 1
            if p.life > p.max_life:
                live.append(self._spawn(belt_r))
                continue

            r = math.hypot(p.x, p.y)
            ax = ay = az = aw = av = 0.0

            if p.phase == 0:     # INTAKE
                target_factor = throat / (r + 1e-9)
                ax = -1.5 * (p.x / belt_r) * target_factor
                ay = -1.5 * (p.y / belt_r) * target_factor
                if r < throat * 1.1: p.phase = 1
            elif p.phase == 1:   # TRANSIT
                ax = -1.0 * p.y * state.spin * GEAR_SHIFT
                ay = 1.0 * p.x * state.spin * GEAR_SHIFT
                if r > belt_r * 0.75: p.phase = 2
            elif p.phase == 2:   # EXHAUST
                ax = 2.0 * (p.x / (r + 1e-9)) * SHADOW
                ay = 2.0 * (p.y / (r + 1e-9)) * SHADOW
                if r > belt_r * 0.95: p.phase = 3
            elif p.phase == 3:   # RETURN
                ax = -2.5 * p.x; ay = -2.5 * p.y
                if r < throat * 1.4: p.phase = 0

            p.dx += ax * dt; p.dy += ay * dt
            drag = 1.0 - (0.04 * state.pressure)
            p.dx *= drag; p.dy *= drag
            p.x += p.dx; p.y += p.dy
            live.append(p)
            
        self.particles = live


# ── Async Telemetry Pipeline & JSON-RPC Broker ────────────────────────────────

class UnifiedAsyncControlBroker:
    """
    Combined communication layer. Operates an outbound asynchronous telemetry 
    broadcast stream while concurrently listening for incoming control RPC payloads.
    """
    def __init__(self, log_filepath: str = "async_system.log", base_port: int = 8890, rpc_port: int = 8891):
        self.log_filepath = log_filepath
        self.base_port = base_port
        self.rpc_port = rpc_port
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=300)
        self.stream_clients = set()
        
        # Concurrent dictionary for state sharing across different async loop context tasks
        self.shared_runtime_modifiers = {"spin": 1.5, "pressure": 1.0, "temp": 0.15, "belt_mod": 1.0}
        self.is_running = False

    def enqueue_frame_sync(self, state: SystemState, delta: float, engine: PhysicsEngine6D):
        """Thread-safe synchronous data ingestion mechanism hook."""
        frame = {
            "timestamp": state.timestamp, "spin": state.spin, "pressure": state.pressure,
            "temp": state.temp, "stability": 1.0 - abs(delta), "particle_count": len(engine.particles)
        }
        try:
            self.queue.put_nowait(frame)
        except asyncio.QueueFull:
            pass

    async def start(self):
        self.is_running = True
        with open(self.log_filepath, "a", encoding="utf-8") as f:
            f.write(f"\n# --- ENGINE SYSTEM ONLINE: {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")

        # Spawn non-blocking logging workers
        self._disk_task = asyncio.create_task(self._disk_worker())
        self._net_task = asyncio.create_task(self._broadcast_worker())

        # Start the Telemetry Output Stream Server
        self._stream_server = await asyncio.start_server(self._accept_stream_client, "127.0.0.1", self.base_port)
        # Start the Inbound Remote Procedure Call (RPC) Server
        self._rpc_server = await asyncio.start_server(self._handle_rpc_connection, "127.0.0.1", self.rpc_port)
        
        print(f"📡 Telemetry Stream active: tcp://127.0.0.1:{self.base_port}")
        print(f"🎛️ Asynchronous RPC Interface listening: tcp://127.0.0.1:{self.rpc_port}")

    async def _accept_stream_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.stream_clients.add(writer)
        try:
            while self.is_running: await asyncio.sleep(1.0)
        except asyncio.CancelledError: pass
        finally:
            self.stream_clients.remove(writer)
            writer.close()
            await writer.wait_closed()

    async def _disk_worker(self):
        while self.is_running:
            frame = await self.queue.get()
            try:
                serialized = json.dumps(frame) + "\n"
                await asyncio.to_thread(self._write_to_disk, serialized)
            finally: self.queue.task_done()

    def _write_to_disk(self, data: str):
        with open(self.log_filepath, "a", encoding="utf-8") as f: f.write(data)

    async def _broadcast_worker(self):
        while self.is_running:
            frame = await self.queue.get()
            try:
                if not self.stream_clients: continue
                payload = (json.dumps(frame) + "\n").encode('utf-8')
                header = struct.pack('!I', len(payload))
                full_frame = header + payload
                
                disconnected = set()
                for writer in self.stream_clients:
                    try:
                        writer.write(full_frame)
                        await writer.drain()
                    except (socket.error, ConnectionResetError): disconnected.add(writer)
                for w in disconnected: self.stream_clients.discard(w)
            finally: self.queue.task_done()

    async def _handle_rpc_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Processes incoming requests matching a JSON-RPC format model specification."""
        try:
            while self.is_running:
                data = await reader.readline()
                if not data: break
                
                try:
                    req = json.loads(data.decode('utf-8'))
                    method = req.get("method")
                    params = req.get("params", {})
                    req_id = req.get("id")
                    
                    if method == "update_vectors":
                        # Directly overwrite atomic variables shared with the primary solver loop
                        for key in self.shared_runtime_modifiers.keys():
                            if key in params:
                                self.shared_runtime_modifiers[key] = max(0.01, float(params[key]))
                        resp = {"jsonrpc": "2.0", "result": "PARAMETERS_MUTATED_OK", "id": req_id}
                    elif method == "get_telemetry":
                        resp = {"jsonrpc": "2.0", "result": self.shared_runtime_modifiers, "id": req_id}
                    else:
                        resp = {"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": req_id}
                except Exception as e:

resp = {"jsonrpc": "2.0", "error": {"code": -32700, "message": f"Parse Failure: {str(e)}"}, "id": None}writer.write((json.dumps(resp) + "\n").encode('utf-8'))await writer.drain()except ConnectionResetError: passfinally:writer.close()await writer.wait_closed()async def stop(self):self.is_running = Falseself._disk_task.cancel()self._net_task.cancel()if hasattr(self, '_stream_server'): self._stream_server.close()if hasattr(self, '_rpc_server'): self._rpc_server.close()── Asynchronous Primary Engine Execution Loop ───────────────────────────────async def run_79hz_simulation(broker: UnifiedAsyncControlBroker):solver = SixCylinderBoundary(base_radius=55.0)engine = PhysicsEngine6D(count=250)target_period = 1.0 / 79.0print(f"⏱️ 6D Physics Array integrated into event loop. Execution locked to 79 Hz.")print("Press Ctrl+C to disconnect from runtime container routines.\n")frame = 0try:while True:start_cycle = asyncio.get_event_loop().time()# 1. Fetch parameters that may have been modified by the RPC serverm = broker.shared_runtime_modifiers# 2. Compute multi-axis geometry stepsstate = solver.compute(spin=m["spin"], pressure=m["pressure"], temp=m["temp"], belt_mod=m["belt_mod"])delta = solver.closed_loop_delta(state)# 3. Advance particle accelerations inside the updated geometric spaceengine.step(state, dt=0.04)# 4. Offload current state data directly onto the background broker queuebroker.enqueue_frame_sync(state, delta, engine)if frame % 160 == 0:print(f"[{frame:05d}] Runtime Spin: {state.spin:.2f} | Temp: {state.temp:.2f} | Drift: {delta:+.6f} | Live Engine Mass: {len(engine.particles)}")frame += 1# High-precision execution loop timing clampelapsed = asyncio.get_event_loop().time() - start_cycleremainder = target_period - elapsedif remainder > 0:await asyncio.sleep(remainder)else:await asyncio.sleep(0)except asyncio.CancelledError: passasync def main():broker = UnifiedAsyncControlBroker()await broker.start()try:await run_79hz_simulation(broker)except KeyboardInterrupt:print("\n⚡ Interrupt hook received. Dismantling event processing pipelines...")finally:await broker.stop()print("🏁 Systems unmounted safely.")