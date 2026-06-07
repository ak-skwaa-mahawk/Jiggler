cat > topo_extractor/code_graph.py << 'PYEOF'
import os
import ast
from collections import defaultdict
from typing import Dict, List, Tuple

def build_code_hypergraph(root_dir: str = ".") -> Dict:
    """Builds a simple hypergraph from Python files (extendable to Rust/Dart)."""
    modules = []
    edges = []
    functions = set()

    for dirpath, _, filenames in os.walk(root_dir):
        for fname in filenames:
            if fname.endswith(".py") and "topo_extractor" not in dirpath:
                fpath = os.path.join(dirpath, fname)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        tree = ast.parse(f.read(), filename=fpath)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            func_name = f"{fname}:{node.name}"
                            functions.add(func_name)
                            # Simple call detection
                            for child in ast.walk(node):
                                if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                                    edges.append((func_name, f"call:{child.func.id}"))
                except Exception:
                    continue

    # Basic topological stats
    n_nodes = len(functions)
    n_edges = len(edges)
    # Proxy for connected components and cycles
    betti0_proxy = max(1, n_nodes - n_edges // 2)
    betti1_proxy = max(0, n_edges - n_nodes + 1)  # rough cycle count

    return {
        "python_files_scanned": len([f for f in os.listdir(root_dir) if f.endswith(".py")]),
        "functions_detected": n_nodes,
        "call_edges": n_edges,
        "betti0_proxy": betti0_proxy,
        "betti1_proxy": betti1_proxy,
        "hypergraph_density": round(n_edges / max(n_nodes, 1), 4)
    }
PYEOF