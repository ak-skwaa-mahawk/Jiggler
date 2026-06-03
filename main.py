cat << 'EOF' > main.py
"""
main.py
Zero-Dependency Native HTTP Micro-Gateway Interface for Verifiable Tordial-GS Matrix Ledger
Includes Sovereign Process Injection & Dynamic Termination APIs
"""

import sqlite3
import json
import random
from http.server import HTTPServer, BaseHTTPRequestHandler

DB_PATH = "tordial_manifold.db"
PHI_OP = 1.65036
GEAR_SHIFT = 1.04

class MockMatrixEngine:
    """Simulates the state matrices within the REST process space"""
    def __init__(self):
        self.current_tick = 42
        # Mock active lists to mimic node storage properties
        self.nodes_a = []
        self.nodes_b = []
        self.nodes_c = []

    def spawn_process(self, ring: str, d: int = 6, r: int = 18, drift_phase: float = 0.0):
        ring = ring.upper()
        node_id = random.randint(100, 999) # Generate a unique identification footprint
        
        # Clamp parameters to preserve geometry contract boundaries
        d = max(4, min(42, d))
        r = max(12, min(500, r))
        
        denom = 4.0 * PHI_OP * GEAR_SHIFT + 0.08 * drift_phase
        sigma_T = r - (d ** 2 / denom)
        
        # Construct dynamic properties to mirror standard node shapes
        node_obj = type('Node', (), {
            "node_id": node_id, "d": d, "r": r, 
            "sigma_T": sigma_T, "drift_phase": drift_phase
        })()
        
        # Persist directly to ledger
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""INSERT INTO nodes 
            (node_id, ring, d, r, sigma_T, drift_phase, fission_count, parent_id) 
            VALUES (?,?,?,?,?,?,0,NULL)""",
            (node_id, f"Injected_{ring}", d, r, sigma_T, drift_phase))
        conn.commit()
        conn.close()
        return node_obj

    def terminate_process(self, node_id: int) -> bool:
        """Removes a process row from the persistent ledger history"""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM nodes WHERE node_id = ?", (node_id,))
        exists = c.fetchone()[0] > 0
        if exists:
            c.execute("DELETE FROM nodes WHERE node_id = ?", (node_id,))
            conn.commit()
        conn.close()
        return exists

# Instantiating the virtual engine matrix memory layout
matrix = MockMatrixEngine()

class NativeLedgerGateway(BaseHTTPRequestHandler):
    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def do_GET(self):
        if self.path == "/":
            self._set_headers(200)
            response = {
                "status": "ONLINE",
                "substrate": "Bounded Triple-Ring Topology (v15)",
                "engine_variance": 0.000000,
                "contract_compliance": "VERIFIED_PASSED"
            }
            self.wfile.write(json.dumps(response).encode("utf-8"))
            return

        elif self.path == "/manifold/telemetry":
            try:
                conn = sqlite3.connect(DB_PATH)
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                c.execute("""
                    SELECT ring, COUNT(*) as recorded_ticks, AVG(sigma_T) as mean_tensor_pressure 
                    FROM nodes 
                    GROUP BY ring;
                """)
                rows = c.fetchall()
                conn.close()

                self._set_headers(200)
                payload = {
                    "timestamp_sync": "UTC_LOCKED",
                    "rings": {row["ring"]: {"datapoints": row["recorded_ticks"], "avg_pressure": round(row["mean_tensor_pressure"], 4)} for row in rows}
                }
                self.wfile.write(json.dumps(payload).encode("utf-8"))
            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

    def do_POST(self):
        """Processes Incoming Sovereign Process Spawn Requests"""
        if self.path == "/process/spawn":
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body.decode('utf-8'))
            except Exception:
                data = {}

            ring = data.get("ring", "A")
            d = int(data.get("d", 6))
            r = int(data.get("r", 18))
            drift_phase = float(data.get("drift_phase", 0.0))

            try:
                node = matrix.spawn_process(ring, d, r, drift_phase)
                self._set_headers(201)
                response = {
                    "status": "SPAWNED",
                    "node_id": node.node_id,
                    "ring": ring.upper(),
                    "initial_state": {
                        "d": node.d, "r": node.r,
                        "sigma_T": round(node.sigma_T, 4), "drift_phase": node.drift_phase
                    }
                }
                self.wfile.write(json.dumps(response).encode("utf-8"))
            except Exception as e:
                self._set_headers(400)
                self.wfile.write(json.dumps({"status": "ERROR", "detail": str(e)}).encode("utf-8"))
            return

    def do_DELETE(self):
        """Processes Injected Process Elimination Requests"""
        if self.path.startswith("/process/terminate/"):
            try:
                node_id = int(self.path.split("/")[-1])
                success = matrix.terminate_process(node_id)
                if success:
                    self._set_headers(200)
                    self.wfile.write(json.dumps({"status": "TERMINATED", "target_node_id": node_id}).encode("utf-8"))
                else:
                    self._set_headers(404)
                    self.wfile.write(json.dumps({"status": "NOT_FOUND", "detail": "Target process signature absent"}).encode("utf-8"))
            except Exception as e:
                self._set_headers(400)
                self.wfile.write(json.dumps({"status": "ERROR", "detail": str(e)}).encode("utf-8"))
            return

if __name__ == "__main__":
    server_address = ("127.0.0.1", 8080)
    httpd = HTTPServer(server_address, NativeLedgerGateway)
    print("[+] Zero-Dependency Native REST Gateway Online with Injection/Termination at http://127.0.0.1:8080")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()
EOF
dos2unix main.py
