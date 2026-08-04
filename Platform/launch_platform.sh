#!/usr/bin/env bash
set -euo pipefail

# --- Config ---
ENGINE="${1:-ollama}"   # or: vllm
VENV_DIR="venv"

echo "[Launcher] Arming environment..."

# 1) Python venv
if [ ! -d "$VENV_DIR" ]; then
  echo "[Launcher] Missing venv. Create it first via setup guide."
  exit 1
fi
source "$VENV_DIR/bin/activate"

# 2) Start LLM engine (background)
if [ "$ENGINE" = "ollama" ]; then
  echo "[Launcher] Assuming Ollama daemon already running on :11434"
elif [ "$ENGINE" = "vllm" ]; then
  echo "[Launcher] Starting vLLM server..."
  python3 -m vllm.entrypoints.openai.api_server \
    --model neural-marvin-7b \
    --port 8000 \
    --api-key sk-vllm-local-orchestration-token \
    > logs/vllm.log 2>&1 &
fi

# 3) Start Node.js concurrency coordinator
echo "[Launcher] Starting Node.js concurrency mesh..."
pushd nodes/concurrency_coordinator > /dev/null
node index.js > ../../logs/node_mesh.log 2>&1 &
popd > /dev/null

# 4) Start Go wave processor
echo "[Launcher] Starting Go wave processor..."
pushd nodes/wave_processor > /dev/null
./wave_processor_srv > ../../logs/wave_processor.log 2>&1 &
popd > /dev/null

# 5) Start Python orchestrator
echo "[Launcher] Starting Flame Swarm Orchestrator..."
python3 flame_swarm_orchestrator.py \
  --config policy_governance/boundary_rules.json \
  --models core/config/model_routing.json \
  --verbose