#!/usr/bin/env python3
# Platform/ai/__init__.py — Intelligent Layer Package Initialization

from .llm_bridge import LocalLLMBridge
from .policy_governance.evaluator import SovereignPolicyGuard

__version__ = "1.0.0"
__all__ = [
    "LocalLLMBridge",
    "SovereignPolicyGuard"
]
