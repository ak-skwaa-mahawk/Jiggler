"""
Peer-to-Peer Reciprocal Soliton Exchange (PRSE)
Academic Reference Protocol & Graph Soliton Transport Module
"""

import math
import time
import json
import urllib.request
import numpy as np

class PeerReciprocalSolitonExchange:
    def __init__(self, node_count: int = 64, carrier_freq: float = 79.79):
        self.node_count = node_count
        self.carrier_freq = carrier_freq
        self.dt = 0.001
        self.state = np.zeros(node_count, dtype=float)
        
    def inject_pulse(self, origin: int, amplitude: float = 1.0):
        x = np.arange(self.node_count)
        width = math.sqrt(amplitude / 6.0) if amplitude > 0 else 1.0
        self.state += amplitude / (np.cosh(width * (x - origin)) ** 2)

    def propagate_step(self, steps: int = 100):
        for _ in range(steps):
            d2 = np.roll(self.state, -1) - 2.0 * self.state + np.roll(self.state, 1)
            flux = -0.1 * (self.state ** 2) * self.dt
            self.state += 0.5 * d2 * self.dt + flux

    def compute_invariants(self):
        energy = float(np.sum(self.state ** 2))
        mass = float(np.sum(self.state))
        return energy, mass

    def log_telemetry_to_mlflow(self, energy: float, mass: float):
        try:
            url = "http://127.0.0.1:5000/api/2.0/mlflow/runs/create"
            payload = {
                "experiment_id": "0",
                "start_time": int(time.time() * 1000),
                "tags": [
                    {"key": "protocol", "value": "PRSE_v1"},
                    {"key": "carrier_freq_hz", "value": str(self.carrier_freq)}
                ]
            }
            req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
            res = json.loads(urllib.request.urlopen(req).read().decode())
            run_id = res["run"]["info"]["run_id"]

            metric_url = "http://127.0.0.1:5000/api/2.0/mlflow/runs/log-metric"
            for k, v in [("prse_energy", energy), ("prse_mass", mass), ("carrier_frequency", self.carrier_freq)]:
                m_req = urllib.request.Request(
                    metric_url,
                    data=json.dumps({"run_id": run_id, "key": k, "value": v, "timestamp": int(time.time() * 1000), "step": 100}).encode(),
                    headers={"Content-Type": "application/json"}
                )
                urllib.request.urlopen(m_req)

            urllib.request.urlopen(urllib.request.Request(
                "http://127.0.0.1:5000/api/2.0/mlflow/runs/update",
                data=json.dumps({"run_id": run_id, "status": "FINISHED", "end_time": int(time.time() * 1000)}).encode(),
                headers={"Content-Type": "application/json"}
            ))
            print(f"PRSE Telemetry Logged to MLflow [Run ID: {run_id}]")
        except Exception as e:
            print(f"MLflow logging bypassed: {e}")

if __name__ == "__main__":
    prse = PeerReciprocalSolitonExchange(node_count=64)
    prse.inject_pulse(origin=16, amplitude=1.5)
    prse.inject_pulse(origin=48, amplitude=1.0)
    prse.propagate_step(steps=200)
    e, m = prse.compute_invariants()
    print(f"PRSE Simulation Completed | Energy: {e:.6f} | Mass: {m:.6f}")
    prse.log_telemetry_to_mlflow(e, m)
