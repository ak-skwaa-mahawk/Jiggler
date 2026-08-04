import hmac
import hashlib
import json
import base64
import time
import numpy as np
from typing import Dict, Any

class SecureStateSerializer:
    """Handles high-integrity state vector serialization, hashing, and encryption packaging."""
    def __init__(self, secret_key: bytes):
        if len(secret_key) < 32:
            raise ValueError("Secret cryptographic key must be at least 32 bytes long.")
        self.secret_key = secret_key

    def serialize_agent_state(self, agent_id: str, ekf_state: np.ndarray, ekf_covariance: np.ndarray, pid_integral: np.ndarray) -> str:
        """
        Converts active numpy memory blocks into a base64-encoded, signed JSON string.
        """
        # 1. Map raw multidimensional runtime objects into serializable types
        state_payload = {
            "agent_id": agent_id,
            "timestamp": time.time(),
            "ekf_x": ekf_state.flatten().tolist(),
            "ekf_P": ekf_covariance.tolist(),
            "pid_integral": pid_integral.flatten().tolist()
        }
        
        # 2. Convert payload dictionary to uniform string footprint
        json_bytes = json.dumps(state_payload, sort_keys=True).encode('utf-8')
        encoded_payload = base64.b64encode(json_bytes).decode('utf-8')
        
        # 3. Generate SHA-256 Message Authentication Code (HMAC) signature to guard against manipulation
        signature = hmac.new(self.secret_key, encoded_payload.encode('utf-8'), hashlib.sha256).hexdigest()
        
        # 4. Synthesize unified transfer envelope string
        transfer_envelope = {
            "payload": encoded_payload,
            "signature": signature
        }
        return json.dumps(transfer_envelope)

    def deserialize_agent_state(self, envelope_str: str) -> Dict[str, Any]:
        """
        Validates cryptographic signatures and reconstitutes raw system arrays.
        Throws a SecurityError if the data payload has been altered.
        """
        envelope = json.loads(envelope_str)
        payload_str = envelope["payload"]
        provided_signature = envelope["signature"]
        
        # 1. Verify message signature before processing strings or allocations
        expected_signature = hmac.new(self.secret_key, payload_str.encode('utf-8'), hashlib.sha256).hexdigest()
        
        if not hmac.compare_digest(expected_signature, provided_signature):
            raise PermissionError("[SECURITY FAULT] State packet signature validation failed! Rejecting payload.")
            
        # 2. Reconstitute JSON object elements
        decoded_bytes = base64.b64decode(payload_str.encode('utf-8'))
        data = json.loads(decoded_bytes.decode('utf-8'))
        
        # 3. Cast python list tracking elements back into native NumPy float configurations
        return {
            "agent_id": data["agent_id"],
            "timestamp": data["timestamp"],
            "ekf_x": np.array(data["ekf_x"]).reshape(-1, 1),
            "ekf_P": np.array(data["ekf_P"]),
            "pid_integral": np.array(data["pid_integral"])
        }
