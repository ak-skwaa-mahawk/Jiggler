import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Pipeline Route Modulators & Geometric Infrastructure Ingress Ports
from api.arc import router as arc_router
from api.tunnel import router as tunnel_router
from api.manifold import router as manifold_router

# Core Rate Limiting & Security Governance Substrates
from slowapi.middleware import SlowAPIMiddleware
from api.ratelimit import limiter, rate_limit_handler, RateLimitExceeded

# Single Consolidated Application Lifecycle Instantiation
app = FastAPI(
    title="Resonance Mesh API",
    version="1.0.0",
    description="Sovereign telemetry mesh coordinating localized hardware nodes, tunnels, and policy controls."
)

# ==========================================
# 1. SECURITY & TRAFFIC GOVERNANCE MEMBERS
# ==========================================

# Attach SlowAPI State Registry & Exception Handlers
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# Allowed Cross-Origin Ingress Footprints (Vital for Google Sites Canvas Embeds)
PRODUCTION_ORIGINS = [
    "https://sites.google.com",
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "http://localhost:8000",
    "http://127.0.0.1:8000"
]

# Toggle dynamic open-cors fallback based on target runtime environment
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
def health_check():
    """
    Empirical trace sensor monitoring baseline stack status.
    """
    return {
        "ok": True,
        "service": "resonance-mesh",
        "governance_membrane": "ACTIVE",
        "rate_limiting": "ENFORCED"
    }

# ==========================================
# 3. PIPELINE GATEWAY ROUTER MOUNTING
# ==========================================

# Mount the localized Arc configuration control vectors
app.include_router(
    arc_router,
    prefix="/arc",
    tags=["Arc Core Logic Layers"]
)

# Mount the automated hardware communication and dynamic tunneling pathways
app.include_router(
    tunnel_router,
    prefix="/tunnel",
    tags=["Dynamic Network Tunneling Channels"]
)

# Mount the dynamic Tordial Infinite-Density Drift Controller matrix calculations
app.include_router(
    manifold_router,
    prefix="/manifold",
    tags=["Tordial Infinite-Density Drift Controller"]
)
