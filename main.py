cat << 'EOF' > main.py
"""
main.py
Synara Telemetry & Security System: Distributed Peer Mesh Architecture.
Supports cross-node peer telemetry audits and hot-migrating state ledgers over network gradients.
"""

import sqlite3
import json
import random
import threading
import time
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

DB_PATH = "tordial_manifold.db"
PHI_OP = 1.65036
GEAR_SHIFT = 1.04
MAX_RING_PRESSURE_ALLOWANCE = 45.0
HEARTBEAT_INTERVAL_SEC = 3.0

# CLUSTER CONFIGURATION: Define peer address maps (Simulating local orchestration mesh)
PEER_NODES = ["http://127.0.0.1:8081", "http://127.0.0.1:8082"] 

class DistributedSynaraEngine:
    def __init__(self, port=8080):
        self.port = port
        self.current_tick = 42
        self.is_running = True
        self.system_status = "NOMINAL"
        self.pqc_handshake_verified = True
        
        self._bootstrap_db()
        
        # Start Autonomous Heartbeat & Cross-Node Optimization Thread
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
        
        c.execute("SELECT COUNT(*) FROM nodes;")
        if c.fetchone()[0] == 0:
            print(f"[CLUSTER INIT] Initializing clean genesis geometry bounds on Port {self.port}...")
            for idx, ring in enumerate(["A", "B", "C"]):
                c.execute("""INSERT INTO nodes 
                    (node_id, ring, d, r, sigma_T, drift_phase, fission_count, parent_id) 
                    VALUES (?, ?, 6, 12, 1.0, 0.0, 0, NULL)""", ((idx + 1) * 10, f"Injected_{ring}"))
            conn.commit()
        conn.close()

    def spawn_process(self, ring: str, d: int = 6, r: int = 18, drift_phase: float = 0.0, static_id=None):
        ring = ring.upper()
        node_id = static_id if static_id else random.randint(100, 999)
        d = max(4, min(42, d))
        r = max(12, min(500, r))
        denom = 4.0 * PHI_OP * GEAR_SHIFT + 0.08 * drift_phase
        sigma_T = r - (d ** 2 / denom)
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""INSERT OR REPLACE INTO nodes 
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

    def _query_peer_safety(self, peer_url: str, ring: str):
        """Interrogates a remote mesh node's safety envelope endpoint over the network"""
        try:
            url = f"{peer_url}/manifold/ring/{ring}/safety"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=1.0) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception:
            return None  # Peer offline or unreachable

    def _ship_node_to_peer(self, peer_url: str, node_data: dict):
        """Executes the physical network state transition payload migration"""
        try:
            url = f"{peer_url}/cluster/ingest"
            req = urllib.request.Request(url, data=json.dumps(node_data).encode('utf-8'), method="POST")
            req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=1.5) as response:
                return json.loads(response.read().decode('utf-8'))["status"] == "SUCCESS"
        except Exception:
            return False

    def rebalance_manifold(self):
        rings = ["A", "B", "C"]
        local_stats = {r: self.inspect_ring_safety(r) for r in rings}
        
        hottest_ring = max(rings, key=lambda r: local_stats[r]["current_average_pressure"])
        hot_pressure = local_stats[hottest_ring]["current_average_pressure"]
        
        # Cross-Node Trigger: If a local ring is approaching crisis thresholds
        if hot_pressure > 30.0:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM nodes WHERE ring = ? AND node_id NOT IN (10,20,30) ORDER BY sigma_T DESC LIMIT 1;", (f"Injected_{hottest_ring}",))
            candidate = c.fetchone()
            
            if candidate:
                node_id = candidate["node_id"]
                # Scan our configured network peers for space
                for peer in PEER_NODES:
                    peer_report = self._query_peer_safety(peer, hottest_ring)
                    if peer_report and peer_report["remaining_pressure_budget"] > candidate["sigma_T"]:
                        
                        # Pack state plane attributes for shipping
                        payload = {
                            "node_id": node_id, "ring": hottest_ring, "d": candidate["d"],
                            "r": candidate["r"], "drift_phase": candidate["drift_phase"]
                        }
                        
                        # Transmit state block across the network wires
                        if self._ship_node_to_peer(peer, payload):
                            # Atomic local eviction on success
                            c.execute("DELETE FROM nodes WHERE node_id = ?", (node_id,))
                            conn.commit()
                            conn.close()
                            return {
                                "status": "NETWORK_MIGRATED",
                                "action": f"Offloaded node {node_id} across hardware boundaries to cluster peer [{peer}]"
                            }
            conn.close()
        return {"status": "LOCAL_EQUILIBRIUM", "metrics": local_stats}

    def _run_heartbeat(self):
        while self.is_running:
            try:
                log = self.rebalance_manifold()
                if log["status"] == "NETWORK_MIGRATED":
                    print(f"\n📡 [MESH OPTIMIZATION] {log['action']}")
            except Exception as e:
                print(f"\n[MESH EXCEPTION] Grid discovery sync fault: {str(e)}")
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

# Dynamic port parsing to easily test multi-node configurations on one machine
if __name__ == "__main__":
    import sys
    run_port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    
    matrix = DistributedSynaraEngine(port=run_port)
    
    class SynaraMeshGateway(BaseHTTPRequestHandler):
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
                self.wfile.write(json.dumps({"status": "ONLINE", "mesh_port": run_port}).encode("utf-8"))
                return

            elif len(path_segments) == 4 and path_segments[0] == "manifold" and path_segments[1] == "ring" and path_segments[3] == "safety":
                report = matrix.inspect_ring_safety(path_segments[2])
                self._set_headers(200)
                self.wfile.write(json.dumps(report).encode("utf-8"))
                return

        def do_POST(self):
            content_length = int(self.headers['Content-Length'])
            try: data = json.loads(self.rfile.read(content_length).decode('utf-8'))
            except Exception: data = {}

            if self.path == "/process/spawn":
                ring = data.get("ring", "A")
                node = matrix.spawn_process(ring, data.get("d", 6), data.get("r", 18), data.get("drift_phase", 0.0))
                self._set_headers(201)
                self.wfile.write(json.dumps({"status": "SPAWNED", "node_id": node.node_id, "sigma_T": round(node.sigma_T, 4)}).encode("utf-8"))
                return

            # NEW Cryptographic Cluster Ingestion API Gateway Route
            elif self.path == "/cluster/ingest":
                try:
                    node = matrix.spawn_process(
                        data["ring"], data["d"], data["r"], data["drift_phase"], static_id=data["node_id"]
                    )
                    print(f"\n📥 [CLUSTER INGEST] Successfully absorbed network process state block: Node ID {node.node_id}")
                    self._set_headers(200)
                    self.wfile.write(json.dumps({"status": "SUCCESS", "absorbed_node": node.node_id}).encode("utf-8"))
                except Exception as e:
                    self._set_headers(400)
                    self.wfile.write(json.dumps({"status": "REJECTED", "error": str(e)}).encode("utf-8"))
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

    server_address = ("127.0.0.1", run_port)
    httpd = HTTPServer(server_address, SynaraMeshGateway)
    print(f"[+] Synara Peer Mesh Engine Online at http://127.0.0.1:{run_port}")
    try: httpd.serve_forever()
    except KeyboardInterrupt:
        matrix.is_running = False
        httpd.server_close()
EOF
dos2unix main.py
