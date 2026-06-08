cat << 'EOF' > api/manifold.py
import time
import numpy as np
import hashlib
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from api.ratelimit import limiter
from grpc_client import get_grpc_client, GrpcSubstrateClient

router = APIRouter()

SHADOW_CONSTANT = 1.04159265
MANIFOLD_C = 3.0e5
TORUS_R_MAJOR = 56.17

class Vector3D(BaseModel):
    x: float
    y: float
    z: float

class AdvancedManifoldPayload(BaseModel):
    vector_id: str
    velocity_vector: Vector3D
    throat_radius: float = 21.86
    magnetic_coupling: float = 1.02

class AdvancedStateMetrics(BaseModel):
    timestamp: float
    state_hash: str
    tensor_density_scalar: float
    lorentz_damping: float
    vector_stable: bool
    rust_substrate_handshake: dict

def compute_tensor_drift(v_vec: Vector3D, r_throat: float) -> tuple[float, float]:
    v = np.array([v_vec.x, v_vec.y, v_vec.z])
    v_magnitude = np.linalg.norm(v)
    boundary_proximity = max(0.001, (TORUS_R_MAJOR - r_throat))
    beta = min(0.9999, v_magnitude / MANIFOLD_C)
    lorentz_factor = 1.0 / np.sqrt(1.0 - beta**2)
    tensor_density = (v_magnitude * np.pi * SHADOW_CONSTANT * lorentz_factor) / boundary_proximity
    return float(tensor_density), float(lorentz_factor)

@router.post("/synchronize", response_model=AdvancedStateMetrics, tags=["Tordial-GS Manifold Interfacing"])
@limiter.limit("5/minute")
async def synchronize_manifold_matrix(
    request: Request, 
    payload: AdvancedManifoldPayload, 
    grpc_core: GrpcSubstrateClient = Depends(get_grpc_client)
):
    try:
        ts = time.time()
        density, gamma = compute_tensor_drift(payload.velocity_vector, payload.throat_radius)
        
        state_string = f"{payload.vector_id}:{density}:{gamma}:{ts}"
        computed_hash = hashlib.sha3_256(state_string.encode()).hexdigest()
        is_stable = not np.isnan(density) and not np.isinf(density) and gamma < 100.0

        # Dispatches structural data downstream to the multiplexed Rust subsystem
        substrate_feedback = await grpc_core.dispatch_vector(
            vector_id=payload.vector_id,
            x=payload.velocity_vector.x,
            y=payload.velocity_vector.y,
            z=payload.velocity_vector.z,
            throat_radius=payload.throat_radius,
            magnetic_coupling=payload.magnetic_coupling
        )

        return AdvancedStateMetrics(
            timestamp=ts,
            state_hash=f"0x{computed_hash}",
            tensor_density_scalar=density if is_stable else 0.00,
            lorentz_damping=gamma,
            vector_stable=is_stable,
            rust_substrate_handshake=substrate_feedback
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Core Sync Error: {str(e)}")
EOF
