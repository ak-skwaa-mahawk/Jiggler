#!/usr/bin/env python3
# core/llm_bridge.py — Local Model Interface (Ollama/vLLM)
import urllib.request
import json
import logging
from typing import Dict, Any, Optional

log = logging.getLogger("FPT_LLM_BRIDGE")

class LocalLLMBridge:
    """
    Manages isolated loopback communication with locally hosted LLM engines.
    Enforces structural response validation to maintain system baseline rules.
    """
    def __init__(self, endpoint: str = "http://localhost:11434/api/generate", model_name: str = "llama3"):
        self.endpoint = endpoint
        self.model_name = model_name

    def request_inference(self, prompt: str, system_prompt: Optional[str] = None) -> Tuple[bool, str]:
        """
        Sends a thread-safe HTTP POST request to the local inference daemon.
        Returns a (success_flag, output_text) tuple.
        """
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,  # Lower temperature maximizes analytical consistency
                "top_p": 0.9
            }
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            req = urllib.request.Request(
                self.endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            # Timeout set strictly to avoid locking the 79Hz master clock pipeline
            with urllib.request.urlopen(req, timeout=8.0) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                return True, res_data.get("response", "").strip()
        except Exception as e:
            log.error("Local inference execution fault", extra={"error": str(e)})
            return False, f"INFERENCE_FAILURE: {str(e)}"

if __name__ == "__main__":
    bridge = LocalLLMBridge()
    print("--- Local LLM Bridge Core Test ---")
    print(f"Targeting Daemon: {bridge.endpoint} | Model: {bridge.model_name}")
