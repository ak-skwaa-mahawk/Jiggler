cat << 'EOF' > main.py
"""
main.py
Zero-Dependency Native HTTP Micro-Gateway Interface for Verifiable Tordial-GS Matrix Ledger
Features an Autonomous Background Heartbeat Daemon with Anti-Thrashing Hysteresis Damping
"""

import sqlite3
import json
import random
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

DB_PATH = "tordial_manifold.db"
PHI_OP = 1.65036
GEAR_SHIFT = 1.04
MAX_RING_PRESSURE_ALLOWANCE = 45.0
HEARTBEAT_INTERVAL_SEC = 3.0

class MockMatrixEngine:
    def __init__(self):
        self.current_tick = 42
        self._bootstrap_db()
        self.is_running = True
        self.heartbeat_thread = threading.Thread(target=self._run_heartbeat, daemon=True)
        self.heartbeat_thread.start()

    def _bootstrap_db(self):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                node_id INTEGER PRIMARY KEY,
                ring TEXT NOT NULL,
                d INTEGER NOT NULL,
                r INTEGER NOT NULL,
                sigma_T REAL NOT NULL,
                drift_phase REAL NOT NULL,
                fission_count INTEGER DEFAULT 0,
                parent_id INTEGER
            );
        """)
        conn.commit()
        conn.close()

    def spawn_process(self, ring: str, d: int = 6, r: int = 18, drift_phase: float = 0.0):
        ring = ring.upper()
        node_id = random.randint(100, 999)
        d = max(4, min(42, d))
        r = max(12, min(500, r))
        denom = 4.0 * PHI_OP * GEAR_SHIFT + 0.08 * drift_phase
        sigma_T = r - (d ** 2 / denom)
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""INSERT INTO nodes 
            (node_id, ring, d, r, sigma_T, drift_phase, fission_count, parent_id) 
            VALUES (?,?,?,?,?,?,0,NULL)""", (node_id, f"Injected_{ring}", d, r, sigma_T, drift_phase))
        conn.commit()
        conn.close()
        return type('Node', (), {"node_id": node_id, "d": d, "r": r, "sigma_T": sigma_T, "drift_phase": drift_phase})()

    def inspect_ring_safety(self, ring: str):
        ring = ring.upper()
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as node_count, COALESCE(AVG(sigma_T), 0.0) as current_avg FROM nodes WHERE ring = ?;", (f"Injected_{ring}",))
        row = c.fetchone()
        conn.close()
        current_avg = round(row["current_avg"], 4)
        budget = round(MAX_RING_PRESSURE_ALLOWANCE - current_avg, 4)
        return {
            "ring": ring, "node_count": row["node_count"], "current_average_pressure": current_avg,
            "remaining_pressure_budget": max(0.0, budget), "status": "NOMINAL" if budget >= 0 else "CRITICAL_OVERLOAD"
        }

    def audit_admission(self, node_id: int, target_ring: str):
        target_ring = target_ring.upper()
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT sigma_T FROM nodes WHERE node_id = ?", (node_id,))
        source_node = c.fetchone()
        if not source_node:
            conn.close()
            return {"status": "NOT_FOUND", "projected_avg": 999.0}
        c.execute("SELECT COUNT(*) as node_count, COALESCE(SUM(sigma_T), 0.0) as cumulative_pressure FROM nodes WHERE ring = ?;", (f"Injected_{target_ring}",))
        dest_stats = c.fetchone()
        projected_count = dest_stats["node_count"] + 1
        projected_average = (dest_stats["cumulative_pressure"] + source_node["sigma_T"]) / projected_count
        conn.close()
        status = "ALLOWED" if projected_average <= MAX_RING_PRESSURE_ALLOWANCE else "REJECTED"
        return {"status": status, "projected_avg": projected_average}

    def rebalance_manifold(self):
        """Autonomous Scheduler with Hysteresis Damping to arrest ping-pong thrashing"""
        rings = ["A", "B", "C"]
        stats = {r: self.inspect_ring_safety(r) for r in rings}
        
        sorted_rings = sorted(rings, key=lambda r: stats[r]["current_average_pressure"])
        coolest_ring = sorted_rings[0]
        hottest_ring = sorted_rings[-1]
        
        hot_pressure = stats[hottest_ring]["current_average_pressure"]
        cool_pressure = stats[coolest_ring]["current_average_pressure"]
        
        # Invariant Gradient Condition
        if hot_pressure > 25.0 and (hot_pressure - cool_pressure) > 12.0:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT node_id, sigma_T FROM nodes WHERE ring = ? ORDER BY sigma_T DESC LIMIT 1;", (f"Injected_{hottest_ring}",))
            candidate = c.fetchone()
            
            if candidate:
                node_id = candidate["node_id"]
                audit = self.audit_admission(node_id, coolest_ring)
                
                if audit["status"] == "ALLOWED":
                    # ANTI-THRASHING FILTER: Only migrate if the target ring's projected pressure
                    # remains lower than the hot ring's current standing pressure baseline.
                    if audit["projected_avg"] < (hot_pressure - 2.0):
                        c.execute("UPDATE nodes SET ring = ? WHERE node_id = ?", (f"Injected_{coolest_ring}", node_id))
                        conn.commit()
                        conn.close()
                        return {
                            "status": "REBALANCED",
                            "action": f"Auto-offloaded node {node_id} from Ring {hottest_ring} to Ring {coolest_ring}",
                            "gradient_mitigated": round(hot_pressure - cool_pressure, 4)
                        }
            conn.close()
        return {"status": "BALANCED", "metrics": stats}

    def _run_heartbeat(self):
        while self.is_running:
            try:
                log = self.rebalance_manifold()
                if log["status"] == "REBALANCED":
                    print(f"\n[HEARTBEAT OPTIMIZATION] {log['action']} | Mitigation Delta: {log['gradient_mitigated']}")
            except Exception as e:
                print(f"\n[HEARTBEAT EXCEPTION] Background balance error: {str(e)}")
            time.sleep(HEARTBEAT_INTERVAL_SEC)

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
        path_segments = parsed_url.path.strip("/").split("/")
        
        if parsed_url.path == "/":
            self._set_headers(200)
            self.wfile.write(json.dumps({"status": "ONLINE", "mode": "STABILIZED_HEARTBEAT"}).encode("utf-8"))
            return

        elif len(path_segments) == 4 and path_segments[0] == "manifold" and path_segments[1] == "ring" and path_segments[3] == "safety":
            report = matrix.inspect_ring_safety(path_segments[2])
            self._set_headers(200)
            self.wfile.write(json.dumps(report).encode("utf-8"))
            return

    def do_POST(self):
        if self.path == "/process/spawn":
            content_length = int(self.headers['Content-Length'])
            try: data = json.loads(self.rfile.read(content_length).decode('utf-8'))
            except Exception: data = {}
            ring = data.get("ring", "A")
            node = matrix.spawn_process(ring, data.get("d", 6), data.get("r", 18), data.get("drift_phase", 0.0))
            self._set_headers(201)
            self.wfile.write(json.dumps({"status": "SPAWNED", "node_id": node.node_id, "ring": ring.upper(), "sigma_T": round(node.sigma_T, 4)}).encode("utf-8"))
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
    print("[+] Stabilized Heartbeat Fabric Gateway Online at http://127.0.0.1:8080")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        matrix.is_running = False
        httpd.server_close()
EOF
dos2unix main.py
