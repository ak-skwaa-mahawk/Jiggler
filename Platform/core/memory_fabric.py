#!/usr/bin/env python3
# core/memory_fabric.py — Vector Similarity Fabric
import numpy as np
import time
from typing import List, Dict, Any, Tuple

class MemoryFabricStore:
    """
    A lightweight, high-performance local vector similarity memory cache.
    Uses cosine-distance computations to manage state retrieval.
    """
    def __init__(self, dimension: int = 3):
        self.dimension = dimension
        self.vectors: List[np.ndarray] = []
        self.metadata: List[Dict[str, Any]] = []

    def commit_memory(self, vector: List[float], document: str, tags: dict):
        """Stores a contextual memory embedding vector with accompanying telemetry tags."""
        np_vec = np.array(vector, dtype=np.float32)
        if np_vec.shape[0] != self.dimension:
            raise ValueError(f"Vector dimension mismatch. Expected {self.dimension}.")
        
        self.vectors.append(np_vec)
        self.metadata.append({
            "text": document,
            "tags": tags,
            "timestamp": time.time_ns()
        })

    def query_closest_context(self, query_vector: List[float], top_k: int = 1) -> List[Tuple[dict, float]]:
        """Executes a flat cosine-similarity query across the cached memory fabric."""
        if not self.vectors:
            return []

        q_vec = np.array(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm == 0:
            return []

        results = []
        for idx, stored_vec in enumerate(self.vectors):
            s_norm = np.linalg.norm(stored_vec)
            if s_norm == 0:
                continue
            
            # Standard cosine similarity formula
            similarity = float(np.dot(q_vec, stored_vec) / (q_norm * s_norm))
            results.append((self.metadata[idx], similarity))

        # Sort based on descending similarity score
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

if __name__ == "__main__":
    fabric = MemoryFabricStore(dimension=3)
    fabric.commit_memory([0.9, 0.1, 0.1], "Authorized system access loop open.", {"node": "quantum"})
    fabric.commit_memory([0.1, 0.2, 0.9], "Critical drift error detected.", {"node": "rmp"})
    
    print("--- Memory Fabric Query ---")
    match = fabric.query_closest_context([0.8, 0.1, 0.2], top_k=1)
    print(f"Closest Context Found: {match}")
