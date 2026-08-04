# synara_core/reconstruction.py — v2.2 GLM-Analogue Signal Recovery
class Chunk:
    def __init__(self, id: str, data: float, confidence: float):
        self.id = id
        self.data = data
        self.confidence = confidence
        self.reconstructed = data

def reconstruct(chunks: list[Chunk], similarity_fn, iterations: int = 5):
    """GLM-style reconstruction from noisy/scattered chunks"""
    for _ in range(iterations):
        for i, chunk in enumerate(chunks):
            if chunk.confidence > 0.8:
                continue  # high-confidence anchor

            neighbors = get_neighbors(chunks, i)
            weighted_sum = 0.0
            weight_total = 0.0

            for n in neighbors:
                weight = similarity_fn(chunk, n) * n.confidence
                weighted_sum += weight * n.reconstructed
                weight_total += weight

            if weight_total > 0:
                chunk.reconstructed = weighted_sum / weight_total
                chunk.confidence = min(1.0, chunk.confidence + 0.1)

    return chunks

def similarity_fn(a: Chunk, b: Chunk) -> float:
    """Feature distance (replace with real embedding distance if needed)"""
    return 1.0 - abs(a.data - b.data)