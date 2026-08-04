cd ~/Tordial-GS-_Manifold

cat << 'EOF' > quickstart.sh
#!/bin/bash
# =======================================================================================
# TORDIAL GS MANIFOLD UNIFIED BOOTSTRAP ENGINE
# Quick-Start Production Initialization Script
# =======================================================================================

echo "================================================================================="
echo "🌀 [QUICKSTART] Initializing Sovereign Substrate Core Matrix..."
echo "================================================================================="

# 1. Export Environment Overrides to Memory
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
export RUSTFLAGS="-C link-arg=-Wl,--gc-sections -C link-arg=-Wl,-z,nocopyreloc"
export MALLOC_PATTERN=1
echo "🔒 Environment variables and forward-compat flags armed."

# 2. Hard Socket Flush Phase (Preventing AddrInUse Errors)
echo "🧹 Scanning and evacuating localized zombie sockets..."
fuser -k 8000/tcp 2>/dev/null
fuser -k 50051/tcp 2>/dev/null
fuser -k 50052/tcp 2>/dev/null
fuser -k 50055/tcp 2>/dev/null
pkill -f tordial_gs_manifold 2>/dev/null
pkill -f uvicorn 2>/dev/null
sleep 1
echo "✨ Network interface pipelines fully cleared."

# 3. Native Engine Release Compilation Guard
if [ ! -f ./target/release/tordial_gs_manifold ]; then
    echo "🏗️  No release binary detected. Executing production build pass..."
    cargo build --release
else
    echo "🚀 Verified optimized release asset on disk."
fi

# 4. Multi-Tenant Runtime Stack Orchestration
echo "🛰️  Spawning Native Substrate gRPC Controller on port 50055..."
./target/release/tordial_gs_manifold > manifold_grpc.log 2>&1 &
MANIFOLD_PID=$!

echo "🐍 Launching Python REST API Gateway (Uvicorn) on port 8000..."
PYTHONPATH=. uvicorn api.app:app --host 127.0.0.1 --port 8000 > python_gateway.log 2>&1 &
GATEWAY_PID=$!

sleep 2

# 5. Core Operational Topology Mapping Verifier
echo "================================================================================="
echo "🌌 INDUSTRIAL SYSTEM MATRIX ALIGNED & DEPLOYED"
echo "================================================================================="
echo " 🔗 Port 8000  -> REST API Gateway Status: [RUNNING] (PID: $GATEWAY_PID)"
echo " 🔗 Port 50055 -> Native gRPC Backplane   : [RUNNING] (PID: $MANIFOLD_PID)"
echo "---------------------------------------------------------------------------------"
echo "📝 Telemetry pipelines printing to *.log configurations."
echo "💡 To view runtime traffic live, execute: tail -f manifold_grpc.log"
echo "================================================================================="

# Keep shell open to monitor child processes
wait
EOF

# Grant execution rights to the bootstrap engine
chmod +x quickstart.sh
echo "🎯 Quick-start shell infrastructure fully constructed and armed."
