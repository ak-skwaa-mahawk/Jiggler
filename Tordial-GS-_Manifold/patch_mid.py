cat << 'EOF' > patch_mid.py
DB_PATH = "tordial_manifold.db"

def _ensure_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS nodes (
        node_id INTEGER, ring TEXT, d INTEGER, r INTEGER, sigma_T REAL,
        drift_phase REAL, fission_count INTEGER, parent_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit()
    conn.close()

def persist_node_state(node: OpenTordialAgentNode, ring: str = "A"):
    if not os.path.exists(DB_PATH): _ensure_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO nodes (node_id, ring, d, r, sigma_T, drift_phase, fission_count, parent_id) VALUES (?,?,?,?,?,?,0,NULL)",
        (node.node_id, ring, node.d, node.r, node.sigma_T, node.drift_phase))
    conn.commit()
    conn.close()

class CurvatureField:
    def __init__(self): 
        self.last_pressure = 0.0
        self.last_resonance = 0.0
        
    def compute(self, avg_sigma: float, avg_kappa: float, node_count: int) -> Tuple[float, float]:
        k_norm = max(0.0, min(1.0, avg_kappa / 12.0))
        bp = 0.45 * k_norm + 0.20 * max(0.0, avg_sigma / 500.0)
        pressure = max(0.0, min(1.25, bp + max(0.0, min(0.3, (node_count - 24) / 80.0))))
        resonance = max(0.0, min(1.0, 0.55 * k_norm))
        return pressure, resonance

class RingGovernor:
    def __init__(self, target_sigma: float = 120.0):
        self.target = target_sigma
        self._integral = 0.0
        self._prev_error = 0.0
        
    def step(self, current_sigma: float) -> Tuple[int, int]:
        error = self.target - current_sigma
        self._integral = max(-50.0, min(50.0, self._integral + error))
        derivative = error - self._prev_error
        self._prev_error = error
        u = 0.012 * error + 0.003 * self._integral + 0.006 * derivative
        delta_d = int(round(max(-1, min(1, u * 0.2))))
        delta_r = int(round(max(-4, min(4, u * 0.8))))
        return delta_d, delta_r
EOF
