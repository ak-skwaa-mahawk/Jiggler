{
  "inference_engine_topology": "CLOUD_FEDERATED_MESH",
  "global_timing_budget_ms": 12.65,
  "engines": {
    "cloud_vllm_endpoint": {
      "base_url": "https://your-allocated-cloud-vllm-node/v1",
      "api_key": "sk-vllm-cloud-orchestration-token",
      "timeout_seconds": 0.045
    }
  },
  "agent_model_mapping": {
    "trajectory_agent": {
      "engine": "cloud_vllm_endpoint",
      "model": "deepseek-coder-1.3b-instruct",
      "execution_priority": "CRITICAL_PATH",
      "parameters": {
        "max_tokens": 16,
        "temperature": 0.0,
        "gpu_memory_utilization": 0.25
      }
    },
    "governance_agent": {
      "engine": "cloud_vllm_endpoint",
      "model": "qwen2.5-1.5b-instruct",
      "execution_priority": "INTERCEPTOR",
      "parameters": {
        "max_tokens": 32,
        "temperature": 0.0
      }
    }
  },
  "network_tuning": {
    "tcp_nodelay": true,
    "keep_alive_ms": 5000,
    "max_pooled_connections": 50
  }
}
