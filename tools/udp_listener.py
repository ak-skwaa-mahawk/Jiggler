#!/usr/bin/env python3
import socket
import json
import logging
import struct
import numpy as np
import sys
import os
import time
import asyncio
import threading

try:
    import websockets
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
    import websockets

sys.path.insert(0, os.path.expanduser("~"))
try:
    from burst_engine import BurstEngine
except ImportError:
    BurstEngine = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class ToroidalGSManifold:
    def __init__(self, major_radius=2.0, minor_radius=0.75):
        self.R = major_radius
        self.r = minor_radius
        self.baseline_impedance = np.zeros(4)
        self.is_calibrated = False

    def embed_torus_to_4d(self, u_phase, v_phase, time_w=0.0):
        x1 = (self.R + self.r * np.cos(v_phase)) * np.cos(u_phase)
        x2 = (self.R + self.r * np.cos(v_phase)) * np.sin(u_phase)
        x3 = self.r * np.sin(v_phase)
        x4 = time_w
        return np.array([x1, x2, x3, x4], dtype=np.float32)

    def dynamic_null(self, reference_state_4d):
        self.baseline_impedance = reference_state_4d
        self.is_calibrated = True

    def compute_lyapunov_damping(self, lyapunov_exp, delta_t=0.01):
        if lyapunov_exp < 0:
            return float(np.exp(lyapunov_exp * delta_t))
        return float(1.0 + (lyapunov_exp * delta_t))

    def slice_and_project(self, state_4d, damping=1.0, fov=1.5):
        calibrated = state_4d - self.baseline_impedance
        p3d = calibrated[:3]
        z_depth = max(abs(p3d[2]) + 1.0, 1e-4)
        x_ndc = (p3d[0] * fov) / z_depth
        y_ndc = (p3d[1] * fov) / z_depth
        action_ndc = np.tanh(np.array([x_ndc, y_ndc])) * damping
        return p3d, action_ndc

class MeshBroadcaster:
    def __init__(self, host="0.0.0.0", port=8765):
        self.host = host
        self.port = port
        self.clients = set()
        self.loop = None

    async def register(self, websocket):
        self.clients.add(websocket)
        logging.info(f"🌐 [WS MESH]: Client connected from {websocket.remote_address}. Active peers: {len(self.clients)}")
        try:
            await websocket.wait_closed()
        finally:
            self.clients.remove(websocket)
            logging.info(f"🌐 [WS MESH]: Client disconnected. Active peers: {len(self.clients)}")

    async def _broadcast(self, message_str):
        if self.clients:
            coros = [client.send(message_str) for client in self.clients]
            await asyncio.gather(*coros, return_exceptions=True)

    def broadcast(self, payload_dict):
        if self.loop and self.clients:
            message_str = json.dumps(payload_dict)
            asyncio.run_coroutine_threadsafe(self._broadcast(message_str), self.loop)

    def run_server(self):
        async def main():
            self.loop = asyncio.get_running_loop()
            async with websockets.serve(self.register, self.host, self.port):
                logging.info(f"🚀 [WS MESH BROADCASTER]: Active and broadcasting on ws://{self.host}:{self.port}")
                await asyncio.Future()

        asyncio.run(main())

def start_telemetry_listener(host="0.0.0.0", udp_port=9999, ws_port=8765):
    engine = BurstEngine(strain_threshold=75.0, burst_budget_sats=500) if BurstEngine else None
    manifold = ToroidalGSManifold()
    broadcaster = MeshBroadcaster(host=host, port=ws_port)

    ws_thread = threading.Thread(target=broadcaster.run_server, daemon=True)
    ws_thread.start()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, udp_port))

    logging.info(f"👂 Listening for Manifold Telemetry on UDP port {udp_port}...")

    t = 0.0
    while True:
        try:
            data, addr = sock.recvfrom(4096)
            
            # --- Stream Handler 1: Binary Coordinates ---
            if len(data) == 12:
                px, py, lyap = struct.unpack('!3f', data)
                t += 0.01
                
                # Forward Lyapunov updates to BurstEngine state
                if engine:
                    engine.update_lyapunov_state(lyap)

                raw_4d = manifold.embed_torus_to_4d(px, py, time_w=t)
                if not manifold.is_calibrated:
                    manifold.dynamic_null(raw_4d)
                    logging.info(f"🎯 [NULL CALIBRATION]: Baseline anchored at {raw_4d[:3]}")

                damping = manifold.compute_lyapunov_damping(lyap)
                p3d, ndc = manifold.slice_and_project(raw_4d, damping=damping)

                mesh_payload = {
                    "type": "MANIFOLD_NDC_STREAM",
                    "timestamp": time.time(),
                    "vector": [round(float(ndc[0]), 6), round(float(ndc[1]), 6)],
                    "p3d": [round(float(coord), 6) for coord in p3d],
                    "stability": {
                        "phase_x": round(float(px), 6),
                        "phase_y": round(float(py), 6),
                        "lyapunov": round(float(lyap), 6),
                        "calibrated": manifold.is_calibrated
                    }
                }
                broadcaster.broadcast(mesh_payload)
                logging.info(f"🌀 [4D SLICE -> WS MESH]: Phase=({px:.3f}, {py:.3f}) | Lyap={lyap:.3f} | NDC Action={ndc}")
                continue

            # --- Stream Handler 2: JSON Burst Engine Telemetry ---
            raw_text = data.decode('utf-8', errors='replace').strip()
            if not raw_text:
                continue

            try:
                telemetry = json.loads(raw_text)
            except json.JSONDecodeError:
                continue

            if engine:
                node_id = telemetry.get("node_id", "UNKNOWN")
                strain = float(telemetry.get("strain_percent", 0.0))
                vitality = float(telemetry.get("vitality_score", 1.0))
                custom_lyap = telemetry.get("lyapunov_exp", None)

                result = engine.evaluate_node_telemetry(
                    node_id=node_id,
                    strain_percent=strain,
                    vitality_score=vitality,
                    lyapunov_exp=custom_lyap
                )

                if result:
                    sock.sendto(json.dumps(result).encode('utf-8'), addr)

        except KeyboardInterrupt:
            logging.info("Stopping telemetry listener.")
            break
        except Exception as e:
            logging.error(f"Error processing packet: {e}")

if __name__ == "__main__":
    start_telemetry_listener()
