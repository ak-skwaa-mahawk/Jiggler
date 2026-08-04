# generate_regime_gain_landscape.py

import json

def export_landscape_data(log_entries, out_path="landscape.json"):
    points = []
    for entry in log_entries:
        x = {"SUBCRITICAL": 0, "EDGE_GS": 1, "DEEP_GS": 2}[entry["regime"]]
        y = entry["pid_index"]  # or PCA(kp,ki,kd)
        z = entry["reward"]
        color = entry["stability"]  # or safety/performance

        points.append({
            "x": x,
            "y": y,
            "z": z,
            "color": color,
            "regime": entry["regime"],
            "kp": entry["kp"],
            "ki": entry["ki"],
            "kd": entry["kd"],
        })

    with open(out_path, "w") as f:
        json.dump({"points": points}, f, indent=2)