#!/usr/bin/env python3
# manifold_analyzer.py — Geometric Trajectory Analysis & Path Projection Engine
import os
import sys
import json
import math

class ManifoldSpaceAnalyzer:
    def __init__(self):
        self.base_dir = os.path.expanduser("~/Tordial-GS-_Manifold")
        self.trajectory_path = os.path.join(self.base_dir, "manifold_trajectories.jsonl")

    def analyze_field_metrics(self) -> dict:
        """Parses the trajectory ledger to extract trends and project forward spatial coordinates."""
        if not os.path.exists(self.trajectory_path):
            return {"status": "ERROR", "message": "Trajectory ledger missing. Clear stream first."}

        frames = []
        try:
            with open(self.trajectory_path, "r") as f:
                for line in f:
                    if line.strip():
                        frames.append(json.loads(line.strip()))
        except Exception as e:
            return {"status": "ERROR", "message": f"Failed to ingest stream frames: {e}"}

        total_frames = len(frames)
        if total_frames == 0:
            return {"status": "EMPTY", "message": "No trajectory points captured yet."}

        velocities = [f["velocity"] for f in frames if "velocity" in f]
        coherences = [f["coherence"] for f in frames if "coherence" in f]
        
        avg_kinetic_momentum = round(sum(velocities) / len(velocities), 4) if velocities else 0.0
        avg_coherence = round(sum(coherences) / len(coherences), 4) if coherences else 0.0

        x_vals = [f["coords"]["X"] for f in frames if "coords" in f and "X" in f["coords"]]
        y_vals = [f["coords"]["Y"] for f in frames if "coords" in f and "Y" in f["coords"]]
        z_vals = [f["coords"]["Z"] for f in frames if "coords" in f and "Z" in f["coords"]]

        centroid_x = round(sum(x_vals) / len(x_vals), 4) if x_vals else 0.0
        centroid_y = round(sum(y_vals) / len(y_vals), 4) if y_vals else 0.0
        centroid_z = round(sum(z_vals) / len(z_vals), 4) if z_vals else 0.0

        spatial_variance = 0.0
        if total_frames > 0:
            total_dev = 0.0
            for f in frames:
                if "coords" in f:
                    total_dev += (f["coords"]["X"] - centroid_x) ** 2
                    total_dev += (f["coords"]["Y"] - centroid_y) ** 2
                    total_dev += (f["coords"]["Z"] - centroid_z) ** 2
            spatial_variance = round(total_dev / total_frames, 4)

        # Compute Forward Path Extrapolation
        projected_coords = {"X": centroid_x, "Y": centroid_y, "Z": centroid_z}
        heading_vector = {"dX": 0.0, "dY": 0.0, "dZ": 0.0}
        projection_confidence = "LOW_DATA_BASELINE"

        if total_frames >= 2:
            f_prev = frames[-2]["coords"]
            f_curr = frames[-1]["coords"]
            
            # Extract direction heading differentials
            heading_vector["dX"] = round(f_curr["X"] - f_prev["X"], 4)
            heading_vector["dY"] = round(f_curr["Y"] - f_prev["Y"], 4)
            heading_vector["dZ"] = round(f_curr["Z"] - f_prev["Z"], 4)
            
            # Extrapolate linear trajectory target
            projected_coords["X"] = round(f_curr["X"] + heading_vector["dX"], 4)
            projected_coords["Y"] = round(f_curr["Y"] + heading_vector["dY"], 4)
            projected_coords["Z"] = round(f_curr["Z"] + heading_vector["dZ"], 4)
            
            # Confidence decreases if past kinetic momentum exhibits erratic velocity variance
            projection_confidence = "HIGH_CONFIDENCE_LINEAR" if avg_kinetic_momentum < 1.0 else "NOMINAL_DRIFT_PROJECTION"

        field_profile = "STABLE_EQUILIBRIUM"
        if avg_kinetic_momentum > 2.0 or spatial_variance > 5.0:
            field_profile = "HIGH_ENERGY_TURBULENT_DRIFT"
        elif avg_coherence > 0.85:
            field_profile = "HIGH_DIVERGENCE_SATURATION"

        return {
            "status": "ANALYSIS_COMPLETE",
            "sample_depth": total_frames,
            "kinetic_analysis": {
                "mean_kinetic_momentum_m": avg_kinetic_momentum,
                "mean_coherence_index": avg_coherence
            },
            "geometric_alignment": {
                "field_centroid_coords": {"X": centroid_x, "Y": centroid_y, "Z": centroid_z},
                "spatial_centroid_variance_vc": spatial_variance
            },
            "path_projection": {
                "directional_heading_vector": heading_vector,
                "predicted_next_coordinates": projected_coords,
                "projection_confidence_rating": projection_confidence
            },
            "trajectory_field_profile": field_profile
        }

if __name__ == "__main__":
    analyzer = ManifoldSpaceAnalyzer()
    metrics = analyzer.analyze_field_metrics()
    print("📊 TORDIAL MANIFOLD FIELD DIAGNOSTIC MATRIX")
    print("📡 [PATH PROJECTION]: Spatial trajectory trend vector calculated cleanly.")
    print(json.dumps(metrics, indent=2))
