cat > topo_extractor/run_full_pipeline.py << 'PYEOF'
from topo_extractor.extractor import TopoExtractor
from topo_extractor.embedding_layer import create_manifold_embedding, embedding_to_dict
from topo_extractor.reasoning_engine import generate_report
import json
import numpy as np

if __name__ == "__main__":
    print("=== Tordial-GS Full Topological Cognition Pipeline ===\n")

    # A. Extract
    extractor = TopoExtractor(repo_root=".")
    signature = extractor.run()

    # B. Embed
    embedding = create_manifold_embedding(signature)
    with open("manifold_embedding.json", "w") as f:
        json.dump(embedding_to_dict(embedding), f, indent=2)

    # C. Reason
    report = generate_report()

    print("\n=== REASONING ENGINE OUTPUT ===")
    print(f"GS Alignment          : {report.gs_alignment}")
    print(f"Curvature Drift Error : {report.curvature_drift_error}")
    print(f"Sovereign Stability   : {report.sovereign_stability}")
    print(f"Topological Richness  : {report.topological_richness}")
    print(f"Holonomy Proxy        : {report.holonomy_proxy}")
    print(f"Overall Assessment    : {report.overall_assessment}")
    print(f"Confidence            : {report.confidence}")

    print("\n=== HOLONOMY-AWARE SUGGESTIONS ===")
    for i, sug in enumerate(report.suggestions, 1):
        print(f"\n{i}. [{sug['type'].upper()}] Priority: {sug['priority']}")
        print(f"   Suggestion : {sug['suggestion']}")
        print(f"   Code hint  : {sug['code_hint']}")
        print(f"   Expected   : {sug['expected_impact']}")
        print(f"   Confidence : {sug['confidence']}")

    print("\nFull artifacts saved:")
    print("  - topo_features.json")
    print("  - manifold_embedding.json")
    print("  - reasoning_report.json")
PYEOF