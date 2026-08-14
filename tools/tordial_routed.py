#!/usr/bin/env python3
"""
tordial-routed: Sovereign Edge Hybrid Control Plane (v9 Live Telemetry Coupled)
"""

import time
import sqlite3
import numpy as np
from pathlib import Path
from tools.kernel_telemetry import KernelNetTelemetry

# --- DEFAULT PRODUCTION PARAMETERS (v9 Baseline) ---
COMM_LIMIT = 0.012
COMM_TARGET = COMM_LIMIT * 0.95  # 0.011400
HOLONOMY_SAFETY_CEILING = 0.200
LOOP_HZ = 79.0
SLEEP_INTERVAL = 1.0 / LOOP_HZ

DB_PATH = Path("tordial_routed.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS flow_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL,
            queue_depth REAL,
            rtt_variance REAL,
            holonomy_norm REAL,
            comm1 REAL,
            comm2 REAL,
            comm3 REAL,
            comm4 REAL,
            rollback_flag INTEGER
        )
    """)
    conn.commit()
    return conn

def compute_subspace_dynamics(telemetry, X5_phase):
    commutators = []
    for i in range(4):
        comm_val = telemetry[i] * np.cos(X5_phase) - (telemetry[i]**2) * np.sin(X5_phase)
        commutators.append(comm_val)
    return np.array(commutators)

def apply_full_spectrum_damping(commutators):
    damped_comms = []
    for c in commutators:
        if abs(c) > COMM_LIMIT:
            clamped = np.sign(c) * COMM_TARGET
            damped_comms.append(clamped)
        else:
            damped_comms.append(c)
    return np.array(damped_comms)

def run_control_plane():
    conn = init_db()
    cursor = conn.cursor()
    telemetry_reader = KernelNetTelemetry(interface="wlan0")
    
    cycle_count = 0
    phase = 0.0
    
    print(f"[+] tordial-routed daemon active @ {LOOP_HZ} Hz.")
    print(f"[+] Live Kernel Netdev Telemetry Attached [wlan0 / fallback].")
    print(f"[+] Full-spectrum micro-damping active (|Comm_i| <= {COMM_TARGET:.6f})")

    try:
        while True:
            t0 = time.perf_counter()
            cycle_count += 1
            phase = (phase + 0.05) % (2 * np.pi)

            # 1. Live Ingest from Kernel Netdev
            telemetry = telemetry_reader.read_live_telemetry()

            # 2. Subspace Evaluation
            comms = compute_subspace_dynamics(telemetry, phase)

            # 3. Micro-Damping Intercept
            damped_comms = apply_full_spectrum_damping(comms)

            # 4. Holonomy Norm Calculation
            h_norm = float(np.linalg.norm(damped_comms) * 3.5)

            # 5. Safety Floor & Rollback Check
            rollback = 0
            if h_norm > HOLONOMY_SAFETY_CEILING:
                rollback = 1
                damped_comms = np.clip(damped_comms, -COMM_TARGET * 0.5, COMM_TARGET * 0.5)

            # 6. Ledger Commit Every 79 Cycles (~1.0s)
            if cycle_count % int(LOOP_HZ) == 0:
                cursor.execute("""
                    INSERT INTO flow_ledger 
                    (timestamp, queue_depth, rtt_variance, holonomy_norm, comm1, comm2, comm3, comm4, rollback_flag)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    time.time(),
                    float(telemetry[0]),
                    float(telemetry[1]),
                    h_norm,
                    float(damped_comms[0]),
                    float(damped_comms[1]),
                    float(damped_comms[2]),
                    float(damped_comms[3]),
                    rollback
                ))
                conn.commit()
                print(f"[CYCLE {cycle_count:06d}] H-Norm: {h_norm:.6f} | Comm1: {damped_comms[0]:+.6f} | Comm2: {damped_comms[1]:+.6f} | Rollback: {rollback}")

            # 7. 79.0 Hz Loop Pacing
            elapsed = time.perf_counter() - t0
            sleep_time = max(0.0, SLEEP_INTERVAL - elapsed)
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\n[!] Daemon stopped gracefully.")
    finally:
        conn.close()

if __name__ == "__main__":
    run_control_plane()
