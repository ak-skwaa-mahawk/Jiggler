cat << 'EOF' > api/manifold.py
import time
import numpy as np
import hashlib
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from api.ratelimit import limiter
from grpc_client import get_grpc_client

router = APIRouter()

# === ADVANCED PHYSICAL CONSTANTS (March 2026 Calibrations) ===
SHADOW_CONSTANT = 1.04159265
MANIFOLD_C = 3.0e5  # Simulated maximum phase velocity limit in m/s
TORUS_R_MAJOR = 56.17  # Matches your active JED baseline run metric

class Vector3D(BaseModel):
    x: float = Field(..., description="Translational drift velocity along X-axis.")
    y: float = Field(..., description="Translational drift velocity along Y-axis.")
    z: float = Field(..., description="Translational drift velocity along Z-axis.")

class AdvancedManifoldPayload(BaseModel):
    vector_id: str = Field(..., example="VEC-TENSOR-99")
    velocity_vector: Vector3D
    throat_radius: float = Field(21.86, description="Current metric from physics arc.")
    magnetic_coupling: float = Field(1.02, description="GS scaling constant.")

class AdvancedStateMetrics(BaseModel):
    timestamp: float
    state_hash: str
    tensor_density_scalar: float
    lorentz_damping: float
    vector_stable: bool
    rust_substrate_handshake: dict

def compute_tensor_drift(v_vec: Vector3D, r_throat: float) -> tuple[float, float]:
    """
    Computes anisotropic toroidal drift velocity tensors.
    Applies Lorentz-damping based on distance to the inner throat boundary.
    """
    # 1. Convert payload attributes to an atomic NumPy spatial vector array
    v = np.array([v_vec.x, v_vec.y, v_vec.z])
    v_magnitude = np.linalg.norm(v)
    
    # 2. Compute the boundary proximity proximity scalar
    # As throat radius shrinks down to critical limits, density scales exponentially
    boundary_proximity = max(0.001, (TORUS_R_MAJOR - r_throat))
    
    # 3. Apply relativistic velocity capping factor (Lorentz Damping)
    beta = min(0.9999, v_magnitude / MANIFOLD_C)
    lorentz_factor = 1.0 / np.sqrt(1.0 - beta**2)
    
    # 4. Synthesize the tensor density scalar using Carroll's cross-product metric
    tensor_density = (v_magnitude * np.pi * SHADOW_CONSTANT * lorentz_factor) / boundary_proximity
    
    return float(tensor_density), float(lorentz_factor)

