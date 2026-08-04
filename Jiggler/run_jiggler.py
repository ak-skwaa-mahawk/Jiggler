#!/usr/bin/env python3
import time
import numpy as np
import jiggler_native
from app import telemetry_buffer

def run_jiggler_pipeline(iterations: int = 5_000_000, continuous: bool = True):
    print(f"🚀 [MULTI-THREADED RAYON ENGINE] Active — Processing {iterations:,} iter batches...")

    input_buffer = np.linspace(-5.0, 5.0, iterations, dtype=np.float64)
    output_buffer = np.empty(iterations, dtype=np.float64)
    threshold = 1.5000

    while True:
        t0 = time.perf_counter_ns()
        violations = jiggler_native.process_drift_batch_zero_copy(
            input_buffer, output_buffer, threshold
        )
        t1 = time.perf_counter_ns()

        total_time_ms = (t1 - t0) / 1e6
        per_pass_ns = (t1 - t0) / iterations
        throughput = iterations / ((t1 - t0) / 1e9)

        print("\n📊 RAYON PARALLEL PERFORMANCE PROFILE")
        print(f" ├── Total Batch Time     : {total_time_ms:.3f} ms")
        print(f" ├── Calculated Throughput: {throughput:,.2f} iterations/sec")
        print(f" ├── Mean Execution Speed : {per_pass_ns:.2f} nanoseconds per pass")
        print(f" └── Out-of-Bounds Trips  : {violations:,} (Allowed: True)")

        telemetry_buffer.push({
            'iterations': iterations,
            'batch_time_ms': total_time_ms,
            'per_pass_ns': per_pass_ns,
            'throughput': throughput,
            'violations': violations
        })

        if not continuous:
            break

        time.sleep(0.001)

if __name__ == "__main__":
    run_jiggler_pipeline(continuous=True)
