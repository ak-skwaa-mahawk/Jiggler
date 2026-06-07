cat << 'EOF' > main.py
"""
main.py
Synara Telemetry Engine: Complex-Valued Cognitive Resonance Substrate.
Implements Kuramoto-style phase synchronization, attention dynamics, and geometric damping.
"""

import sqlite3
import json
import random
import threading
import time
import math
import socket
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

DB_PATH = "tordial_manifold.db"
PHI_OP = 1.65036
GEAR_SHIFT = 1.04
MAX_RING_PRESSURE_ALLOWANCE = 45.0
HEARTBEAT_INTERVAL_SEC = 2.0

# RECOGNIZED COGNITIVE MODES (Task Families)
MODES = ["SPEC_SYNTHESIS", "NUMERICAL_STABILIZATION", "IO_ARBITRATION"]

class ResonanceEngine:
    def __init__(self, port=8080):
        self.port = port
        self.is_running = True
        self.system_status = "NOMINAL"
        
        # State Plane maps: (agent_id, mode) -> {"A": amplitude, "theta": phase, "kappa": curvature}
        self.resonance_field = {}
        self.agents = ["PLANNER", "WALKER", "CRITIC"]
        
        self._bootstrap_db()
        self._initialize_resonance_field()
        
        # Start Autonomous Cognitive Dynamics solver loop
        self.dynamics_thread = threading.Thread(target=self._run_resonance_dynamics, daemon=True)
        self.dynamics_thread.start()

    def _bootstrap_db(self):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS resonance_ledger (
                agent TEXT NOT NULL,
                mode TEXT NOT NULL,
                amplitude REAL NOT NULL,
                phase REAL NOT NULL,
                curvature REAL NOT NULL,
                PRIMARY KEY (agent, mode)
            );
        """)
        conn.commit()
        conn.close()

    def _initialize_resonance_field(self):
        """Seeds the baseline cognitive modes with natural frequencies and soft entropy"""
        print("[RESONANCE INIT] Seeding Complex-Valued Resonance Domain Fields...")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        for agent in self.agents:
            for mode in MODES:
                # Distribute initial phases across the unit circle randomly
                init_phase = random.uniform(0, 2 * math.pi)
                init_amp = random.uniform(0.1, 0.5)
                init_kappa = 0.05
                
                c.execute("""INSERT OR IGNORE INTO resonance_ledger 
                    (agent, mode, amplitude, phase, curvature) 
                    VALUES (?, ?, ?, ?, ?)""", (agent, mode, init_amp, init_phase, init_kappa))
                
                self.resonance_field[(agent, mode)] = {
                    "A": init_amp, "theta": init_phase, "kappa": init_kappa,
                    "omega_0": random.uniform(0.2, 0.8) # Natural drift frequency
                }
        conn.commit()
        conn.close()

    def calculate_mode_coherence(self, mode: str) -> float:
        """Computes the Kuramoto order parameter length C(w) for a given task family"""
        sum_sin = 0.0
        sum_cos = 0.0
        count = 0
        
        for agent in self.agents:
            if (agent, mode) in self.resonance_field:
                theta = self.resonance_field[(agent, mode)]["theta"]
                sum_sin += math.sin(theta)
                sum_cos += math.cos(theta)
                count += 1
                
        if count == 0: return 0.0
        return math.sqrt(sum_sin**2 + sum_cos**2) / count

    def calculate_mode_energy(self, mode: str) -> float:
        """Computes field mode energy E(w) as the square sum of tracking attention amplitudes"""
        return sum(self.resonance_field[(a, mode)]["A"]**2 for a in self.agents if (a, mode) in self.resonance_field)

    def inject_cognitive_drive(self, agent: str, mode: str, drive_magnitude: float):
        """Allows planners or walkers to inject a real-valued torque/attention boost into a vector band"""
        agent = agent.upper()
        mode = mode.upper()
        if (agent, mode) in self.resonance_field:
            self.resonance_field[(agent, mode)]["A"] += max(0.0, drive_magnitude)
            return True
        return False

    def _step_field_dynamics(self, dt=0.5):
        """Solves the coupling phase torque updates and attention allocation constraints"""
        K_coupling = 0.4  # Core synchronization torque coefficient
        
        for mode in MODES:
            # Evaluate Invariant metrics before transforming fields
            coherence = self.calculate_mode_coherence(mode)
            energy = self.calculate_mode_energy(mode)
            
            for a in self.agents:
                f_state = self.resonance_field[(a, mode)]
                
                # Kuramoto Phase update block with curvature penalization feedback
                coupling_torque = 0.0
                for b in self.agents:
                    if a != b:
                        theta_diff = self.resonance_field[(b, mode)]["theta"] - f_state["theta"]
                        coupling_torque += K_coupling * math.sin(theta_diff)
                
                # Feedback loop: higher localized curvature slows phase adjustments down
                gs_feedback = -0.1 * f_state["kappa"] 
                f_state["theta"] = (f_state["theta"] + (f_state["omega_0"] + coupling_torque + gs_feedback) * dt) % (2 * math.pi)
                
                # Amplitude attention update: Drive vs Damping vs Cross-Mode Competition
                f_damp = 0.05 * f_state["kappa"] * f_state["A"]
                f_compete = 0.02 * sum(self.resonance_field[(a, m)]["A"] for m in MODES if m != mode)
                
                f_state["A"] = max(0.02, min(5.0, f_state["A"] - (f_damp + f_compete) * dt))
                
                # Evolve geometric curvature metric organically alongside energy lines
                f_state["kappa"] = round(0.01 * energy + 0.05 * (1.0 - coherence), 4)

        # Mirror updated memory state back down transactionally into the SQLite ledger plane
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        for (agent, mode), state in self.resonance_field.items():
            c.execute("""UPDATE resonance_ledger 
                SET amplitude = ?, phase = ?, curvature = ? 
                WHERE agent = ? AND mode = ?""", (state["A"], state["theta"], state["kappa"], agent, mode))
        conn.commit()
        conn.close()

    def _run_resonance_dynamics(self):
        """Continuous background heartbeat processing the differential field state changes"""
        while self.is_running:
            try:
                self._step_field_dynamics(dt=0.3)
            except Exception as e:
                print(f"[RESONANCE EXCEPTION] Math integration failure: {str(e)}")
            time.sleep(HEARTBEAT_INTERVAL_SEC)

matrix = ResonanceEngine()

class ResonanceGateway(BaseHTTPRequestHandler):
    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def do_GET(self):
        if self.path == "/":
            self._set_headers(200)
            self.wfile.write(json.dumps({
                "status": "ONLINE", "substrate": "TORDIAL_COGNITIVE_RESONANCE_FIELD",
                "active_modes": MODES, "monitored_agents": matrix.agents
            }).encode("utf-8"))
            return

        elif self.path == "/resonance/telemetry":
            # Formulates real-time telemetry matrix profiles containing complex amplitude and coherence states
            report = {}
            for mode in MODES:
                report[mode] = {
                    "mode_energy": round(matrix.calculate_mode_energy(mode), 4),
                    "mode_coherence": round(matrix.calculate_mode_coherence(mode), 4),
                    "agent_matrix": {a: {
                        "amplitude": round(matrix.resonance_field[(a, mode)]["A"], 4),
                        "phase_rad": round(matrix.resonance_field[(a, mode)]["theta"], 4),
                        "local_curvature": matrix.resonance_field[(a, mode)]["kappa"]
                    } for a in matrix.agents}
                }
            self._set_headers(200)
            self.wfile.write(json.dumps(report).encode("utf-8"))
            return

    def do_POST(self):
        if self.path == "/resonance/drive":
            content_length = int(self.headers['Content-Length'])
            try: data = json.loads(self.rfile.read(content_length).decode('utf-8'))
            except Exception: data = {}
            
            agent = data.get("agent", "")
            mode = data.get("mode", "")
            magnitude = float(data.get("magnitude", 0.0))
            
            if matrix.inject_cognitive_drive(agent, mode, magnitude):
                self._set_headers(200)
                self.wfile.write(json.dumps({
                    "status": "DRIVE_ENGAGED", "target_agent": agent.upper(),
                    "target_mode": mode.upper(), "boost": magnitude
                }).encode("utf-8"))
            else:
                self._set_headers(400)
                self.wfile.write(json.dumps({"status": "REJECTED", "error": "Invalid Agent/Mode pairing"}).encode("utf-8"))
            return

if __name__ == "__main__":
    server_address = ("127.0.0.1", 8080)
    httpd = HTTPServer(server_address, ResonanceGateway)
    print("[+] Tordial Resonance & Attention Core Online at http://127.0.0.1:8080")
    try: httpd.serve_forever()
    except KeyboardInterrupt:
        matrix.is_running = False
        httpd.server_close()
EOF
dos2unix main.py
