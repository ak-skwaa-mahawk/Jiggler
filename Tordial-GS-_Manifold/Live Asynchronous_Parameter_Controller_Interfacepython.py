import sys
import math
import time
import json
import socket
import select
import asyncio
import threading
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

# ── Global Repository Constants ──────────────────────────────────────────────
TOROIDAL_ROOT = 3.1730059     
GEAR_SHIFT    = 1.02          
SHADOW        = 1.03          


# ── Thread-Safe State Proxy Substrate ────────────────────────────────────────

class ThreadSafeSystemState:
    """
    Maintains atomic control parameters using an internal lock descriptor 
    to facilitate concurrent reading and writing across async thread tasks.
    """
    def __init__(self):
        self._lock = threading.Lock()
        # Calibrated default operational parameters
        self._spin = 1.5
        self._pressure = 1.0
        self._temp = 0.1
        self._belt_mod = 1.0

    def get_all(self) -> Tuple[float, float, float, float]:
        with self._lock:
            return self._spin, self._pressure, self._temp, self._belt_mod

    def update_dict(self, updates: Dict[str, float]) -> Dict[str, str]:
        results = {}
        with self._lock:
            if "spin" in updates:
                self._spin = max(0.01, float(updates["spin"]))
                results["spin"] = f"MUTATED_TO_{self._spin:.3f}"
            if "pressure" in updates:
                self._pressure = max(0.01, float(updates["pressure"]))
                results["pressure"] = f"MUTATED_TO_{self._pressure:.3f}"
            if "temp" in updates:
                self._temp = max(0.0, min(1.0, float(updates["temp"])))
                results["temp"] = f"MUTATED_TO_{self._temp:.3f}"
            if "belt_mod" in updates:
                self._belt_mod = max(0.1, float(updates["belt_mod"]))
                results["belt_mod"] = f"MUTATED_TO_{self._belt_mod:.3f}"
        return results


# ── Physics Boundary Solver Mapping ──────────────────────────────────────────

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

    def compute(self, spin, pressure, temp, belt_mod) -> SystemState:
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


# ── Asynchronous JSON-RPC Parameter Controller Node ──────────────────────────

class AsyncParameterControllerNode:
    """
    Hosts an asynchronous non-blocking network socket handler to parse incoming 
    JSON-RPC string updates, updating live math variables on the fly.
    """
    def __init__(self, state_proxy: ThreadSafeSystemState, host: str = "127.0.0.1", port: int = 8895):
        self.proxy = state_proxy
        self.host = host
        self.port = port
        self._server: Optional[asyncio.AbstractServer] = None
        self.is_running = False

    async def start(self):
        self.is_running = True
        self._server = await asyncio.start_server(self._handle_client_stream, self.host, self.port)
        print(f"🎛️ Async Parameter Controller active on tcp://{self.host}:{self.port}")

    async def _handle_client_stream(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        client_addr = writer.get_extra_info('peername')
        
        try:
            while self.is_running:
                # Extract clean line-delimited request strings over non-blocking streams
                line_bytes = await reader.readline()
                if not line_bytes:
                    break
                    
                response_packet = self._process_rpc_payload(line_bytes.decode('utf-8'))
                writer.write((json.dumps(response_packet) + "\n").encode('utf-8'))
                await writer.drain()
                
        except (ConnectionResetError, socket.error):
            pass
        finally:
            writer.close()
            await writer.wait_closed()

    def _process_rpc_payload(self, raw_str: str) -> Dict[str, Any]:
        try:
            req = json.loads(raw_str)
            method = req.get("method")
            params = req.get("params", {})
            req_id = req.get("id", None)
            
            if method == "mutate_parameters":
                mutation_results = self.proxy.update_dict(params)
                return {
                    "jsonrpc": "2.0", 
                    "result": {"status": "SUCCESS", "changes": mutation_results}, 
                    "id": req_id
                }
                
            elif method == "inspect_state":
                s, p, t, b = self.proxy.get_all()
                return {
                    "jsonrpc": "2.0", 
                    "result": {"spin": s, "pressure": p, "temp": t, "belt_mod": b}, 
                    "id": req_id
                }
                
            else:
                return {"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": req_id}
                
        except Exception as e:
            return {"jsonrpc": "2.0", "error": {"code": -32700, "message": f"Parse Error: {str(e)}"}, "id": None}

    async def stop(self):
        self.is_running = False
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        print("🛑 Parameter control infrastructure server cleanly unmounted.")


# ── Asynchronous Execution Orchestration Loop ───────────────────────────────

async def primary_simulation_loop(state_proxy: ThreadSafeSystemState):
    """
    Main high-precision execution runner driving spatial calculations at 79 Hz.
    Dynamically loads proxy parameter targets to execute geometry sweeps.
    """
    solver = SixCylinderBoundary(base_radius=50.0)
    target_period = 1.0 / 79.0  # Precise ~12.65 ms frame ticks

    print(f"⏱️ 79 Hz primary physical engine tracking loop online.")
    print("Press Ctrl+C to disconnect from the runtime system context safely.\n")

    frame = 0
    try:
        while True:
            cycle_start = asyncio.get_event_loop().time()
            
            # Atomic fetch of current active parameters
            spin, pressure, temp, belt_mod = state_proxy.get_all()
            
            # Execute physical boundary calculations
            state = solver.compute(spin, pressure, temp, belt_mod)
            delta = solver.closed_loop_delta(state)
            
            if frame % 160 == 0:
                print(f"[{frame:05d}] Active Matrix parameters -> Spin: {spin:.3f} | Pres: {pressure:.3f} | Temp: {temp:.3f} | Closed-Loop Drift: {delta:+.6f}")
                
            frame += 1
            
            # High-precision cycle execution sleep clamp
            elapsed = asyncio.get_event_loop().time() - cycle_start
            sleep_remainder = target_period - elapsed
            
            if sleep_remainder > 0:
                await asyncio.sleep(sleep_remainder)
            else:
                await asyncio.sleep(0)
                
    except asyncio.CancelledError:
        pass


async def main():
    # Instantiate atomic system storage state tracking
    shared_proxy = ThreadSafeSystemState()
    
    # Initialize and fire up the non-blocking async network remote control node
    controller_node = AsyncParameterControllerNode(state_proxy=shared_proxy, port=8895)
    await controller_node.start()
    
    try:
        # Run the primary physical iteration processing thread handle
        await primary_simulation_loop(state_proxy=shared_proxy)
    except KeyboardInterrupt:
        print("\n⚡ Interruption signal captured. Dismantling matrix controllers...")
    finally:
        await controller_node.stop()

if __name__ == "__main__":
    asyncio.run(main())
