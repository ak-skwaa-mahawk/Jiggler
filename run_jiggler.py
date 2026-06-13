import sys
import os
import ctypes
import time

# 1. Link Native Substrate
lib_path = os.path.abspath("./jiggler_native.so")
try:
    jiggler_lib = ctypes.CDLL(lib_path)
except OSError as e:
    print(f"[❌] Failed to load binary library: {e}")
    sys.exit(1)

class SovereignMetric(ctypes.Structure):
    _fields_ = [
        ("pose", ctypes.c_double * 3),          # pose[0]=d, pose[1]=r, pose[2]=sigma_t
        ("stability_score", ctypes.c_double),    # rho
        ("resonance_delta", ctypes.c_double),    # baseline_intent
        ("timestamp", ctypes.c_uint64)
    ]

class DerivedMetric(ctypes.Structure):
    _fields_ = [
        ("optimized_resonance", ctypes.c_double),
        ("lifecycle_epoch", ctypes.c_uint64)
    ]

class GuardedOutput(ctypes.Structure):
    _fields_ = [
        ("allowed", ctypes.c_bool),
        ("fidelity", ctypes.c_double),
        ("neutralized_reason", ctypes.c_void_p),
        ("derived_metric", ctypes.c_void_p)
    ]

jiggler_lib.check_extraction_guard.argtypes = [ctypes.POINTER(SovereignMetric)]
jiggler_lib.check_extraction_guard.restype = GuardedOutput

# 2. Benchmark Controller Setup
ITERATIONS = 250000
print(f"⚡ [TORDIAL MANIFOLD BENCHMARK] Initializing {ITERATIONS:,} execution iterations...")

# Prepare operational arrays to test varying drift scenarios
# Phase A: Deep Goldilocks center
# Phase B: Gentle Transitional drift
# Phase C: Critical Out-of-Bounds threshold breach
test_cases = [
    ((27.5, 155.0, 62.0), 0.325, 0.87, "Goldilocks Basin Center"),
    ((31.5, 155.0, 62.0), 0.325, 0.87, "Transitional Zone Drift"),
    ((45.0, 155.0, 62.0), 0.325, 0.87, "Critical Out-of-Bounds Breach")
]

print("\n--- RUNNING HIGH-FIDELITY SPEED TESTS ---")

for pose, rho, intent, label in test_cases:
    metric = SovereignMetric()
    metric.pose = (ctypes.c_double * 3)(*pose)
    metric.stability_score = rho
    metric.resonance_delta = intent
    metric.timestamp = 1686566400
    
    # Warm up compilation/cache lines
    for _ in range(100):
        res = jiggler_lib.check_extraction_guard(ctypes.byref(metric))
        if res.derived_metric:
            jiggler_lib.free_guarded_output(res)

    # High-precision timing loop
    start_time = time.perf_counter_ns()
    
    for i in range(ITERATIONS):
        res = jiggler_lib.check_extraction_guard(ctypes.byref(metric))
        # Safely release heap memory generated inside the Rust box to maintain 0.0% leak benchmarks
        if res.derived_metric:
            jiggler_lib.free_guarded_output(res)
            
    end_time = time.perf_counter_ns()
    
    # Calculate performance metrics
    total_duration_ms = (end_time - start_time) / 1_000_000.0
    avg_latency_ns = (end_time - start_time) / ITERATIONS
    throughput = ITERATIONS / (total_duration_ms / 1000.0)
    
    # Final confirmation run for data checking
    final_check = jiggler_lib.check_extraction_guard(ctypes.byref(metric))
    drift = 0.0
    if final_check.derived_metric:
        derived = ctypes.cast(final_check.derived_metric, ctypes.POINTER(DerivedMetric)).contents
        drift = derived.optimized_resonance
        jiggler_lib.free_guarded_output(final_check)

    print(f"\n📊 TARGET LOG PROFILE: {label}")
    print(f" ├── Total Time for Loop : {total_duration_ms:.2f} ms")
    print(f" ├── Calculated Throughput: {throughput:,.2f} iterations/sec")
    print(f" ├── Mean Execution Speed: {avg_latency_ns:.1f} nanoseconds per pass")
    print(f" └── Computed Drift Space : {drift:.4f} units (Allowed: {final_check.allowed})")

print("\n🏁 Benchmark Suite Execution Complete. Standard Baseline Established.")
