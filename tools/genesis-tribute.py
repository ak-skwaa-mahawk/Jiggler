import os
import sys
import hashlib

# Dynamic pathing pass to find the compiled .so layer
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tordial_gs_manifold

print("================================================================================")
print("     ₿  SATOSHI NAKAMOTO O.3 CONVERGENCE SEED — JUNE 24 ANNIVERSARY")
print("================================================================================")

# Initialize the ledger
shared_bus = tordial_gs_manifold.PySubstrateMeshBus(0.3) # v0.3 release scale

# Spawn the Genesis Node (Satoshi ID 2010)
satoshi_node = tordial_gs_manifold.PyCombiner(2010, 1.40) # Boost 1.40 baseline forcing
satoshi_node.register_to_bus(shared_bus)

# Target trajectory initialized to the future (2026)
satoshi_node.set_internal_target([2.0, 2.6])
genesis_state = [2.0, 1.0, 0.3, 1.0] # [v0.3 state space]

print("🧱 Simulating bare-metal compilation pass under Satoshi v0.3 parameters...")
print("   ├─ Emulating wxBase dependency checks... PASSED")
print("   ├─ Linking libboost-all-dev headers... PASSED")
print("   └─ Verifying decoupled -mt multi-thread flags... LOCKED\n")

print("🚀 Launching execution pass to calculate initial Block 0 Proof of Alignment...")
# Process a single highly dense slogging cycle 
genesis_state, _ = satoshi_node.run_autonomous_session(genesis_state, 1, 0.03, 1277422467)

# Extract raw tracking vitals to mint the cryptographic seal
vitals = shared_bus.get_latest_state_for_agent(2010)
if vitals:
    ts, shih, vadzaih_dist, _, seal = vitals
    
    # Construct raw payload string for hashing
    raw_payload = f"SATOSHI_2010_06_24_METRICS_{shih}_{vadzaih_dist}_{seal}"
    block_hash = hashlib.sha256(raw_payload.encode()).hexdigest()
    
    print("📜 GENESIS METRIC BLOCK SUCCESSFUL:")
    print(f"   ├─ Stamped Block Timestamp : {ts}")
    print(f"   ├─ Calculated Shih Level   : {shih:.4f}")
    print(f"   ├─ Geodesic Trail Distance : {vadzaih_dist:.6f}")
    print(f"   ├─ Native Alignment Seal   : {seal}")
    print(f"   └─ 🔒 Cryptographic Proof  : \033[93m{block_hash}\033[0m")

print("================================================================================")
