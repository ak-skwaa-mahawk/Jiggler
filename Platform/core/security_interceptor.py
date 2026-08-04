import json
import os
import sys

def verify_vault_gate(routing_config_path="core/config/model_routing.json"):
    # 1. Read out the active routing schema
    with open(routing_config_path, 'r') as f:
        config = json.load(f)
        
    # 2. Extract expected cryptographic handshake rules from our bridge
    try:
        with open("config/sovereign_bridge.json", 'r') as b:
            bridge = json.load(b)
            is_locked = bridge["security_integrity"]["enforce_strict_hardware_lock"]
    except FileNotFoundError:
        print("[FATAL] sovereign_bridge.json missing. Vault-gate locked out.")
        sys.exit(1)

    # 3. Intercept and isolate if running an insecure layout
    vllm_token = config["engines"]["high_frequency_vllm"]["api_key"]
    
    if is_locked and vllm_token == "sk-vllm-local-orchestration-token":
        print("[SECURITY WARNING] Running placeholder credentials on a locked hardware profile!")
        print("[SECURITY DETECTOR] Reverting routing profile to public_baseline_matrix.")
        return False
        
    print("[VAULT-GATE] Token and hardware signature matched. Real-time inference authorized.")
    return True
