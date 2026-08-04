#!/usr/bin/env python3
# Platform/core/__init__.py — Foundational Mechanics Package Initialization

from .memory_fabric import MemoryFabricStore
from .octagonal_fpt_agent import OctagonalFPTAgent

__version__ = "1.0.0"
__all__ = [
    "MemoryFabricStore",
    "OctagonalFPTAgent"
]
