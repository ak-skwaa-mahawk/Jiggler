# intent_client.py
# Sovereign Intent + SixCylinderBoundary Client
# Features: Auto-reconnect, caching, logging, async support, streaming-ready

import time
import logging
import grpc
from google.protobuf import empty_pb2

import issttoft_pb2
import issttoft_pb2_grpc

# ====================== LOGGING SETUP ======================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("IntentClient")


class IntentClientError(Exception):
    """Base exception for IntentClient."""
    pass


class IntentClientConnectionError(IntentClientError):
    """Raised when connection to the gRPC server fails after retries."""
    pass


class IntentClient:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 50051,
        cache_ttl_seconds: float = 8.0,
        max_retries: int = 3,
        retry_backoff: float = 0.4,
    ):
        self.host = host
        self.port = port
        self.cache_ttl = cache_ttl_seconds
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff

        self._channel = None
        self._stub = None
        self._cache = {}
        self._connect()

    # ====================== CONNECTION MANAGEMENT ======================

    def _connect(self):
        if self._channel:
            try:
                self._channel.close()
            except Exception:
                pass

        self._channel = grpc.insecure_channel(
            f"{self.host}:{self.port}",
            options=[
                ("grpc.keepalive_time_ms", 10000),
                ("grpc.keepalive_timeout_ms", 5000),
            ],
        )
        self._stub = issttoft_pb2_grpc.InferenceServiceStub(self._channel)
        logger.info(f"Connected to gRPC server at {self.host}:{self.port}")

    def _ensure_connected(self):
        try:
            grpc.channel_ready_future(self._channel).result(timeout=2)
        except grpc.FutureTimeoutError:
            logger.warning("Connection lost. Reconnecting...")
            self._connect()

    def _classify_error(self, e: grpc.RpcError) -> str:
        if e.code() in (grpc.StatusCode.UNAVAILABLE, grpc.StatusCode.DEADLINE_EXCEEDED):
            return "transient"
        return "permanent"

    # ====================== INTENT METHODS ======================

    def get_all_intent_bands(self, use_cache: bool = True):
        cache_key = "all_bands"

        if use_cache and cache_key in self._cache:
            ts, data = self._cache[cache_key]
            if time.time() - ts < self.cache_ttl:
                return data

        for attempt in range(self.max_retries):
            try:
                self._ensure_connected()
                response = self._stub.GetAllIntentBands(empty_pb2.Empty())
                bands = list(response.bands)
                self._cache[cache_key] = (time.time(), bands)
                return bands

            except grpc.RpcError as e:
                error_type = self._classify_error(e)
                logger.warning(f"get_all_intent_bands failed ({error_type}): {e.code()}")
                if error_type == "permanent" or attempt == self.max_retries - 1:
                    raise IntentClientConnectionError(str(e))
                time.sleep(self.retry_backoff * (attempt + 1))
                self._connect()

    def get_intent_band(self, band_id: str, mode: int = 0):
        for attempt in range(self.max_retries):
            try:
                self._ensure_connected()
                req = issttoft_pb2.GetIntentBandRequest(band_id=band_id, mode=mode)
                return self._stub.GetIntentBand(req)
            except grpc.RpcError as e:
                if e.code() == grpc.StatusCode.NOT_FOUND:
                    return None
                if attempt == self.max_retries - 1:
                    raise
                self._connect()
                time.sleep(self.retry_backoff)

    # ====================== SIXCYLINDERBOUNDARY METHODS ======================

    def compute_six_face_boundary(self, spin=1.5, pressure=1.0, temp=0.15, belt_mod=1.0):
        for attempt in range(self.max_retries):
            try:
                self._ensure_connected()
                req = issttoft_pb2.SixFaceRequest(
                    spin=spin, pressure=pressure, temp=temp, belt_mod=belt_mod
                )
                return self._stub.ComputeSixFaceBoundary(req)
            except grpc.RpcError:
                if attempt == self.max_retries - 1:
                    raise
                self._connect()
                time.sleep(self.retry_backoff)

    def get_closed_loop_delta(self, spin=1.5, pressure=1.0, temp=0.15, belt_mod=1.0):
        for attempt in range(self.max_retries):
            try:
                self._ensure_connected()
                req = issttoft_pb2.SixFaceRequest(
                    spin=spin, pressure=pressure, temp=temp, belt_mod=belt_mod
                )
                return self._stub.GetClosedLoopDelta(req).delta
            except grpc.RpcError:
                if attempt == self.max_retries - 1:
                    raise
                self._connect()
                time.sleep(self.retry_backoff)

    def run_tracking_form_proof(self, spin=1.5, pressure=1.0, temp=0.15, belt_mod=1.0):
        for attempt in range(self.max_retries):
            try:
                self._ensure_connected()
                req = issttoft_pb2.SixFaceRequest(
                    spin=spin, pressure=pressure, temp=temp, belt_mod=belt_mod
                )
                return self._stub.RunTrackingFormProof(req)
            except grpc.RpcError:
                if attempt == self.max_retries - 1:
                    raise
                self._connect()
                time.sleep(self.retry_backoff)

    def close(self):
        if self._channel:
            self._channel.close()

    # ====================== STREAMING SUPPORT (Future) ======================

    def stream_intent_updates(self):
        """
        Placeholder for future streaming RPC.
        Example usage once we add a streaming method in the .proto:

        for update in self.stream_intent_updates():
            print(update)
        """
        raise NotImplementedError(
            "Streaming not yet implemented. "
            "Add a streaming RPC in the .proto first (e.g. StreamIntentUpdates)."
        )


# ====================== ASYNC VERSION ======================

import asyncio
import grpc.aio as grpc_aio


class AsyncIntentClient:
    def __init__(self, host="localhost", port=50051):
        self.address = f"{host}:{port}"
        self._channel = None
        self._stub = None

    async def connect(self):
        self._channel = grpc_aio.insecure_channel(self.address)
        self._stub = issttoft_pb2_grpc.InferenceServiceStub(self._channel)
        logger.info(f"[Async] Connected to {self.address}")

    async def get_all_intent_bands(self):
        response = await self._stub.GetAllIntentBands(empty_pb2.Empty())
        return list(response.bands)

    async def compute_six_face_boundary(self, spin=1.5, pressure=1.0, temp=0.15, belt_mod=1.0):
        req = issttoft_pb2.SixFaceRequest(
            spin=spin, pressure=pressure, temp=temp, belt_mod=belt_mod
        )
        return await self._stub.ComputeSixFaceBoundary(req)

    async def close(self):
        if self._channel:
            await self._channel.close()


# ====================== EXAMPLE USAGE ======================

if __name__ == "__main__":
    client = IntentClient(host="127.0.0.1")

    try:
        bands = client.get_all_intent_bands()
        print(f"Found {len(bands)} intent bands")

        result = client.compute_six_face_boundary(spin=1.82, pressure=1.15)
        print(f"Stability: {result.closed_loop_stability:.4f}")

    finally:
        client.close()