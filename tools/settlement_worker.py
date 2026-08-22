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
    import xrpl
    from xrpl.asyncio.clients import AsyncJsonRpcClient
    from xrpl.asyncio.wallet import generate_faucet_wallet
    from xrpl.asyncio.transaction import submit_and_wait
    from xrpl.wallet import Wallet
    from xrpl.models.transactions import Payment
    XRPL_AVAILABLE = True
except ImportError:
    XRPL_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

JSON_RPC_URL = "https://s.altnet.rippletest.net:51234"

class XRPLAgentSettlementWorker:
    def __init__(self, ws_uri="ws://127.0.0.1:8765"):
        self.ws_uri = ws_uri
        self.client = AsyncJsonRpcClient(JSON_RPC_URL) if XRPL_AVAILABLE else None
        self.sender_wallet = None
        self.target_agent_address = None
        self.total_dispatched_drops = 0
        self.tx_ledger = []

    async def initialize_wallets(self):
        if not XRPL_AVAILABLE:
            logging.warning("⚠️  [XRPL]: xrpl-py not available. Running in simulation mode.")
            return

        logging.info("⏳ [XRPL]: Provisioning sender wallet from testnet faucet...")
        try:
            self.sender_wallet = await generate_faucet_wallet(self.client, debug=False)
            logging.info(f"✅ [SENDER WALLET ACTIVE]: Address = {self.sender_wallet.classic_address}")
            
            # Destination wallet for recipient agent node
            receiver_wallet = Wallet.create()
            self.target_agent_address = receiver_wallet.classic_address
            logging.info(f"🎯 [TARGET AGENT NODE]: Address = {self.target_agent_address}")
        except Exception as e:
            logging.error(f"❌ [XRPL WALLET INIT FAILED]: {e}")
            self.sender_wallet = None

    async def execute_xrpl_settlement(self, node_id, amount_sats, effective_strain, lyapunov):
        if amount_sats <= 0:
            return None

        drops_to_send = str(amount_sats)

        if not XRPL_AVAILABLE or not self.sender_wallet or not self.target_agent_address:
            logging.info(f"⚡ [SIMULATED XRPL TX]: Sent {drops_to_send} drops to node {node_id}")
            return {"status": "SIMULATED", "drops": drops_to_send}

        try:
            payment_tx = Payment(
                account=self.sender_wallet.classic_address,
                amount=drops_to_send,
                destination=self.target_agent_address
            )

            logging.info(
                f"🚀 [XRPL SUBMIT]: Broadcasting {drops_to_send} drops ({int(drops_to_send)/1e6:.6f} XRP) "
                f"from {self.sender_wallet.classic_address[:8]}... to {self.target_agent_address[:8]}... for Node {node_id}"
            )
            
            tx_response = await submit_and_wait(payment_tx, self.client, self.sender_wallet)
            
            tx_hash = tx_response.result.get("hash", "UNKNOWN_HASH")
            tx_result = tx_response.result.get("meta", {}).get("TransactionResult", "UNKNOWN")

            receipt = {
                "tx_hash": tx_hash,
                "engine_result": tx_result,
                "recipient_node": node_id,
                "destination_address": self.target_agent_address,
                "amount_drops": drops_to_send,
                "effective_strain": effective_strain,
                "lyapunov": lyapunov,
                "timestamp": time.time(),
                "status": "SETTLED" if tx_result == "tesSUCCESS" else "FAILED"
            }

            self.total_dispatched_drops += int(drops_to_send)
            self.tx_ledger.append(receipt)

            logging.info(
                f"💎 [XRPL FINALIZED]: Hash={tx_hash[:16]}... | Code={tx_result} | "
                f"Node={node_id} | TotalDispatched={self.total_dispatched_drops} drops"
            )
            return receipt

        except Exception as e:
            logging.error(f"❌ [XRPL TX ERROR]: {e}")
            return None

    async def run(self):
        await self.initialize_wallets()

        logging.info(f"🛰️  [SETTLEMENT WORKER]: Connecting to Manifold mesh at {self.ws_uri}...")
        while True:
            try:
                async with websockets.connect(self.ws_uri) as ws:
                    logging.info("✅ [SETTLEMENT WORKER]: Subscribed to mesh burst events.")
                    while True:
                        msg = await ws.recv()
                        data = json.loads(msg)

                        if data.get("status") == "SUCCESS" and data.get("action") == "DISPATCH_BURST":
                            node_id = data.get("node_id", "ANON_NODE")
                            sats = data.get("allocated_budget_sats", 0)
                            eff_strain = data.get("effective_strain", 0.0)
                            lyap = data.get("lyapunov_exp", 0.0)
                            
                            await self.execute_xrpl_settlement(node_id, sats, eff_strain, lyap)

            except (ConnectionRefusedError, OSError):
                logging.warning("⚠️  Local WebSocket mesh unavailable. Retrying in 3s...")
                await asyncio.sleep(3)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Settlement loop error: {e}")
                await asyncio.sleep(2)

if __name__ == "__main__":
    worker = XRPLAgentSettlementWorker()
    try:
        asyncio.run(worker.run())
    except KeyboardInterrupt:
        logging.info("Stopping XRPL Agent Settlement Worker.")
