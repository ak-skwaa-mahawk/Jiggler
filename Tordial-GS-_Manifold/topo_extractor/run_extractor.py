cat > topo_extractor/run_extractor.py << 'PYEOF'
from topo_extractor.extractor import TopoExtractor

if __name__ == "__main__":
    extractor = TopoExtractor(repo_root=".")
    result = extractor.run()
    print("\n=== TOPOLOGICAL SIGNATURE ===")
    print(f"GS-regime alignment : {result['gs_invariants']['gs_regime_alignment']}")
    print(f"Curvature drift err : {result['trajectory']['drift_error']}")
    print(f"Sovereign stability : {result['gs_invariants']['sovereign_stability']}")
    print(f"Topological richness: {result['gs_invariants']['topological_richness']}")
    print(f"Full output saved to: topo_features.json")
PYEOF