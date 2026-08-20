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
    max_life: int = 1200

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
        throat = state.core.throat * 0.6
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

            if p.phase == 0:  # INTAKE: Radial inward suction + spin induction
                nx, ny = p.x / (r + 1e-9), p.y / (r + 1e-9)
                ax = -25.0 * nx - 5.0 * ny * state.spin
                ay = -25.0 * ny + 5.0 * nx * state.spin
                if r <= throat * 1.25:
                    p.phase = 1

            elif p.phase == 1:  # TRANSIT: Vortex angular acceleration + centrifugal expansion
                tx, ty = -p.y / (r + 1e-9), p.x / (r + 1e-9)
                nx, ny = p.x / (r + 1e-9), p.y / (r + 1e-9)
                spin_force = 18.0 * state.spin * GEAR_SHIFT
                centrifugal = 12.0 * (state.spin ** 2)
                ax = tx * spin_force + nx * centrifugal
                ay = ty * spin_force + ny * centrifugal
                if r >= belt_r * 0.70:
                    p.phase = 2

            elif p.phase == 2:  # EXHAUST: Outward boundary expulsion
                nx, ny = p.x / (r + 1e-9), p.y / (r + 1e-9)
                ax = 20.0 * nx * SHADOW
                ay = 20.0 * ny * SHADOW
                if r >= belt_r * 0.92:
                    p.phase = 3

            elif p.phase == 3:  # RETURN: Hyperbolic recirculation loop back to throat
                nx, ny = p.x / (r + 1e-9), p.y / (r + 1e-9)
                ax = -22.0 * nx
                ay = -22.0 * ny
                if r <= throat * 1.85:
                    p.phase = 0

            p.dx += ax * dt
            p.dy += ay * dt
            drag = 1.0 - (0.02 * state.pressure)
            p.dx *= drag
            p.dy *= drag
            p.x += p.dx * dt * 20.0
            p.y += p.dy * dt * 20.0
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
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self.is_running = False
        self.shared_runtime_modifiers = {
            "spin": 1.5,
            "pressure": 1.0,
            "temp": 0.0,
            "belt_mod": 1.0
        }

    async def start(self):
        self.is_running = True
        self._disk_task = asyncio.create_task(self._disk_writer_loop())

    def enqueue_frame_sync(self, state: SystemState, delta: float, engine: PhysicsEngine6D):
        if not self.is_running:
            return
        payload = {
            "timestamp": time.time(),
            "spin": state.spin,
            "pressure": state.pressure,
            "temp": state.temp,
            "belt_mod": state.belt_mod,
            "delta": delta,
            "particle_count": len(engine.particles)
        }
        try:
            self.queue.put_nowait(payload)
        except asyncio.QueueFull:
            pass

    async def _disk_writer_loop(self):
        with open(self.log_filepath, "a") as f:
            while self.is_running:
                try:
                    record = await asyncio.wait_for(self.queue.get(), timeout=0.5)
                    f.write(json.dumps(record) + "\n")
                    f.flush()
                except asyncio.TimeoutError:
                    continue
                except asyncio.CancelledError:
                    break

    async def _handle_rpc_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            data = await reader.readline()
            if not data:
                return
            message = data.decode("utf-8").strip()
            try:
                payload = json.loads(message)
                method = payload.get("method", "")
                params = payload.get("params", {})
                req_id = payload.get("id", None)

                if method == "update_vectors":
                    for key in self.shared_runtime_modifiers.keys():
                        if key in params:
                            self.shared_runtime_modifiers[key] = max(0.01, float(params[key]))
                    resp = {"jsonrpc": "2.0", "result": "PARAMETERS_MUTATED_OK", "id": req_id}
                elif method == "get_telemetry":
                    resp = {"jsonrpc": "2.0", "result": self.shared_runtime_modifiers, "id": req_id}
                else:
                    resp = {"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": req_id}
            except Exception as e:
                resp = {"jsonrpc": "2.0", "error": {"code": -32700, "message": f"Parse Failure: {str(e)}"}, "id": None}

            writer.write((json.dumps(resp) + "\n").encode("utf-8"))
            await writer.drain()
        except ConnectionResetError:
            pass
        finally:
            writer.close()
            await writer.wait_closed()

    async def stop(self):
        self.is_running = False
        if hasattr(self, "_disk_task"):
            self._disk_task.cancel()
        if hasattr(self, "_net_task"):
            self._net_task.cancel()
        if hasattr(self, "_stream_server"):
            self._stream_server.close()
        if hasattr(self, "_rpc_server"):
            self._rpc_server.close()


# ── Asynchronous Primary Engine Execution Loop ───────────────────────────────

async def run_79hz_simulation(broker: UnifiedAsyncControlBroker):
    solver = SixCylinderBoundary(base_radius=55.0)
    engine = PhysicsEngine6D(count=250)
    target_period = 1.0 / 79.0
    print("⏱️ 6D Physics Array integrated into event loop. Execution locked to 79 Hz.")
    print("Press Ctrl+C to disconnect from runtime container routines.\n")
    frame = 0
    try:
        while True:
            start_cycle = asyncio.get_event_loop().time()
            m = broker.shared_runtime_modifiers
            state = solver.compute(spin=m["spin"], pressure=m["pressure"], temp=m["temp"], belt_mod=m["belt_mod"])
            delta = solver.closed_loop_delta(state)
            engine.step(state, dt=0.04)
            broker.enqueue_frame_sync(state, delta, engine)

            if frame % 160 == 0:
                print(f"[{frame:05d}] Runtime Spin: {state.spin:.2f} | Temp: {state.temp:.2f} | Drift: {delta:+.6f} | Live Engine Mass: {len(engine.particles)}")
            frame += 1

            elapsed = asyncio.get_event_loop().time() - start_cycle
            remainder = target_period - elapsed
            if remainder > 0:
                await asyncio.sleep(remainder)
            else:
                await asyncio.sleep(0)
    except asyncio.CancelledError:
        pass


async def main():
    broker = UnifiedAsyncControlBroker()
    await broker.start()
    try:
        await run_79hz_simulation(broker)
    except KeyboardInterrupt:
        print("\n⚡ Interrupt hook received. Dismantling event processing pipelines...")
    finally:
        await broker.stop()
        print("🏁 Systems unmounted safely.")


if __name__ == "__main__":
    asyncio.run(main())
