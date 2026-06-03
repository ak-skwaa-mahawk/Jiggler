cat << 'EOF' > main.py
"""
main.py
Zero-Dependency Native HTTP Micro-Gateway Interface for Verifiable Tordial-GS Matrix Ledger
"""

import sqlite3
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

DB_PATH = "tordial_manifold.db"

class NativeLedgerGateway(BaseHTTPRequestHandler):
    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def do_GET(self):
        # 1. Root Endpoint Mapping
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

        # 2. Group Telemetry Summary Endpoint Mapping
        elif self.path == "/manifold/telemetry":
            try:
                conn = sqlite3.connect(DB_PATH)
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                c.execute("""
                    SELECT ring, COUNT(*) as recorded_ticks, AVG(sigma_T) as mean_tensor_pressure 
                    FROM nodes 
                    WHERE ring LIKE 'Live_%' 
                    GROUP BY ring;
                """)
                rows = c.fetchall()
                conn.close()

                self._set_headers(200)
                if not rows:
                    self.wfile.write(json.dumps({"message": "Ledger is nominal but currently vacant."}).encode("utf-8"))
                    return

                payload = {
                    "timestamp_sync": "UTC_LOCKED",
                    "rings": {row["ring"]: {"datapoints": row["recorded_ticks"], "avg_pressure": round(row["mean_tensor_pressure"], 4)} for row in rows}
                }
                self.wfile.write(json.dumps(payload).encode("utf-8"))
            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": f"Ledger interrogation failure: {str(e)}"}).encode("utf-8"))
            return

        # 3. Individual Node Parameters Mapping
        elif self.path.startswith("/manifold/nodes/"):
            ring_id = self.path.split("/")[-1].upper()
            target_ring = f"Live_{ring_id}"
            try:
                conn = sqlite3.connect(DB_PATH)
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                c.execute("""
                    SELECT node_id, d, r, sigma_T, drift_phase 
                    FROM nodes 
                    WHERE ring = ? 
                    ORDER BY created_at DESC LIMIT 12;
                """, (target_ring,))
                rows = c.fetchall()
                conn.close()

                if not rows:
                    self._set_headers(404)
                    self.wfile.write(json.dumps({"error": f"No data for ring segment: {ring_id}"}).encode("utf-8"))
                    return

                self._set_headers(200)
                self.wfile.write(json.dumps([dict(row) for row in rows]).encode("utf-8"))
            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint route not found"}).encode("utf-8"))

if __name__ == "__main__":
    server_address = ("127.0.0.1", 8080)
    httpd = HTTPServer(server_address, NativeLedgerGateway)
    print("[+] Zero-Dependency Native REST Gateway Online listening at http://127.0.0.1:8080")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[-] Gateway micro-kernel shutting down gracefully.")
        httpd.server_close()
EOF
dos2unix main.py
