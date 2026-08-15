# ==============================================================================
# Multi-Arch OCI Container: Tordial Routing Protocol (TRP) Control Plane
# Supported Platforms: linux/amd64, linux/arm64/v8
# ==============================================================================

FROM python:3.11-slim-bookworm AS runtime

LABEL org.opencontainers.image.title="Tordial Routing Protocol (TRP)" \
      org.opencontainers.image.description="Sovereign Geometric Edge Router & 79Hz Control Plane" \
      org.opencontainers.image.version="v9.0-FINAL" \
      org.opencontainers.image.licenses="MIT"

# Set non-interactive install and UTF-8 locale
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    HEADLESS=1 \
    TORDIAL_STATE_DIR=/var/lib/tordial

# Install low-level networking primitives & runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    iproute2 \
    iptables \
    wireguard-tools \
    curl \
    procps \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency requirements
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy source modules and tools
COPY src/ /app/src/
COPY tools/ /app/tools/
COPY state_attestation.json /app/state_attestation.json
COPY tordial_gs.db /app/tordial_gs.db

# Create persistent state directory and link database paths
RUN mkdir -p /var/lib/tordial && \
    touch /var/lib/tordial/tordial_routed.db && \
    ln -sf /var/lib/tordial/tordial_routed.db /app/tordial_routed.db

# Volume mount point for ledger persistence
VOLUME ["/var/lib/tordial"]

# Default entrypoint runs the 79Hz TRP control plane
ENTRYPOINT ["python3", "tools/tordial_routed.py"]
