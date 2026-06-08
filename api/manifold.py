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
