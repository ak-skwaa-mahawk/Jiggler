#!/usr/bin/env python3
import asyncio
import json
import logging
import os
import sys
import time

try:
    import websockets
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
    import websockets

try:
    from google.cloud import pubsub_v1
    GCP_PUBSUB_AVAILABLE = True
except ImportError:
    GCP_PUBSUB_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class GCPManifoldBridge:
    def __init__(self, ws_uri="ws://127.0.0.1:8765", topic_name="manifold-telemetry-topic"):
        self.ws_uri = ws_uri
        self.project_id = os.popen("gcloud config get-value project 2>/dev/null").read().strip()
        self.topic_name = topic_name
        self.publisher = None
        self.topic_path = None

        if GCP_PUBSUB_AVAILABLE and self.project_id:
            try:
                self.publisher = pubsub_v1.PublisherClient()
                self.topic_path = self.publisher.topic_path(self.project_id, self.topic_name)
                logging.info(f"☁️  [GCP BRIDGE]: Pub/Sub enabled for topic {self.topic_path}")
            except Exception as e:
                logging.warning(f"⚠️  [GCP BRIDGE]: Pub/Sub initialization error: {e}")
        else:
            logging.info(f"ℹ️  [GCP BRIDGE]: Running in local simulation mode (Pub/Sub SDK or active project not configured).")

    def publish_to_cloud(self, payload_dict):
        data_str = json.dumps(payload_dict)
        if self.publisher and self.topic_path:
            try:
                data_bytes = data_str.encode("utf-8")
                self.publisher.publish(self.topic_path, data=data_bytes)
            except Exception as e:
                logging.error(f"GCP Publish failed: {e}")
        else:
            # Emulated logging for development/offline mode
            logging.debug(f"[EMULATED GCP INGRESS]: {data_str}")

    async def stream_loop(self):
        logging.info(f"🛰️  Connecting bridge to local manifold WebSocket at {self.ws_uri}...")
        while True:
            try:
                async with websockets.connect(self.ws_uri) as ws:
                    logging.info("✅ [GCP BRIDGE]: Connected to local manifold stream.")
                    while True:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        
                        # Enrich frame with cloud metadata
                        data["gcp_origin_project"] = self.project_id or "local-termux"
                        data["ingest_epoch"] = time.time()
                        
                        self.publish_to_cloud(data)
            except (ConnectionRefusedError, OSError):
                logging.warning("⚠️  Local WebSocket mesh unavailable. Retrying in 3 seconds...")
                await asyncio.sleep(3)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Bridge loop error: {e}")
                await asyncio.sleep(2)

if __name__ == "__main__":
    bridge = GCPManifoldBridge()
    try:
        asyncio.run(bridge.stream_loop())
    except KeyboardInterrupt:
        logging.info("Stopping GCP Manifold Bridge.")
