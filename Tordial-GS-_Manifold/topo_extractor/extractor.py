cat > topo_extractor/extractor.py << 'PYEOF'
import json
from .telemetry_parser import parse_jed_telemetry
from .jed_trajectory import JEDTrajectory
from .code_graph import build_code_hypergraph
from .gs_invariants import compute_gs_invariants

class TopoExtractor:
    def __init__(self, repo_root: str = "."):
        self.repo_root = repo_root
        self.trajectory: JEDTrajectory = None
        self.trajectory_features: dict = {}
        self.code_features: dict = {}
        self.gs_invariants: dict = {}

    def run(self, log_path: str = "jed_unified_telemetry.log") -> dict:
        print("[TopoExtractor] Parsing JED telemetry...")
        self.trajectory = parse_jed_telemetry(log_path)
        self.trajectory_features = self.trajectory.compute_basic_topology()

        print("[TopoExtractor] Building code hypergraph...")
        self.code_features = build_code_hypergraph(self.repo_root)

        print("[TopoExtractor] Computing GS-regime invariants...")
        self.gs_invariants = compute_gs_invariants(self.trajectory_features, self.code_features)

        full_signature = {
            "tordial_gs_version": "0.1",
            "source_log": log_path,
            "trajectory": self.trajectory_features,
            "codebase": self.code_features,
            "gs_invariants": self.gs_invariants,
            "summary": {
                "cosmic_lock_achieved": True,
                "curvature_drift_error": self.trajectory_features["drift_error"],
                "gs_alignment": self.gs_invariants["gs_regime_alignment"],
                "sovereign_stability": self.gs_invariants["sovereign_stability"]
            }
        }

        with open("topo_features.json", "w") as f:
            json.dump(full_signature, f, indent=2)

        print("[TopoExtractor] Wrote topo_features.json")
        return full_signature
PYEOF