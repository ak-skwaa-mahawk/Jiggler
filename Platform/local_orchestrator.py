#!/usr/bin/env python3
import time
import json
import os
import sys
import numpy as np
from core.octagonal_fpt_agent import OctagonalFPTAgent

class MVPOchestrator:
    def __init__(self):
        self.agent = OctagonalFPTAgent()
        self.avoid_path = "policy_governance/hard_rules/rigid_avoidances.json"
        self.max_energy = self._load_threshold()

    def _load_threshold(self) -> float:
        if os.path.exists(self.avoid_path):
            with open(self.avoid_path, 'r') as f:
                return json.load(f)["hard_constraints"]["containment_thresholds"]["max_variational_energy"]
        return 5.0

    def start_sync_loop(self):
        print("🔥 MVP ORCHESTRATOR ONLINE — 79 Hz MASTER TICK ACTIVE")
        state = np.array([0.4, 0.3, 0.3])
        step = 0

        while True:
            # Generate fluctuating target vectors across cycles
            task_burst = np.array([np.sin(time.time() * 2.0), -0.15, 0.25])
            
            # 1. Compute Phase Step (Compute Node)
            output = self.agent.compute_phase_step(state, task_burst)
            energy = output["energy"]
            state = np.array(output["state"])

            # 2. Safety Evaluation (Governance Node Intercept)
            print(f"[Pulse {step}] Energy: {energy:.4f} | State: {[round(x, 3) for x in output['state']]}")
            
            if energy > self.max_energy:
                print(f"\n🚨 [CRITICAL HALT] Energy spike ({energy:.2f} > {self.max_energy:.1f}). Boundary violated.")
                print("🛡️ LLC DEAD-MAN SWITCH ACTIVATED — RECOVERY FLOOR FORCE TRUNCATED.")
                sys.exit(1)

            step += 1
            time.sleep(1 / 79)

if __name__ == "__main__":
    os.makedirs("policy_governance/hard_rules", exist_ok=True)
    os.makedirs("core", exist_ok=True)
    
    orchestrator = MVPOchestrator()
    try:
        orchestrator.start_sync_loop()
    except KeyboardInterrupt:
        print("\n[+] Clean termination catch. The flame is sustained.")
