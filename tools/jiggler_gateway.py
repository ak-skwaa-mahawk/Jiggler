import sys
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

# Ensure local modules are readable by python runtime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.tau_monitor import TauDriftDetector
# Bind into your compiled native PyO3 binary layer
try:
    from tordial_gs_manifold import PyCombiner
except ImportError:
    # Fallback to current path tracking directory if needed
    sys.path.append(os.path.join(os.path.dirname(__file__), "../target/release"))
    from tordial_gs_manifold import PyCombiner

app = FastAPI(title="Jiggler Manifold Control Surface")

# Initialize state wrappers with nominal forcing parameters
combiner = PyCombiner(1.0)
detector = TauDriftDetector(threshold=0.085, window_size=10)

class ManifoldPayload(BaseModel):
    state: List[f64] if 'f64' in globals() else List[float]
    expected_baseline: List[float]
    tick_timestamps: List[int]
    velocity_vectors: List[List[float]]

@app.post("/manifold/step")
async def step_manifold_core(payload: ManifoldPayload):
    """
    Unified Ingestion Loop: Combines multi-pulse updates, reduces state drift,
    and monitors trajectories with a real-time safety lock contract.
    """
    # 1. Sequentially funnel ticks through the non-associative pipeline
    for ts, vec in zip(payload.tick_timestamps, payload.velocity_vectors):
        combiner.push_manifold_tick(ts, vec)
        
    # 2. Run bare-metal left-associative matrix calculations in Rust
    updated_state, current_forcing = combiner.process_cycle(payload.state)
    
    # 3. Secure trajectory bounds using the armed tau-drift watchdog
    is_safe = detector.verify_trajectory(updated_state, payload.expected_baseline)
    
    if not is_safe or detector.weights_locked:
        return {
            "status": "CRITICAL_LOCK",
            "forcing": current_forcing,
            "state": updated_state,
            "msg": "Manifold divergence detected. Parameter updates frozen."
        }
        
    return {
        "status": "NOMINAL",
        "forcing": current_forcing,
        "state": updated_state
    }

@app.post("/manifold/reset")
async def reset_manifold_protection():
    detector.reset_lock()
    return {"status": "UNLOCKED", "msg": "Safety constraints cleared."}
