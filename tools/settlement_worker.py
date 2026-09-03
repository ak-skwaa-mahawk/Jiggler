#!/usr/bin/env python3
import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path

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
    from xrpl.wallet import Wallet
    from xrpl.asyncio.transaction import submit_and_wait
    from xrpl.models.transactions import Payment
    XRPL_AVAILABLE = True
except ImportError:
    XRPL_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

JSON_RPC_URL = os.getenv("XRPL_RPC_URL", "https://s.altnet.rippletest.net:51234")
LEDGER_FILE = Path(os.path.expanduser("~/.manifold_xrpl_ledger.jsonl"))

class XRPLAgentSettlementWorker:
    def __init__(self, ws_uri="ws://127.0.0.1:8765"):
        self.ws_uri = ws_uri
        self.client = AsyncJsonRpcClient(JSON_RPC_URL) if XRPL_AVAILABLE else None
        self.sender_wallet = None
        self.target_wallet_address = None
        self.total_dispatched_drops = 0
        self.tx_ledger = []

    def _persist_receipt(self, receipt: dict):
        try:
            with open(LEDGER_FILE, "a") as f:
                f.write(json.dumps(receipt) + "\n")
        except Exception as e:
            logging.error(f"❌ [DISK WRITE FAILED]: Could not write receipt to disk: {e}")

    async def initialize_wallets(self):
        if not XRPL_AVAILABLE:
            logging.warning("⚠️  [XRPL]: xrpl-py not available. Running in simulation mode.")
            return

        sender_seed = os.getenv("XRPL_SENDER_SEED")
        target_addr = os.getenv("XRPL_TARGET_ADDRESS")

        if sender_seed and target_addr:
            try:
                self.sender_wallet = Wallet.from_seed(sender_seed)
                self.target_wallet_address = target_addr
                logging.info(f"🔑 [PERSISTENT WALLET LOADED]: Sender = {self.sender_wallet.classic_address}")
                logging.info(f"🎯 [PERSISTENT TARGET ACTIVE]: Destination = {self.target_wallet_address}")
                return
            except Exception as e:
                logging.error(f"❌ [PERSISTENT WALLET ERROR]: Could not parse seeds: {e}. Falling back to faucet.")

        logging.info("⏳ [XRPL]: Provisioning ephemeral agent wallets from testnet faucet...")
        try:
            self.sender_wallet = await generate_faucet_wallet(self.client, debug=False)
            logging.info(f"✅ [SENDER WALLET ACTIVE]: Address = {self.sender_wallet.classic_address} (Seed: {self.sender_wallet.seed})")

            target_wallet = await generate_faucet_wallet(self.client, debug=False)
            self.target_wallet_address = target_wallet.classic_address
            logging.info(f"🎯 [TARGET AGENT NODE ACTIVE]: Address = {self.target_wallet_address}")
        except Exception as e:
            logging.error(f"❌ [XRPL WALLET INIT FAILED]: {e}")
            self.sender_wallet = None
            self.target_wallet_address = None

    async def execute_xrpl_settlement(self, node_id, amount_sats, effective_strain, lyapunov):
        if amount_sats <= 0:
            return None

        drops_to_send = str(amount_sats)

        if not XRPL_AVAILABLE or not self.sender_wallet or not self.target_wallet_address:
            logging.info(f"⚡ [SIMULATED XRPL TX]: Sent {drops_to_send} drops to node {node_id}")
            sim_receipt = {
                "status": "SIMULATED",
                "recipient_node": node_id,
                "amount_drops": drops_to_send,
                "timestamp": time.time()
            }
            self._persist_receipt(sim_receipt)
            return sim_receipt

        max_attempts = 3
        backoff_sec = 1.5

        for attempt in range(1, max_attempts + 1):
            try:
                payment_tx = Payment(
                    account=self.sender_wallet.classic_address,
                    amount=drops_to_send,
                    destination=self.target_wallet_address
                )

                logging.info(
                    f"🚀 [XRPL SUBMIT]: Broadcasting {drops_to_send} drops ({int(drops_to_send)/1e6:.6f} XRP) "
                    f"from {self.sender_wallet.classic_address[:8]}... to {self.target_wallet_address[:8]}... for Node {node_id} (Attempt {attempt}/{max_attempts})"
                )

                tx_response = await submit_and_wait(payment_tx, self.client, self.sender_wallet)
                tx_hash = tx_response.result.get("hash", "UNKNOWN_HASH")
                tx_result = tx_response.result.get("meta", {}).get("TransactionResult", "UNKNOWN")

                # If successfully committed, break and save receipt
                if tx_result == "tesSUCCESS":
                    receipt = {
                        "tx_hash": tx_hash,
                        "engine_result": tx_result,
                        "recipient_node": node_id,
                        "source_address": self.sender_wallet.classic_address,
                        "destination_address": self.target_wallet_address,
                        "amount_drops": drops_to_send,
                        "effective_strain": effective_strain,
                        "lyapunov": lyapunov,
                        "timestamp": time.time(),
                        "attempts": attempt,
                        "status": "SETTLED"
                    }

                    self.total_dispatched_drops += int(drops_to_send)
                    self.tx_ledger.append(receipt)
                    self._persist_receipt(receipt)

                    logging.info(
                        f"💎 [XRPL FINALIZED]: Hash={tx_hash[:16]}... | Code={tx_result} | "
                        f"Node={node_id} | TotalDispatched={self.total_dispatched_drops} drops"
                    )
                    return receipt

                # Transient engine result handling
                logging.warning(f"⚠️ [XRPL RETRYABLE RESULT]: Engine code {tx_result}. Retrying in {backoff_sec}s...")
                await asyncio.sleep(backoff_sec)
                backoff_sec *= 2

            except Exception as e:
                logging.error(f"❌ [XRPL TX ATTEMPT {attempt} FAILED]: {e}")
                if attempt < max_attempts:
                    await asyncio.sleep(backoff_sec)
                    backoff_sec *= 2
                else:
                    fail_receipt = {
                        "tx_hash": "FAILED",
                        "engine_result": str(e),
                        "recipient_node": node_id,
                        "amount_drops": drops_to_send,
                        "timestamp": time.time(),
                        "status": "FAILED"
                    }
                    self._persist_receipt(fail_receipt)
                    return None

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
