cat > topo_extractor/__init__.py << 'PYEOF'
"""Tordial-GS Topological Feature Extractor v0.1
Aligned to TR≈3.173, GS-regime algebra, toroidal geometry, and sovereign invariants.
"""
from .extractor import TopoExtractor
__all__ = ["TopoExtractor"]
PYEOF