#!/usr/bin/env python3
import socket
import json
import logging
import sys
import os

sys.path.insert(0, os.path.expanduser("~"))
from burst_engine import BurstEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def start_telemetry_listener(host="0.0.0.0", port=9999):
    engine = BurstEngine(strain_threshold=75.0, burst_budget_sats=500)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))

    logging.info(f"👂 Listening for Manifold Telemetry on UDP port {port}...")

    while True:
        try:
            data, addr = sock.recvfrom(4096)
            raw_text = data.decode('utf-8', errors='replace').strip()
            
            if not raw_text:
                continue

            try:
                telemetry = json.loads(raw_text)
            except json.JSONDecodeError:
                # Silently ignore non-JSON pings/raw packets instead of throwing errors
                continue

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
