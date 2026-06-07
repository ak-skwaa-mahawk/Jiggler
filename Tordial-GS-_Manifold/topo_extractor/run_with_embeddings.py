cat > topo_extractor/run_with_embeddings.py << 'PYEOF'
from topo_extractor.extractor import TopoExtractor
from topo_extractor.embedding_layer import create_manifold_embedding, embedding_to_dict
import json

if __name__ == "__main__":
    print("=== Tordial-GS Full Topological Pipeline ===")
    extractor = TopoExtractor(repo_root=".")
    signature = extractor.run()                    # produces topo_features.json

    print("\n[Embedding Layer] Creating manifold-aligned embeddings...")
    embedding = create_manifold_embedding(signature)
    emb_dict = embedding_to_dict(embedding)

    with open("manifold_embedding.json", "w") as f:
        json.dump(emb_dict, f, indent=2)

    print("Saved manifold_embedding.json")
    print("\nToroidal angles (θ1–θ4):", np.round(embedding.toroidal_angles, 4))
    print("GS alignment score     :", embedding.metadata["gs_alignment"])
    print("Sovereign stability    :", embedding.metadata["sovereign_stability"])
PYEOF