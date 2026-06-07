cat << 'EOF' > tordial_bridge_governor.py
import sqlite3
import time
from datetime import datetime

def run_bridge_aggregation():
    db_path = "tordial_gs.db"
    print("🚀 [BRIDGE GOVERNOR] Analytical invariant cross-coupling engine active.")
    
    while True:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Pull metrics strictly from nominal, un-vetoed Rust runs
            cursor.execute("""
                SELECT AVG(holonomy_norm_local), AVG(commutator_1_5) 
                FROM runs 
                WHERE runtime_env LIKE 'Rust%' AND quarantine_rate <= 0.30;
            """)
            rust_h, rust_c = cursor.fetchone()
            
            # Pull metrics strictly from stable Python runs
            cursor.execute("""
                SELECT AVG(holonomy_norm), AVG(commutator_1_5) 
                FROM runs 
                WHERE runtime_env LIKE 'Python%' AND rollback_flag = 0;
            """)
            py_h, py_c = cursor.fetchone()
            
            # Fallback to nominal baselines if either lane has a cold-start blank status
            rust_h = rust_h if rust_h is not None else 0.076
            rust_c = rust_c if rust_c is not None else -0.0108
            py_h = py_h if py_h is not None else 0.018
            py_c = py_c if py_c is not None else -0.0021
            
            # Commit the evaluated cross-lineage equilibrium centroids
            cursor.execute("""
                INSERT INTO cross_lineage_state 
                (timestamp, mean_h_rust, mean_h_python, mean_c_rust, mean_c_python)
                VALUES (?, ?, ?, ?, ?);
            """, (datetime.now().isoformat(), rust_h, py_h, rust_c, py_c))
            conn.commit()
            
            print(f"🔹 [BIAS MATRIX SYNCED] Rust H_μ: {rust_h:.5f}, C_μ: {rust_c:.5f} | Python H_μ: {py_h:.5f}, C_μ: {py_c:.5f}")
            
        except Exception as e:
            print(f"❌ [BRIDGE ERROR] Invariant aggregation cycle stalled: {e}")
            
        finally:
            conn.close()
            
        # Run calculation intervals every 10 seconds to avoid locking disk I/O channels
        time.sleep(10)

if __name__ == "__main__":
    run_bridge_aggregation()
EOF
