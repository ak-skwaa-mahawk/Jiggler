#!/usr/bin/env python3
# Platform/runtime/telemetry_server.py — Advanced Intelligent Injin Controller
import http.server
import socketserver
import json
import sys
import os
import urllib.request
import numpy as np

# Bind parent directory workspace parameters
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.octagonal_fpt_agent import OctagonalFPTAgent
from ai.policy_governance.evaluator import SovereignPolicyGuard

# Initialize Platform Core Architecture Elements
fpt_agent = OctagonalFPTAgent()
policy_guard = SovereignPolicyGuard(base_path="ai/policy_governance")

# Target Local LLM Core Parameters (Ollama loopback endpoint default)
OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3"

SYSTEM_STATE = np.array([0.4, 0.3, 0.3], dtype=np.float32)
LIVE_METRICS = {
    "status": "🟢 LIVE CORE",
    "frequency_hz": 79.0,
    "current_energy": 0.0,
    "last_verdict": "PENDING"
}

class SovereignIntelligentBridge(http.server.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if "action=telemetry" in self.path:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(LIVE_METRICS).encode("utf-8"))

    def do_POST(self):
        global SYSTEM_STATE
        if "action=execute" in self.path:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            payload = json.loads(post_data.decode('utf-8'))
            user_prompt = payload.get("command", "").strip()
            
            print(f"\n📥 [Injin Prompt Ingress]: '{user_prompt}'")
            
            # Phase 1: Call Local Unquantized LLM Worker
            ai_response_text = self._query_local_llm(user_prompt)
            
            # Phase 2: Convert Output Metadata Into Evaluation Trajectories
            seed = sum(ord(char) for char in ai_response_text)
            np.random.seed(seed)
            task_trajectory = np.random.uniform(-1.0, 1.0, 3).astype(np.float32)
            
            # Phase 3: Run Mass-Preserving Math Engine
            compute_results = fpt_agent.compute_phase_step(SYSTEM_STATE, task_trajectory)
            calculated_energy = compute_results["energy"]
            candidate_state = compute_results["state"]
            
            # Phase 4: Enforce Hardcoded Governance Guardrails
            metrics_package = {"variational_energy": calculated_energy, "cognitive_drift": 0.01}
            is_clear = policy_guard.verify_runtime_safety("web_prompt_execution", metrics_package)
            
            if is_clear:
                SYSTEM_STATE = np.array(candidate_state, dtype=np.float32)
                LIVE_METRICS["current_energy"] = calculated_energy
                LIVE_METRICS["last_verdict"] = "APPROVE"
                final_reply = ai_response_text
            else:
                LIVE_METRICS["current_energy"] = calculated_energy
                LIVE_METRICS["last_verdict"] = "HALT_FOR_HUMAN_OVERRIDE"
                final_reply = "⚠️ [GOVERNANCE CIRCUIT BREAKER TRIPPED]: The generated calculation trajectory breached safety parameters. Action aborted."

            # Transmit Response Data Array Back to Frontend Screen Component
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            
            self.wfile.write(json.dumps({"status": "SUCCESS", "message": final_reply}).encode("utf-8"))

    def _query_local_llm(self, prompt: str) -> str:
        """Sends inference requests to an air-gapped Ollama microservice instance."""
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "system": "You are Skoden Injin, an authoritative, highly strategic sovereign artificial intelligence platform developed by Two Mile Solutions LLC under authority 99733. Speak concisely with clear, unfiltered tactical clarity."
        }
        try:
            req = urllib.request.Request(
                OLLAMA_ENDPOINT,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=12.0) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                return res_data.get("response", "").strip()
        except Exception as e:
            return f"Inference Fallback Offline. Local compute loop executed safely, but local LLM endpoint on port 11434 could not be reached. [Error: {str(e)}]"

    def log_message(self, format, *args):
        return

if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", 7979), SovereignIntelligentBridge) as httpd:
        print("="*80)
        print("🔥 SKODEN INJIN INTELLIGENT WORKSPACE CORE ENGINE ACTIVE")
        print("⚡ Route Pipeline Linked: Google Sites UI ➔ Port 7979 ➔ Ollama Local Compute")
        print("="*80)
        httpd.serve_forever()
