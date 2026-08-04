#!/usr/bin/env python3
# nodes/flame_quantum_node.py — Quantum Phase Node
import sys
import time
import numpy as np

def run_quantum_loop():
    print("✨ QUANTUM NODE INITIALIZED — ENTERING PHASE MONITORING MODE", flush=True)
    step = 0
    while True:
        # Generate a synthetic 3D unitary trajectory phase vector
        t = time.time()
        phase_x = np.sin(t * 0.5)
        phase_y = np.cos(t * 0.7)
        phase_z = np.sin(t * 1.1)
        
        state_vector = np.array([phase_x, phase_y, phase_z])
        normalized_energy = float(np.linalg.norm(state_vector))
        
        # Flush stdout instantly so the Master Orchestrator catches the text streams
        print(f"[QUANTUM] Step {step} | Energy Norm: {normalized_energy:.4f} | Vector: {state_vector.tolist()}", flush=True)
        step += 1
        time.sleep(1.0)

if __name__ == "__main__":
    try:
        run_quantum_loop()
    except KeyboardInterrupt:
        print("\n[QUANTUM] Clean termination requested.", flush=True)
        sys.exit(0)
