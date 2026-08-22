#!/usr/bin/env python3
import socket
import json
import logging
import struct
import numpy as np
import sys
import os

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
        
        # Smooth depth perspective projection
        z_depth = max(abs(p3d[2]) + 1.0, 1e-4)
        x_ndc = (p3d[0] * fov) / z_depth
        y_ndc = (p3d[1] * fov) / z_depth
        
        # Soft saturation via tanh
        action_ndc = np.tanh(np.array([x_ndc, y_ndc])) * damping
        return p3d, action_ndc

def start_telemetry_listener(host="0.0.0.0", port=9999):
    engine = BurstEngine(strain_threshold=75.0, burst_budget_sats=500) if BurstEngine else None
    manifold = ToroidalGSManifold()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))

    logging.info(f"👂 Listening for Manifold Telemetry (JSON & Binary 4D) on UDP port {port}...")

    t = 0.0
    while True:
        try:
            data, addr = sock.recvfrom(4096)
            
            if len(data) == 12:
                px, py, lyap = struct.unpack('!3f', data)
                t += 0.01
                
                raw_4d = manifold.embed_torus_to_4d(px, py, time_w=t)
                if not manifold.is_calibrated:
                    manifold.dynamic_null(raw_4d)
                    logging.info(f"🎯 [NULL CALIBRATION]: Baseline anchored at {raw_4d[:3]}")

                damping = manifold.compute_lyapunov_damping(lyap)
                p3d, ndc = manifold.slice_and_project(raw_4d, damping=damping)
                logging.info(f"🌀 [4D SLICE]: Phase=({px:.3f}, {py:.3f}) | Lyap={lyap:.3f} | NDC Action={ndc}")
                continue

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

                result = engine.evaluate_node_telemetry(
                    node_id=node_id,
                    strain_percent=strain,
                    vitality_score=vitality
                )

                if result and result.get("status") == "SUCCESS":
                    sock.sendto(json.dumps(result).encode('utf-8'), addr)

        except KeyboardInterrupt:
            logging.info("Stopping telemetry listener.")
            break
        except Exception as e:
            logging.error(f"Error processing packet: {e}")

if __name__ == "__main__":
    start_telemetry_listener()
