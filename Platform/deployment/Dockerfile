# Stage 1: Build Go Binaries
FROM golang:1.22-alpine AS go-builder
WORKDIR /build
COPY modules/networkxg/soliton_node.go .
RUN go mod init networkxg && go build -o soliton_node soliton_node.go

# Stage 2: Final Runtime Environment
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies, Node.js, and process supervisors
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    npm \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python telemetry and mathematical compute requirements
RUN pip install --no-cache-dir numpy scipy rich

# Copy structural platform directories
COPY core/ ./core/
COPY ai/ ./ai/
COPY runtime/ ./runtime/
COPY modules/ ./modules/
COPY deployment/config/ ./config/

# Bring compiled Go assets forward from Stage 1
COPY --from=go-builder /build/soliton_node ./modules/networkxg/soliton_node

# Expose local environment telemetry bridge ports
EXPOSE 7979

# Set execution targeting the master control plane
ENV PYTHONPATH=/app
CMD ["python", "runtime/flame_swarm_orchestrator.py"]
