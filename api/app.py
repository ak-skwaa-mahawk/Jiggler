cat << 'EOF' > api/app.py
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Pipeline Route Modulators & Geometric Infrastructure Ingress Ports
from api.arc import router as arc_router
from api.tunnel import router as tunnel_router
from api.manifold import router as manifold_router

# Core Rate Limiting & Security Governance Substrates
from api.ratelimit import limiter, rate_limit_handler, RateLimitExceeded

# Import our new gRPC substrate toolchain
from grpc_client import get_grpc_client

# ==========================================
# 0. LIFECYCLE MANAGEMENT (gRPC Interlink)
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize the channel pool connection to Rust core
    grpc_core = get_grpc_client()
    print("[🔌] FastAPI Lifecycle: HTTP/2 lane opened to Rust substrate.")
    status = await grpc_core.verify_handshake()
    print(f"[🛰️] Substrate Verification Status: {status['status']}")
    yield
    # Shutdown: Cleanly unwind the socket channel parameters
    await grpc_core.close()
    print("[💤] FastAPI Lifecycle: HTTP/2 channel pool securely disconnected.")

# Single Consolidated Application Lifecycle Instantiation
app = FastAPI(
    title="Resonance Mesh API",
    version="1.0.0",
    description="Sovereign telemetry mesh coordinating localized hardware nodes, tunnels, and policy controls.",
    lifespan=lifespan
)

# Attach SlowAPI State Registry & Exception Handlers
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware) if 'SlowAPIMiddleware' in globals() else None
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

PRODUCTION_ORIGINS = [
    "https://sites.google.com",
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "http://localhost:8000",
    "http://127.0.0.1:8000"
]

ALLOW_ALL = os.getenv("ENV_MODE", "development") == "development"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if ALLOW_ALL else PRODUCTION_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.get("/health", tags=["Telemetry Sensors"])
async def health_check():
    """Empirical trace sensor monitoring baseline stack status."""
    grpc_core = get_grpc_client()
    substrate_check = await grpc_core.verify_handshake()
    return {
        "ok": True,
        "service": "resonance-mesh",
        "governance_membrane": "ACTIVE",
        "rust_substrate_link": substrate_check
    }

app.include_router(arc_router, prefix="/arc", tags=["Arc Core Logic Layers"])
app.include_router(tunnel_router, prefix="/tunnel", tags=["Dynamic Network Tunneling Channels"])
app.include_router(manifold_router, prefix="/manifold", tags=["Tordial Infinite-Density Drift Controller"])
EOF


cat << 'EOF' > api/app.py
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Pipeline Route Modulators & Geometric Infrastructure Ingress Ports
from api.arc import router as arc_router
from api.tunnel import router as tunnel_router
from api.manifold import router as manifold_router

# Core Rate Limiting & Security Governance Substrates
from slowapi.middleware import SlowAPIMiddleware
from api.ratelimit import limiter, rate_limit_handler, RateLimitExceeded

# Import our new gRPC substrate toolchain
from grpc_client import get_grpc_client

# ==========================================
# 0. LIFECYCLE MANAGEMENT (gRPC Interlink)
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize the channel pool connection to Rust core
    grpc_core = get_grpc_client()
    print("[🔌] FastAPI Lifecycle: HTTP/2 lane opened to Rust substrate.")
    # Run a quick check-in log during boot
    status = await grpc_core.verify_handshake()
    print(f"[🛰️] Substrate Verification Status: {status['status']}")
    
    yield
    
    # Shutdown: Cleanly unwind the socket channel parameters
    await grpc_core.close()
    print("[💤] FastAPI Lifecycle: HTTP/2 channel pool securely disconnected.")

# Single Consolidated Application Lifecycle Instantiation
app = FastAPI(
    title="Resonance Mesh API",
    version="1.0.0",
    description="Sovereign telemetry mesh coordinating localized hardware nodes, tunnels, and policy controls.",
    lifespan=lifespan
)

# ==========================================
# 1. SECURITY & TRAFFIC GOVERNANCE MEMBERS
# ==========================================
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

PRODUCTION_ORIGINS = [
    "https://sites.google.com",
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "http://localhost:8000",
    "http://127.0.0.1:8000"
]

ALLOW_ALL = os.getenv("ENV_MODE", "development") == "development"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if ALLOW_ALL else PRODUCTION_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ==========================================
# 2. TELEMETRY SENSORS & HEALTH MONITORS
# ==========================================
@app.get("/health", tags=["Telemetry Sensors"])
async def health_check():
    """
    Empirical trace sensor monitoring baseline stack status and Rust core visibility.
    """
    grpc_core = get_grpc_client()
    substrate_check = await grpc_core.verify_handshake()
    
    return {
        "ok": True,
        "service": "resonance-mesh",
        "governance_membrane": "ACTIVE",
        "rate_limiting": "ENFORCED",
        "rust_substrate_link": substrate_check
    }

# ==========================================
# 3. PIPELINE GATEWAY ROUTER MOUNTING
# ==========================================
app.include_router(arc_router, prefix="/arc", tags=["Arc Core Logic Layers"])
app.include_router(tunnel_router, prefix="/tunnel", tags=["Dynamic Network Tunneling Channels"])
app.include_router(manifold_router, prefix="/manifold", tags=["Tordial Infinite-Density Drift Controller"])
EOF
