#!/bin/bash
# turbo_sync.sh — Bridge Tordial Manifold with Turbo_Takeoff Codebase

BASE_DIR="$HOME/Tordial-GS-_Manifold"
BUFFER_DIR="$BASE_DIR/buffer"
QUARANTINE_DIR="$BASE_DIR/quarantine"
REPO_DIR="$HOME/Turbo_Takeoff" # Assumes local clone location

echo "⚡ TURBO_TAKEOFF INTEGRATION BRIDGE INITIALIZING..."

# Action 1: Downstream Buffer Ingress Check
if [ -d "$REPO_DIR" ]; then
    echo "📁 Target Repo Directory Found at $REPO_DIR"
    mkdir -p "$REPO_DIR/ingress_payloads"
    
    STABLE_COUNT=$(ls -1 "$BUFFER_DIR"/*.json 2>/dev/null | wc -l)
    if [ "$STABLE_COUNT" -gt 0 ]; then
        echo "📦 Moving $STABLE_COUNT stable payloads to Turbo_Takeoff ingress buffer..."
        mv "$BUFFER_DIR"/*.json "$REPO_DIR/ingress_payloads/"
    else
        echo "💤 No new stable payloads waiting in buffer."
    fi
else
    echo "⚠️  [LOCAL CHECK]: Local clone of Turbo_Takeoff not found at $REPO_DIR."
    echo "   To pair, clone it locally or update REPO_DIR in this script."
fi

# Action 2: Packaging Core Code for Repository Sync
echo "🔧 Packaging Core files for commit staging..."
mkdir -p "$BASE_DIR/dist"
tar -czf "$BASE_DIR/dist/tordial_core_v1.7.0.tar.gz" \
    -C "$BASE_DIR" \
    isst_toft_core.py \
    run_pipeline.sh \
    tools/manifold_dispatcher.py \
    tools/manifold_monitor.py

echo "✅ Package written to: $BASE_DIR/dist/tordial_core_v1.7.0.tar.gz"