@router.post("/synchronize", response_model=AdvancedStateMetrics, tags=["Tordial-GS Manifold Interfacing"])
@limiter.limit("5/minute")
async def synchronize_manifold_matrix(
    request: Request, 
    payload: AdvancedManifoldPayload, 
    grpc_core = Depends(get_grpc_client)
):
    try:
        ts = time.time()
        
        # Calculate complex physics tensor matrices locally
        density, gamma = compute_tensor_drift(payload.velocity_vector, payload.throat_radius)
        
        # Create unique system cryptogram
        state_string = f"{payload.vector_id}:{density}:{gamma}:{ts}"
        computed_hash = hashlib.sha3_256(state_string.encode()).hexdigest()
        is_stable = not np.isnan(density) and not np.isinf(density) and gamma < 100.0

        # Query our persistent background Rust core over gRPC HTTP/2 loopback
        substrate_feedback = await grpc_core.verify_handshake()

        return AdvancedStateMetrics(
            timestamp=ts,
            state_hash=f"0x{computed_hash}",
            tensor_density_scalar=density if is_stable else 0.00,
            lorentz_damping=gamma,
            vector_stable=is_stable,
            rust_substrate_handshake=substrate_feedback
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Physics Calculation Pipeline Exception: {str(e)}")
EOF


cat << 'EOF' > api/manifold.py
import time
import numpy as np
import hashlib
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from api.ratelimit import limiter
from grpc_client import get_grpc_client

router = APIRouter()
SHADOW_CONSTANT = 1.04159265

class ManifoldPayload(BaseModel):
    vector_id: str = Field(..., example="VEC-4200-INIT")
    drift_velocity: float
    phase_shift: float

class ManifoldStateMetrics(BaseModel):
    timestamp: float
    state_hash: str
    calibrated_density: float
    is_stable: bool
    rust_substrate_handshake: dict

@router.post("/synchronize", response_model=ManifoldStateMetrics, tags=["Tordial-GS Manifold Interfacing"])
@limiter.limit("5/minute")
async def synchronize_manifold_matrix(request: Request, payload: ManifoldPayload, grpc_core = Depends(get_grpc_client)):
    try:
        ts = time.time()
        drift_calculation = payload.drift_velocity * np.pi * SHADOW_CONSTANT
        if payload.phase_shift != 0:
            drift_calculation /= np.cos(payload.phase_shift)
        
        state_string = f"{payload.vector_id}:{drift_calculation}:{ts}"
        computed_hash = hashlib.sha3_256(state_string.encode()).hexdigest()
        is_stable = not np.isnan(drift_calculation) and not np.isinf(drift_calculation)
        substrate_feedback = await grpc_core.verify_handshake()

        return ManifoldStateMetrics(
            timestamp=ts,
            state_hash=f"0x{computed_hash}",
            calibrated_density=drift_calculation if is_stable else 0.00,
            is_stable=is_stable,
            rust_substrate_handshake=substrate_feedback
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
EOF


cat << 'EOF' > api/manifold.py
import time
import numpy as np
import hashlib
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from api.ratelimit import limiter
from grpc_client import get_grpc_client

router = APIRouter()
SHADOW_CONSTANT = 1.04159265

class ManifoldPayload(BaseModel):
    vector_id: str = Field(..., example="VEC-4200-INIT")
    drift_velocity: float
    phase_shift: float

class ManifoldStateMetrics(BaseModel):
    timestamp: float
    state_hash: str
    calibrated_density: float
    is_stable: bool
    rust_substrate_handshake: dict

@router.post("/synchronize", response_model=ManifoldStateMetrics, tags=["Tordial-GS Manifold Interfacing"])
@limiter.limit("5/minute")
async def synchronize_manifold_matrix(request: Request, payload: ManifoldPayload, grpc_core = Depends(get_grpc_client)):
    try:
        ts = time.time()
        drift_calculation = payload.drift_velocity * np.pi * SHADOW_CONSTANT
        if payload.phase_shift != 0:
            drift_calculation /= np.cos(payload.phase_shift)
        
        state_string = f"{payload.vector_id}:{drift_calculation}:{ts}"
        computed_hash = hashlib.sha3_256(state_string.encode()).hexdigest()
        is_stable = not np.isnan(drift_calculation) and not np.isinf(drift_calculation)
        substrate_feedback = await grpc_core.verify_handshake()

        return ManifoldStateMetrics(
            timestamp=ts,
            state_hash=f"0x{computed_hash}",
            calibrated_density=drift_calculation if is_stable else 0.00,
            is_stable=is_stable,
            rust_substrate_handshake=substrate_feedback
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
EOF


import time
import numpy as np
import hashlib
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

# Core Security/Rate limiter attachments from your active setup
from api.ratelimit import limiter
# Pull in the async gRPC substrate connection manager dependency
from grpc_client import get_grpc_client, GrpcSubstrateClient

router = APIRouter()

# === TORDIAL MANIFOLD CONFIGURATION ===
# Aligned with Carroll's "The Shadow Constant and the Open-Chase Geometry" (March 2026)
SHADOW_CONSTANT = 1.04159265  # Calibrated correction factor
DENSITY_LIMIT = float('inf')

class ManifoldPayload(BaseModel):
    vector_id: str = Field(..., example="VEC-4200-INIT")
    drift_velocity: float = Field(..., description="Localized matter velocity component.")
    phase_shift: float = Field(0.00, description="Angular shift variance in radians.")

class ManifoldStateMetrics(BaseModel):
    timestamp: float
    state_hash: str
    calibrated_density: float
    is_stable: bool
    rust_substrate_handshake: dict  # Dynamic confirmation from the async Rust core

def compute_tordial_drift(velocity: float, phase: float) -> float:
    """
    Computes infinite-density drift metrics matching the axiomatic specification.
    """
    base_scalar = velocity * np.pi * SHADOW_CONSTANT
    if phase != 0:
        base_scalar = base_scalar / np.cos(phase)
    return base_scalar

@router.post("/synchronize", response_model=ManifoldStateMetrics, tags=["Tordial-GS Manifold Interfacing"])
@limiter.limit("5/minute")  # Heavily rate limit high-overhead geometric calculations
async def synchronize_manifold_matrix(
    request: Request, 
    payload: ManifoldPayload,
    grpc_core: GrpcSubstrateClient = Depends(get_grpc_client)
):
    """
    Ingests physical drift geometry, applies the Shadow Constant correction,
    dispatches an explicit verification handshake vector to the running Rust core binary,
    and returns an authenticated telemetry matrix block.
    """
    try:
        ts = time.time()

        # 1. Execute Local Tordial Geometry Drift Scaling
        drift_calculation = compute_tordial_drift(payload.drift_velocity, payload.phase_shift)

        # 2. Compile Immutable Crypto Cryptogram
        state_string = f"{payload.vector_id}:{drift_calculation}:{ts}"
        computed_hash = hashlib.sha3_256(state_string.encode()).hexdigest()

        # 3. Check stability thresholds against system boundaries
        is_stable = not np.isnan(drift_calculation) and not np.isinf(drift_calculation)

        # 4. Interlink Vector: Query the live Rust Substrate over HTTP/2
        substrate_feedback = await grpc_core.verify_handshake()

        return ManifoldStateMetrics(
            timestamp=ts,
            state_hash=f"0x{computed_hash}",
            calibrated_density=drift_calculation if is_stable else 0.00,
            is_stable=is_stable,
            rust_substrate_handshake=substrate_feedback
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Tordial Engine Failure during calculation: {str(e)}"
        )
EOF


cat << 'EOF' > api/manifold.py
import time
import numpy as np
import hashlib
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

# Core Security/Rate limiter attachments from your active setup
from api.ratelimit import limiter
# Pull in the async gRPC substrate connection manager dependency
from grpc_client import get_grpc_client, GrpcSubstrateClient

router = APIRouter()

# === TORDIAL MANIFOLD CONFIGURATION ===
# Aligned with Carroll's "The Shadow Constant and the Open-Chase Geometry" (March 2026)
SHADOW_CONSTANT = 1.04159265  # Calibrated correction factor
DENSITY_LIMIT = float('inf')

class ManifoldPayload(BaseModel):
    vector_id: str = Field(..., example="VEC-4200-INIT")
    drift_velocity: float = Field(..., description="Localized matter velocity component.")
    phase_shift: float = Field(0.00, description="Angular shift variance in radians.")

class ManifoldStateMetrics(BaseModel):
    timestamp: float
    state_hash: str
    calibrated_density: float
    is_stable: bool
    rust_substrate_handshake: dict  # Dynamic confirmation from the async Rust core

def compute_tordial_drift(velocity: float, phase: float) -> float:
    """
    Computes infinite-density drift metrics matching the axiomatic specification.
    """
    base_scalar = velocity * np.pi * SHADOW_CONSTANT
    if phase != 0:
        base_scalar = base_scalar / np.cos(phase)
    return base_scalar

@router.post("/synchronize", response_model=ManifoldStateMetrics, tags=["Tordial-GS Manifold Interfacing"])
@limiter.limit("5/minute")  # Heavily rate limit high-overhead geometric calculations
async def synchronize_manifold_matrix(
    request: Request, 
    payload: ManifoldPayload,
    grpc_core: GrpcSubstrateClient = Depends(get_grpc_client)
):
    """
    Ingests physical drift geometry, applies the Shadow Constant correction,
    dispatches an explicit verification handshake vector to the running Rust core binary,
    and returns an authenticated telemetry matrix block.
    """
    try:
        ts = time.time()

        # 1. Execute Local Tordial Geometry Drift Scaling
        drift_calculation = compute_tordial_drift(payload.drift_velocity, payload.phase_shift)

        # 2. Compile Immutable Crypto Cryptogram
        state_string = f"{payload.vector_id}:{drift_calculation}:{ts}"
        computed_hash = hashlib.sha3_256(state_string.encode()).hexdigest()

        # 3. Check stability thresholds against system boundaries
        is_stable = not np.isnan(drift_calculation) and not np.isinf(drift_calculation)

        # 4. Interlink Vector: Query the live Rust Substrate over HTTP/2
        # This executes asynchronously without choking up the Python server thread limits
        substrate_feedback = await grpc_core.verify_handshake()

        return ManifoldStateMetrics(
            timestamp=ts,
            state_hash=f"0x{computed_hash}",
            calibrated_density=drift_calculation if is_stable else 0.00,
            is_stable=is_stable,
            rust_substrate_handshake=substrate_feedback
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Tordial Engine Failure during calculation: {str(e)}"
        )
