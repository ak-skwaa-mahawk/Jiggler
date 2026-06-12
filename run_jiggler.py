import sys
import os
import ctypes

lib_path = os.path.abspath("./jiggler_native.so")
try:
    jiggler_lib = ctypes.CDLL(lib_path)
    print("[🎛️] Sovereign Python Controller Online. Native C Substrate Linked.")
except OSError as e:
    print(f"[❌] Failed to load binary library directly: {e}")
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

try:
    jiggler_lib.check_extraction_guard.argtypes = [ctypes.POINTER(SovereignMetric)]
    jiggler_lib.check_extraction_guard.restype = GuardedOutput
    print("[✅] Complete 32-byte value-return bridges fully synchronized.")
except AttributeError as e:
    print(f"[❌] Base symbol binding failure: {e}")
    sys.exit(1)

# Input real data parameters within your attractor basin limits
test_metric = SovereignMetric()
test_metric.pose = (ctypes.c_double * 3)(27.50, 155.0, 62.0) # d, r, sigma_t
test_metric.stability_score = 0.325                         # rho (inside 0.31-0.34)
test_metric.resonance_delta = 0.870                         # baseline intent input value
test_metric.timestamp = 1686566400

print("\n🚀 Executing value-return memory extraction guard check...")
try:
    output_data = jiggler_lib.check_extraction_guard(ctypes.byref(test_metric))
    
    print("\n[🛰️ NATIVE ENGINE C-FFI TELEMETRY]")
    print(f" ├── Execution Allowed : {output_data.allowed}")
    print(f" ├── Resolution Fidelity: {output_data.fidelity:.6f}")
    
    if output_data.neutralized_reason:
        reason = ctypes.string_at(output_data.neutralized_reason).decode('utf-8')
    else:
        reason = "None (Pass)"
    print(f" └── Neutralized Reason : {reason}")

    if output_data.derived_metric:
        derived = ctypes.cast(output_data.derived_metric, ctypes.POINTER(DerivedMetric)).contents
        print(f"\n[📦 DERIVED METRIC SUBSTRATE]")
        print(f" ├── Attractor Drift Offset: {derived.optimized_resonance:.6f}")
        print(f" └── Lifecycle Epoch       : {derived.lifecycle_epoch}")

except Exception as parse_err:
    print(f" [❌] Telemetry execution exception: {parse_err}")
