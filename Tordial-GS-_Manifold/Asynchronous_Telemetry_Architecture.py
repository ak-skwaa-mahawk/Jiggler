import sys
import math
import time
import json
import struct
import socket
import asyncio
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set

# --- Baseline Framework Constants ---
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

    def compute(self, spin=1.5, pressure=1.0, temp=0.0, belt_mod=1.0) -> SystemState:
        spin = max(0.01, spin); pressure = max(0.01, pressure)
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


# ── Asynchronous Telemetry Routing Pipeline ───────────────────────────────────

class AsyncTelemetryPipeline:
    """
    Ingests 79 Hz telemetry frames into an in-memory Pub-Sub architecture.
    Aggregates data into atomic transaction batches to optimize disk I/O and network transmission.
    """
    def __init__(self, log_filepath: str = "async_manifold.log", host: str = "127.0.0.1", port: int = 8890, batch_size: int = 40):
        self.log_filepath = log_filepath
        self.host = host
        self.port = port
        self.batch_size = batch_size

        # Isolated Pub-Sub queues to prevent cross-worker consumption starvation
        self.disk_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self.network_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        
        self.connected_clients: Set[asyncio.StreamWriter] = set()
        self._server: Optional[asyncio.AbstractServer] = None
        self.is_running = False

    def enqueue_frame_sync(self, state: SystemState, delta: float):
        """Thread-safe Pub-Sub ingestion interface to drop frames into independent worker channels."""
        frame = {
            "timestamp": state.timestamp,
            "spin": state.spin,
            "pressure": state.pressure,
            "temp": state.temp,
            "stability": 1.0 - abs(delta),
            "drift": delta
        }
        
        # Publish to Disk Logger Channel
        try:
            self.disk_queue.put_nowait(frame)
        except asyncio.QueueFull:
            pass # Non-blocking shedding protects solver loop stability

        # Publish to Network Broadcast Channel
        try:
            self.network_queue.put_nowait(frame)
        except asyncio.QueueFull:
            pass

    async def start(self):
        """Starts background processing tasks and launches the network socket server."""
        self.is_running = True

        with open(self.log_filepath, "a", encoding="utf-8") as f:
            f.write(f"\n# --- ASYNC PIPELINE LOOP OPENED: {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")

        # Spawn independent consumer tasks
        self._disk_worker_task = asyncio.create_task(self._disk_logging_worker())
        self._network_worker_task = asyncio.create_task(self._network_broadcast_worker())

        self._server = await asyncio.start_server(self._handle_client_connection, self.host, self.port)
        print(f"📡 Async Telemetry Broadcast Socket active on tcp://{self.host}:{self.port}")
        print(f"📝 Async Logging Pipeline writing batches of {self.batch_size} to: {self.log_filepath}")

    async def _handle_client_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Tracks open network listener connections."""
        self.connected_clients.add(writer)
        try:
            while self.is_running:
                await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            pass
        finally:
            self.connected_clients.discard(writer)
            writer.close()
            await writer.wait_closed()

    async def _disk_logging_worker(self):
        """Worker task that pools frames and executes batched thread-safe I/O file dumps."""
        while self.is_running:
            batch = []
            
            # Non-blocking pull of the initial frame
            frame = await self.disk_queue.get()
            batch.append(frame)
            self.disk_queue.task_done()
            
            # Pack queue items up to the batch limit or until empty
            while len(batch) < self.batch_size and not self.disk_queue.empty():
                frame = self.disk_queue.get_nowait()
                batch.append(frame)
                self.disk_queue.task_done()
                
            # Process string construction and offload the actual file I/O to a background thread
            if batch:
                serialized_block = "".join([json.dumps(f) + "\n" for f in batch])
                await asyncio.to_thread(self._write_to_disk, serialized_block)
                
            # Yield core loop execution focus back to the scheduler
            await asyncio.sleep(0.01)

    def _write_to_disk(self, data_str: str):
        with open(self.log_filepath, "a", encoding="utf-8") as f:
            f.write(data_str)

    async def _network_broadcast_worker(self):
        """Worker task that batches frames and writes length-prefixed bytes over active streams."""
        while self.is_running:
            batch = []
            
            frame = await self.network_queue.get()
            batch.append(frame)
            self.network_queue.task_done()
            
            while len(batch) < self.batch_size and not self.network_queue.empty():
                frame = self.network_queue.get_nowait()
                batch.append(frame)
                self.network_queue.task_done()
                
            if batch and self.connected_clients:
                # Compound batch serialize execution step
                full_payload = b""
                for item in batch:
                    serialized_bytes = (json.dumps(item) + "\n").encode('utf-8')
                    header = struct.pack('!I', len(serialized_bytes))
                    full_payload += (header + serialized_bytes)
                
                # Concurrent write loop targeting active stream connection points
                disconnected = set()
                for writer in list(self.connected_clients):
                    try:
                        writer.write(full_payload)
                        await writer.drain()
                    except (socket.error, ConnectionResetError, BrokenPipeError):
                        disconnected.add(writer)
                        
                for writer in disconnected:
                    self.connected_clients.discard(writer)
                    
            await asyncio.sleep(0.01)

    async def stop(self):
        """Cleans up and terminates open sockets and running asynchronous workers."""
        self.is_running = False
        if self._server:
            self._server.close()
            await self._server.wait_closed()

        self._disk_worker_task.cancel()
        self._network_worker_task.cancel()
        await asyncio.gather(self._disk_worker_task, self._network_worker_task, return_exceptions=True)


# ── Asynchronous Execution Orchestrator Loop ────────────────────────────────

async def primary_simulation_loop(pipeline: AsyncTelemetryPipeline):
    """
    Main high-precision execution runner driving spatial calculations at 79 Hz.
    """
    solver = SixCylinderBoundary(base_radius=50.0)
    target_hz_period = 1.0 / 79.0  # Precise ~12.65 ms timing increment step

    print(f"⏱️ Matrix loop active. Enforcing strict 79 Hz simulation update intervals.")
    print("Press Ctrl+C to drop system execution loops safely.\n")

    frame_count = 0
    try:
        while True:
            cycle_start_time = asyncio.get_event_loop().time()

            # Simulate real-world geometric operational drift parameters
            noise = 0.1 * math.sin(frame_count * 0.05)
            state = solver.compute(spin=1.5 + noise, temp=0.1)
            delta = solver.closed_loop_delta(state)

            # Non-blocking handover to the async log pipeline
            pipeline.enqueue_frame_sync(state, delta)

            if frame_count % 160 == 0:
                print(f" Frame: {frame_count:05d} | Current Spin Axis: {state.spin:.4f} | Manifold Drift: {delta:+.6f}")
                
            frame_count += 1
            
            # Calculate precision timing margins
            execution_cost = asyncio.get_event_loop().time() - cycle_start_time
            sleep_duration = target_hz_period - execution_cost
            
            if sleep_duration > 0:
                await asyncio.sleep(sleep_duration)
            else:
                # Execution overrun warning metric hook
                await asyncio.sleep(0)
                
    except asyncio.CancelledError:
        pass


async def main():
# Instantiate pipeline with a target compaction parameter size of 40 elementstelemetry_pipeline = AsyncTelemetryPipeline(log_filepath="async_telemetry.log", batch_size=40)await telemetry_pipeline.start()try:await primary_simulation_loop(telemetry_pipeline)except KeyboardInterrupt:print("\n⚡ Interruption command parsed. Cleaning loop variables...")finally:await telemetry_pipeline.stop()print("🏁 Async server instances dropped cleanly.")if name == "main":asyncio.run(main())