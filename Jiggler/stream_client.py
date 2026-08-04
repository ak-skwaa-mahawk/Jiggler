import argparse
import asyncio
import datetime
import os
import signal
import sys
import time
import numpy as np
import grpc
import jiggler_native
import Atmospheric_Vector_pb2 as pb2

try:
    import Atmospheric_Vector_pb2_grpc as pb2_grpc
except ImportError:
    pb2_grpc = None

def parse_args():
    parser = argparse.ArgumentParser(
        description="Jiggler Substrate gRPC Streamer (Graceful Signal Shutdown)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--fps", type=float, default=60.0, help="Target max streaming FPS")
    parser.add_argument("--batch-size", type=int, default=1_000_000, help="Number of f32 elements per batch")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="gRPC server host")
    parser.add_argument("--port", type=int, default=50051, help="gRPC server port")
    parser.add_argument("--threshold", type=float, default=0.048, help="Out-of-bounds drift threshold")
    parser.add_argument("--report-interval", type=float, default=1.0, help="Telemetry reporting interval in seconds")
    parser.add_argument("--min-fps", type=float, default=5.0, help="Minimum adaptive FPS floor")
    parser.add_argument("--log-file", type=str, default="telemetry.log", help="Path to write telemetry logs")
    return parser.parse_args()

def write_log(log_fp, message):
    """Writes a timestamped line to stdout and appends to the log file."""
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    formatted_msg = f"[{timestamp}] {message}"
    print(formatted_msg, flush=True)
    if log_fp and not log_fp.closed:
        log_fp.write(formatted_msg + "\n")
        log_fp.flush()

class SubstrateBufferPool:
    """Pre-allocates memory buffers and reusable Protobuf message structures."""
    def __init__(self, batch_size, threshold):
        self.batch_size = batch_size
        self.threshold = np.float32(threshold)
        self.input_buffer = np.random.uniform(-0.1, 0.1, batch_size).astype(np.float32)
        self.output_buffer = np.empty(batch_size, dtype=np.float32)
        self.msg = pb2.AtmosphericVector()
        self.fields = [f.name for f in self.msg.DESCRIPTOR.fields]

    def process_and_pack(self):
        t0 = time.perf_counter()
        oob_count = jiggler_native.process_drift_batch_zero_copy(
            self.input_buffer, self.output_buffer, self.threshold
        )
        simd_ms = (time.perf_counter() - t0) * 1000.0

        values_slice = self.output_buffer[:len(self.fields)]
        for idx, field_name in enumerate(self.fields):
            val = float(values_slice[idx]) if idx < len(values_slice) else 0.0
            setattr(self.msg, field_name, val)

        return self.msg, oob_count, simd_ms

async def main():
    args = parse_args()
    server_address = f"{args.host}:{args.port}"
    log_fp = open(args.log_file, "a", encoding="utf-8")

    running = True

    def handle_signal(sig):
        nonlocal running
        if running:
            running = False
            sig_name = signal.Signals(sig).name
            write_log(log_fp, f"🛑 Received {sig_name}. Initiating instant graceful shutdown...")

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, handle_signal, sig)
        except NotImplementedError:
            # Fallback for OS environments without loop signal handling
            signal.signal(sig, lambda sig_num, frame: handle_signal(sig_num))

    write_log(log_fp, f"🚀 Initializing Async gRPC Streamer (Signal Handler Active)")
    write_log(log_fp, f"   Target: {server_address} | Max FPS: {args.fps} | Log File: {args.log_file}")

    buffer_pool = SubstrateBufferPool(args.batch_size, args.threshold)

    async with grpc.aio.insecure_channel(server_address) as channel:
        try:
            await asyncio.wait_for(channel.channel_ready(), timeout=2.0)
            write_log(log_fp, f"✅ Connected to gRPC Server at {server_address}")
        except Exception as e:
            write_log(log_fp, f"❌ Connection to {server_address} failed: {e}")
            log_fp.close()
            return

        batch_counter = 0
        window_batches = 0
        window_bytes = 0
        window_simd_ms = 0.0
        last_report_time = time.perf_counter()
        current_target_fps = args.fps
        throttled = False

        while running:
            loop_start = time.perf_counter()
            batch_counter += 1

            msg, oob_count, simd_ms = buffer_pool.process_and_pack()
            payload_len = len(msg.SerializeToString())

            window_batches += 1
            window_bytes += payload_len
            window_simd_ms += simd_ms

            elapsed_processing = time.perf_counter() - loop_start
            frame_budget_sec = 1.0 / current_target_fps

            if elapsed_processing > frame_budget_sec:
                max_sustainable_fps = 1.0 / (elapsed_processing * 1.15)
                new_fps = max(args.min_fps, max_sustainable_fps)
                if not throttled or abs(new_fps - current_target_fps) > 1.0:
                    write_log(log_fp, f"⚠️ EVENT: Throttle Engaged | ({elapsed_processing * 1000.0:.2f}ms > {frame_budget_sec * 1000.0:.2f}ms). Target FPS: {current_target_fps:.1f} -> {new_fps:.1f}")
                current_target_fps = new_fps
                throttled = True
            elif throttled and elapsed_processing < (frame_budget_sec * 0.75):
                new_fps = min(args.fps, current_target_fps * 1.1)
                if new_fps >= args.fps * 0.98:
                    new_fps = args.fps
                    throttled = False
                    write_log(log_fp, f"🟢 EVENT: Throttle Disengaged | Target FPS restored to {args.fps:.1f}")
                current_target_fps = new_fps

            now = time.perf_counter()
            elapsed_report = now - last_report_time

            if elapsed_report >= args.report_interval:
                actual_fps = window_batches / elapsed_report
                simd_throughput_m = (window_batches * args.batch_size / (window_simd_ms / 1000.0)) / 1e6
                network_kbps = (window_bytes / elapsed_report) / 1024.0
                avg_simd_latency = window_simd_ms / window_batches
                status_str = "THROTTLED" if throttled else "NOMINAL"

                log_line = (
                    f"📊 [{status_str:<9}] [Batch #{batch_counter:06d}] "
                    f"FPS: {actual_fps:5.1f} / {current_target_fps:5.1f} target | "
                    f"SIMD: {avg_simd_latency:4.2f}ms ({simd_throughput_m:6.2f} M/s) | "
                    f"Payload: {network_kbps:5.2f} KB/s"
                )
                write_log(log_fp, log_line)

                window_batches = 0
                window_bytes = 0
                window_simd_ms = 0.0
                last_report_time = now

            sleep_time = max(0.0, (1.0 / current_target_fps) - (time.perf_counter() - loop_start))
            try:
                await asyncio.sleep(sleep_time)
            except asyncio.CancelledError:
                break

    write_log(log_fp, "🏁 Stream client shutdown sequence finished cleanly.")
    log_fp.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
