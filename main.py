cat << 'EOF' > main.py
"""
main.py
Zero-Dependency Native HTTP Micro-Gateway Interface for Verifiable Tordial-GS Matrix Ledger
Includes Injection, Termination, Curvature Migration, and What-If Admission Analysis APIs
"""

import sqlite3
import json
import random
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

DB_PATH = "tordial_manifold.db"
PHI_OP = 1.65036
GEAR_SHIFT = 1.04
MAX_RING_PRESSURE_ALLOWANCE = 45.0

class MockMatrixEngine:
    def __init__(self):
        self.current_tick = 42

    def spawn_process(self, ring: str, d: int = 6, r: int = 18, drift_phase: float = 0.0):
        ring = ring.upper()
        node_id = random.randint(100, 999)
        d = max(4, min(42, d))
        r = max(12, min(500, r))
        denom = 4.0 * PHI_OP * GEAR_SHIFT + 0.08 * drift_phase
        sigma_T = r - (d ** 2 / denom)
        
        node_obj = type('Node', (), {"node_id": node_id, "d": d, "r": r, "sigma_T": sigma_T, "drift_phase": drift_phase})()
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""INSERT INTO nodes 
            (node_id, ring, d, r, sigma_T, drift_phase, fission_count, parent_id) 
            VALUES (?,?,?,?,?,?,0,NULL)""", (node_id, f"Injected_{ring}", d, r, sigma_T, drift_phase))
        conn.commit()
        conn.close()
        return node_obj

    def audit_admission(self, node_id: int, target_ring: str):
        """Dry-run calculation matrix to isolate metric shifts before table writes occur"""
        target_ring = target_ring.upper()
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("SELECT sigma_T FROM nodes WHERE node_id = ?", (node_id,))
        source_node = c.fetchone()
        if not source_node:
            conn.close()
            return None

        c.execute("""
            SELECT COUNT(*) as node_count, 
                   COALESCE(SUM(sigma_T), 0.0) as cumulative_pressure,
                   COALESCE(AVG(sigma_T), 0.0) as current_avg
            FROM nodes WHERE ring = ?;
        """, (f"Injected_{target_ring}",))
        dest_stats = c.fetchone()
        
        projected_count = dest_stats["node_count"] + 1
        projected_pressure = dest_stats["cumulative_pressure"] + source_node["sigma_T"]
        projected_average = projected_pressure / projected_count
        conn.close()

        evaluation = "ALLOWED" if projected_average <= MAX_RING_PRESSURE_ALLOWANCE else "REJECTED_PRESSURE_OVERFLOW"
        
        return {
            "evaluation": evaluation,
            "node_id": node_id,
            "target_ring": target_ring,
            "impact": {
                "node_tensor_pressure": round(source_node["sigma_T"], 4),
                "current_ring_average": round(dest_stats["current_avg"], 4),
                "projected_ring_average": round(projected_average, 4),
                "safety_ceiling": MAX_RING_PRESSURE_ALLOWANCE
            }
        }

    def migrate_process(self, node_id: int, target_ring: str):
        target_ring = target_ring.upper()
        audit = self.audit_admission(node_id, target_ring)
        if not audit:
            return {"status": "NOT_FOUND"}
        if audit["evaluation"] == "REJECTED_PRESSURE_OVERFLOW":
            return {"status": "VIOLATION", "projected_pressure": audit["impact"]["projected_ring_average"], "ceiling": MAX_RING_PRESSURE_ALLOWANCE}
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE nodes SET ring = ? WHERE node_id = ?", (f"Injected_{target_ring}", node_id))
        conn.commit()
        
        c.execute("SELECT d, r, sigma_T, drift_phase FROM nodes WHERE node_id = ?", (node_id,))
        conn.row_factory = sqlite3.Row
        node_state = dict(conn.cursor().fetchone())
        conn.close()
        return {"status": "SUCCESS", "data": node_state}

    def terminate_process(self, node_id: int) -> bool:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM nodes WHERE node_id = ?", (node_id,))
        exists = c.fetchone()[0] > 0
        if exists:
            c.execute("DELETE FROM nodes WHERE node_id = ?", (node_id,))
            conn.commit()
        conn.close()
        return exists

matrix = MockMatrixEngine()

class NativeLedgerGateway(BaseHTTPRequestHandler):
    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def do_GET(self):
        parsed_url = urlparse(self.path)
        
        if parsed_url.path == "/":
            self._set_headers(200)
            self.wfile.write(json.dumps({"status": "ONLINE", "substrate": "Bounded Geometry Spec"}).encode("utf-8"))
            return

        # NEW Predictor Endpoint: /kernel/admission?node_id=N&target_ring=R
        elif parsed_url.path == "/kernel/admission":
            query_params = parse_qs(parsed_url.query)
            try:
                node_id = int(query_params.get("node_id", [0])[0])
                target_ring = query_params.get("target_ring", ["C"])[0].upper()
                
                audit_report = matrix.audit_admission(node_id, target_ring)
                if not audit_report:
                    self._set_headers(404)
                    self.wfile.write(json.dumps({"error": "Node ID signature not tracked in ledger"}).encode("utf-8"))
                    return
                
                status_code = 200 if audit_report["evaluation"] == "ALLOWED" else 403
                self._set_headers(status_code)
                self.wfile.write(json.dumps(audit_report).encode("utf-8"))
            except Exception as e:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        elif parsed_url.path == "/manifold/telemetry":
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT ring, COUNT(*) as recorded_ticks, AVG(sigma_T) as mean_tensor_pressure FROM nodes GROUP BY ring;")
            rows = c.fetchall()
            conn.close()
            self._set_headers(200)
            payload = {"rings": {row["ring"]: {"datapoints": row["recorded_ticks"], "avg_pressure": round(row["mean_tensor_pressure"], 4)} for row in rows}}
            self.wfile.write(json.dumps(payload).encode("utf-8"))
            return

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        try: data = json.loads(body.decode('utf-8'))
        except Exception: data = {}

        if self.path == "/process/spawn":
            ring = data.get("ring", "A")
            node = matrix.spawn_process(ring, data.get("d", 6), data.get("r", 18), data.get("drift_phase", 0.0))
            self._set_headers(201)
            self.wfile.write(json.dumps({"status": "SPAWNED", "node_id": node.node_id, "ring": ring.upper(), "initial_state": {"d": node.d, "r": node.r, "sigma_T": round(node.sigma_T, 4), "drift_phase": node.drift_phase}}).encode("utf-8"))
            return

        elif self.path.startswith("/process/migrate/"):
            node_id = int(self.path.split("/")[-1])
            target_ring = data.get("target_ring", "C")
            result = matrix.migrate_process(node_id, target_ring)
            if result["status"] == "SUCCESS":
                self._set_headers(200)
                self.wfile.write(json.dumps({"status": "MIGRATED", "node_id": node_id, "to_ring": f"Injected_{target_ring.upper()}", "state": result["data"]}).encode("utf-8"))
            elif result["status"] == "VIOLATION":
                self._set_headers(403)
                self.wfile.write(json.dumps({"status": "REJECTED_PRESSURE_OVERFLOW", "detail": f"Target ring stabilization breached. Projected: {result['projected_pressure']} (Max allowed: {result['ceiling']})"}).encode("utf-8"))
            else:
                self._set_headers(404)
                self.wfile.write(json.dumps({"status": "NOT_FOUND"})).encode("utf-8"))
            return

    def do_DELETE(self):
        if self.path.startswith("/process/terminate/"):
            node_id = int(self.path.split("/")[-1])
            if matrix.terminate_process(node_id):
                self._set_headers(200)
                self.wfile.write(json.dumps({"status": "TERMINATED", "target_node_id": node_id}).encode("utf-8"))
            else:
                self._set_headers(404)
                self.wfile.write(json.dumps({"status": "NOT_FOUND"}).encode("utf-8"))
            return

if __name__ == "__main__":
    server_address = ("127.0.0.1", 8080)
    httpd = HTTPServer(server_address, NativeLedgerGateway)
    print("[+] Sovereign Micro-Kernel REST Core Engine Online with Analysis Tools at http://127.0.0.1:8080")
    try: httpd.serve_forever()
    except KeyboardInterrupt: httpd.server_close()
EOF
dos2unix main.py
