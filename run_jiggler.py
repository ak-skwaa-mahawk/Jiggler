import sys
import os
import ctypes

# 1. Load the raw shared object payload natively via ctypes
lib_path = os.path.abspath("./jiggler_native.so")
try:
    jiggler_lib = ctypes.CDLL(lib_path)
    print("[🎛️] Sovereign Python Controller Online. Native C Substrate Linked.")
except OSError as e:
    print(f"[❌] Failed to load binary library directly: {e}")
    sys.exit(1)

# 2. Replicate the strict 48-byte SovereignMetric input layout
class SovereignMetric(ctypes.Structure):
    _fields_ = [
        ("pose", ctypes.c_double * 3),
        ("stability_score", ctypes.c_double),
        ("resonance_delta", ctypes.c_double),
        ("timestamp", ctypes.c_uint64)
    ]

# Derived structure to support the nested pointer tracking mapping
class DerivedMetric(ctypes.Structure):
    _fields_ = [
        ("optimized_resonance", ctypes.c_double),
        ("lifecycle_epoch", ctypes.c_uint64)
    ]

# 3. Explicitly reconstruct the 32-byte GuardedOutput mapping
class GuardedOutput(ctypes.Structure):
    _fields_ = [
        ("allowed", ctypes.c_bool),             # Rust bool (1 byte) + 7 bytes implicit padding
        ("fidelity", ctypes.c_double),          # Rust f64 (8 bytes)
        ("neutralized_reason", ctypes.c_void_p), # Rust *const c_char (8 bytes)
        ("derived_metric", ctypes.c_void_p)     # Rust *mut DerivedMetric (8 bytes)
    ]

# 4. Bind parameters to the execution channel (Enforces 32-byte AAPCS64 block parameters)
try:
    jiggler_lib.check_extraction_guard.argtypes = [ctypes.POINTER(SovereignMetric)]
    jiggler_lib.check_extraction_guard.restype = GuardedOutput
    print("[✅] Complete 32-byte value-return bridges fully synchronized.")
except AttributeError as e:
    print(f"[❌] Base symbol binding failure: {e}")
    sys.exit(1)

# 5. Prepare tuned variables matching your system parameters
test_metric = SovereignMetric()
test_metric.pose = (ctypes.c_double * 3)(21.50, 160.0, 60.0)
test_metric.stability_score = 0.850   # Clears the 0.65 stability baseline
test_metric.resonance_delta = 0.025   # Tightened to clear bounds constraint
test_metric.timestamp = 1686566400

print("\n🚀 Executing value-return memory extraction guard check...")
try:
    output_data = jiggler_lib.check_extraction_guard(ctypes.byref(test_metric))
    
    print("\n[🛰️ NATIVE ENGINE C-FFI TELEMETRY]")
    print(f" ├── Execution Allowed : {output_data.allowed}")
    print(f" ├── Resolution Fidelity: {output_data.fidelity:.6f}")
    
    # Safely resolve the text string pointer address if populated
    if output_data.neutralized_reason:
        reason = ctypes.string_at(output_data.neutralized_reason).decode('utf-8')
    else:
        reason = "None (Pass)"
    print(f" └── Neutralized Reason : {reason}")

    # Safely look at nested tracking telemetry if returned
    if output_data.derived_metric:
        derived = ctypes.cast(output_data.derived_metric, ctypes.POINTER(DerivedMetric)).contents
        print(f"\n[📦 DERIVED METRIC SUBSTRATE]")
        print(f" ├── Optimized Resonance: {derived.optimized_resonance:.6f}")
        print(f" └── Lifecycle Epoch    : {derived.lifecycle_epoch}")

except Exception as parse_err:
    print(f" [❌] Telemetry execution exception: {parse_err}")
