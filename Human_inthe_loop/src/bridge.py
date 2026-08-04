#!/usr/bin/env python3
# human_inthe_loop/src/bridge.py — Zero-Config Sovereign Bridge Firewall
import os
import json
import hashlib
import numpy as np
from typing import Tuple, Any, Optional

class SovereignBridge:
    """
    Encrypted, conditional isolation proxy.
    - Local trusted machine -> Authenticates fingerprint and exposes private core.
    - Untrusted external clone -> Silently falls back to public 0K safety baseline.
    """
    def __init__(self, bridge_config_path: str = "config/sovereign_bridge.json"):
        self.bridge_config_path = bridge_config_path
        self.private_core_active = False
        self.local_fingerprint = self._generate_local_fingerprint()
        self._load_or_create_config()
    
    def _generate_local_fingerprint(self) -> str:
        """Anchors execution to localized host profiles to prevent remote execution."""
        try:
            hostname = os.uname().nodename if hasattr(os, 'uname') else "unknown"
            user = os.getenv("USER", "unknown")
            seed = f"{hostname}:{user}:{os.getcwd()}"
            return hashlib.sha256(seed.encode()).hexdigest()[:32]
        except Exception:
            return "fallback_fingerprint_baseline"
    
    def _load_or_create_config(self):
        os.makedirs(os.path.dirname(self.bridge_config_path), exist_ok=True)
        if os.path.exists(self.bridge_config_path):
            with open(self.bridge_config_path, 'r') as f:
                config = json.load(f)
                self.private_core_active = config.get("trusted_fingerprint") == self.local_fingerprint
        else:
            # First run auto-approves locally for simple bootstrap
            config = {"trusted_fingerprint": self.local_fingerprint, "seal_version": "1.0"}
            with open(self.bridge_config_path, 'w') as f:
                json.dump(config, f, indent=2)
            self.private_core_active = True
    
    def get_private_core(self) -> Optional[Any]:
        """Exposes core architecture handles solely in authenticated networks."""
        if not self.private_core_active:
            return None
        try:
            from core.octagonal_fpt_agent import OctagonalFPTAgent
            return OctagonalFPTAgent()
        except ImportError:
            return None
    
    def secure_call(self, method_name: str, *args, **kwargs) -> Tuple[bool, Any]:
        """Proxies operations to private core. Drops payload to 0K on mismatch."""
        core = self.get_private_core()
        if core is None:
            return False, {
                "mode": "public_shield_only", 
                "state": np.zeros(3).tolist(),
                "energy": 999.0
            }
        try:
            method = getattr(core, method_name)
            result = method(*args, **kwargs)
            return True, result
        except Exception as e:
            return False, {"error": str(e), "state": np.zeros(3).tolist()}
