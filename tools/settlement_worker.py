#!/usr/bin/env python3
import asyncio
import json
import logging
import os
import sys
import time
import hashlib
import hmac

try:
    import websockets
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
    import websockets

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class AgentSettlementWorker:
    def __init__(self, ws_uri="ws://127.0.0.1:8765", settlement_rail="XRPL_MICROPAYMENT"):
        self.ws_uri = ws_uri
        self.rail = settlement_rail
        self.secret_key = os.urandom(32)
        self.total_dispatched_sats = 0
        self.tx_ledger = []

    def sign_settlement_receipt(self, node_id, amount_sats, timestamp):
        message = f"{node_id}:{amount_sats}:{timestamp}:{self.rail}".encode('utf-8')
        signature = hmac.new(self.secret_key, message, hashlib.sha256).hexdigest()
        return signature

    def execute_micro_settlement(self, node_id, amount_sats, effective_strain, lyapunov):
        if amount_sats <= 0:
            return None

        timestamp = time.time()
        tx_hash = hashlib.sha256(f"{node_id}:{amount_sats}:{timestamp}".encode('utf-8')).hexdigest()[:16]
        sig = self.sign_settlement_receipt(node_id, amount_sats, timestamp)

        receipt = {
            "tx_id": f"tx_{tx_hash}",
            "rail": self.rail,
            "recipient_node": node_id,
            "amount_sats": amount_sats,
            "effective_strain": effective_strain,
            "lyapunov": lyapunov,
            "signature": sig,
            "timestamp": timestamp,
            "status": "SETTLED"
        }

        self.total_dispatched_sats += amount_sats
        self.tx_ledger.append(receipt)

        logging.info(
            f"⚡ [AGENT SETTLED]: Rail={self.rail} | Node={node_id} | "
            f"Amount={amount_sats} sats | TxID={receipt['tx_id']} | TotalDispatched={self.total_dispatched_sats} sats"
        )
        return receipt

    async def run(self):
        logging.info(f"🛰️  [SETTLEMENT WORKER]: Connecting to Manifold mesh at {self.ws_uri}...")
        while True:
            try:
                async with websockets.connect(self.ws_uri) as ws:
                    logging.info(f"✅ [SETTLEMENT WORKER]: Subscribed to mesh stream on rail: {self.rail}")
                    while True:
                        msg = await ws.recv()
                        data = json.loads(msg)

                        # Handle direct telemetry burst evaluations
                        if data.get("status") == "SUCCESS" and data.get("action") == "DISPATCH_BURST":
                            node_id = data.get("node_id", "ANON_NODE")
                            sats = data.get("allocated_budget_sats", 0)
                            eff_strain = data.get("effective_strain", 0.0)
                            lyap = data.get("lyapunov_exp", 0.0)
                            self.execute_micro_settlement(node_id, sats, eff_strain, lyap)

            except (ConnectionRefusedError, OSError):
                logging.warning("⚠️  Local WebSocket mesh unavailable. Reconnecting in 3s...")
                await asyncio.sleep(3)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Settlement loop error: {e}")
                await asyncio.sleep(2)

if __name__ == "__main__":
    worker = AgentSettlementWorker()
    try:
        asyncio.run(worker.run())
    except KeyboardInterrupt:
        logging.info("Stopping Agent Settlement Worker.")
