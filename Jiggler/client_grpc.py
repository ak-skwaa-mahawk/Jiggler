import grpc
import time
import queue
import threading
import numpy as np
import proto.manifold_pb2 as manifold_pb2
import proto.manifold_pb2_grpc as manifold_pb2_grpc

def run():
    print("⚡ [gRPC CLIENT] Connecting to Manifold Substrate on 127.0.0.1:50051...", flush=True)
    channel = grpc.insecure_channel('127.0.0.1:50051')
    stub = manifold_pb2_grpc.ManifoldInferenceServiceStub(channel)

    payload_size = 5_000_000
    print(f"📦 Pre-allocating {payload_size:,} float payload buffer...", flush=True)
    
    # Pre-allocate binary payload (20MB)
    data_bytes = np.random.uniform(-0.1, 0.1, payload_size).astype(np.float32).tobytes()

    q = queue.Queue()

    # Generator reading directly from thread queue
    def request_stream():
        while True:
            item = q.get()
            if item is None:
                break
            yield item

    start_time = time.time()

    # Start bidirectional gRPC RPC call
    response_iterator = stub.StreamDriftBatch(request_stream())

    # Consumer thread function
    def listen_responses():
        for resp in response_iterator:
            print(
                f"✅ [RESPONSE] Batch #{resp.batch_id} | "
                f"Rust Compute: {resp.batch_time_ms:.2f}ms | "
                f"Throughput: {resp.throughput_iters_per_sec / 1e6:.2f} M/s | "
                f"Per-Pass: {resp.per_pass_ns:.2f}ns | "
                f"Out of bounds: {resp.out_of_bounds_trips:,}",
                flush=True
            )

    # Spawn listener in background
    listener = threading.Thread(target=listen_responses, daemon=True)
    listener.start()

    # Producer loop: push items into queue
    for batch_id in range(1, 6):
        print(f"🚀 Pushing Batch #{batch_id} to queue...", flush=True)
        req = manifold_pb2.DriftBatchRequest(
            batch_id=batch_id,
            threshold=0.048,
            input_buffer=data_bytes
        )
        q.put(req)
        time.sleep(0.01) # Yield execution brief fraction to flush socket

    # Signal generator termination and wait for listener thread to finish
    q.put(None)
    listener.join()

    total_time = time.time() - start_time
    print(f"\n🎉 Stream finished in {total_time:.2f}s across 25,000,000 elements.", flush=True)

if __name__ == '__main__':
    run()
