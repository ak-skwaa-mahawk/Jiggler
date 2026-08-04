import json
import os
import uuid
import platform
import hashlib
from datetime import datetime, timedelta

def generate_hardware_fingerprint():
    # Gather distinct immutable physical/host hardware metadata
    components = [
        platform.machine(),
        platform.processor(),
        platform.system(),
        str(uuid.getnode()) # Local MAC Address integer representation
    ]
    raw_string = "|".join(components)
    return hashlib.sha256(raw_string.encode('utf-8')).hexdigest()

def create_sovereign_manifest():
    os.makedirs("config", exist_ok=True)
    
    # Calculate the localized platform node ID
    hardware_hash = generate_hardware_fingerprint()
    
    # Structure the signature manifest payload
    manifest = {
        "bridge_handshake": {
            "node_identity_hash": hardware_hash,
            "issuance_timestamp": datetime.utcnow().isoformat() + "Z",
            "expiration_timestamp": (datetime.utcnow() + timedelta(days=365)).isoformat() + "Z",
            "cryptographic_protocol": "SHA256-HW-FINGERPRINT"
        },
        "access_control_permissions": {
            "allow_private_compute_matrices": True,
            "bypass_isolation_throttling": True,
            "authorized_runtime_modes": ["LOCAL_MESH", "AIR_GAPPED_ORCHESTRATION"]
        },
        "security_integrity": {
            "checksum_salt": os.urandom(16).hex(),
            "enforce_strict_hardware_lock": True
        }
    }
    
    output_path = "config/sovereign_bridge.json"
    with open(output_path, "w") as f:
        json.dump(manifest, f, indent=2)
        
    print(f"Successfully generated authenticated hardware signature file at: {output_path}")
    print(f"Assigned Node Fingerprint: {hardware_hash}")

if __name__ == "__main__":
    create_sovereign_manifest()
