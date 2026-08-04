#!/usr/bin/env python3
# manifold_monitor.py — Real-Time Manifold Telemetry Dashboard Console (v1.3.0)
import os
import sys
import json
import time

class ManifoldConsoleMonitor:
    def __init__(self):
        self.base_dir = os.path.expanduser("~/Tordial-GS-_Manifold")
        self.ledger_path = os.path.join(self.base_dir, "state_ledger.json")
        self.trajectory_path = os.path.join(self.base_dir, "manifold_trajectories.jsonl")
        self.analyzer_path = os.path.join(self.base_dir, "tools/manifold_analyzer.py")

    def run_telemetry_loop(self):
        """Standard curses-free refreshing console loop optimized for Termux viewports."""
        try:
            while True:
                # Clear terminal screen
                sys.stdout.write("\033[H\033[J")
                
                # Fetch base ledger metrics
                ledger_data = {}
                if os.path.exists(self.ledger_path):
                    try:
                        with open(self.ledger_path, "r") as f:
                            ledger_data = json.load(f)
                    except:
                        pass
                
                # Fetch recent trajectory stream metrics
                trajectory_history = []
                if os.path.exists(self.trajectory_path):
                    try:
                        with open(self.trajectory_path, "r") as f:
                            lines = f.readlines()
                            trajectory_history = [json.loads(line.strip()) for line in lines if line.strip()]
                    except:
                        pass

                # Query analyzer results
                analyzer_metrics = {}
                if os.path.exists(self.analyzer_path):
                    try:
                        import subprocess
                        res = subprocess.run([sys.executable, self.analyzer_path], capture_output=True, text=True)
                        if res.returncode == 0:
                            raw_out = res.stdout
                            j_start = raw_out.find("{")
                            if j_start != -1:
                                analyzer_metrics = json.loads(raw_out[j_start:])
                    except:
                        pass

                active_state = ledger_data.get("current_state", "STABLE_ALIGNMENT")
                history = ledger_data.get("history", [])
                current_hz = history[-1]["hz"] if history else 0.0
                current_coords = history[-1]["coords"] if history else {"X": 0.0, "Y": 0.0, "Z": 0.0}
                
                # Fetch resonance from the most recent logged trajectory frame
                current_resonance = trajectory_history[-1].get("resonance", 1.0) if trajectory_history else 1.0

                # Construct Console Layout Render Block
                print("=" * 64)
                print("🌌 TORDIAL MANIFOLD SYSTEM TELEMETRY MONITOR")
                print("=" * 64)
                
                # State Block
                state_color = "\033[92m" if active_state == "STABLE_ALIGNMENT" else "\033[91m"
                print(f"📡 CORE SYSTEM STATE  : {state_color}{active_state}\033[0m")
                print(f"📊 INTERCEPT CEILING  : {analyzer_metrics.get('path_projection', {}).get('projection_confidence_rating', 'STANDARD_CEILING')}")
                print("-" * 64)

                # Vector Coordinate Block
                print("🎯 CURRENT MANIFOLD GEOMETRIC SPACE COORDINATES:")
                print(f"   -> Coordinate [X]  : {current_coords.get('X', 0.0):.4f}")
                print(f"   -> Coordinate [Y]  : {current_coords.get('Y', 0.0):.4f}")
                print(f"   -> Coordinate [Z]  : {current_coords.get('Z', 0.0):.4f}")
                print("-" * 64)

                # Resonance Network Block
                res_color = "\033[92m" if current_resonance >= 0.85 else "\033[93m"
                print("🕸️  RESONANCE ATTRACTION GRID:")
                print(f"   -> Resonance Factor R: {res_color}{current_resonance:.4f}\033[0m")
                print(f"   -> Target Node Match : {trajectory_history[-1].get('gate_state', 'N/A') if trajectory_history else 'N/A'}")
                print("-" * 64)

                # Kinetic Metrics Block
                proj_coords = analyzer_metrics.get("path_projection", {}).get("predicted_next_coordinates", {})
                last_vel = trajectory_history[-1].get("velocity", 0.0) if trajectory_history else 0.0
                print("⚡ REAL-TIME KINETIC VECTOR PROFILE:")
                print(f"   -> Instantaneous F0: {current_hz:.4f} Hz")
                print(f"   -> Translation Δd   : {last_vel:.4f}")
                print(f"   -> Mean Momentum M : {analyzer_metrics.get('kinetic_analysis', {}).get('mean_kinetic_momentum_m', 0.0):.4f}")
                print(f"   -> Field Centroid  : X={proj_coords.get('X', 0.0):.2f}, Y={proj_coords.get('Y', 0.0):.2f}, Z={proj_coords.get('Z', 0.0):.2f}")
                print("-" * 64)

                # Output final log traces
                print("🪵 RECENT SIGNAL LOG SUMMARY TRAJECTORY:")
                recent_traces = trajectory_history[-3:] if len(trajectory_history) >= 3 else trajectory_history
                for trace in reversed(recent_traces):
                    sum_txt = trace.get("signal_summary", "")[:35]
                    print(f"   [{trace.get('timestamp', '')[11:19]}] {sum_txt:<35} | R={trace.get('resonance', 1.0):.4f}")
                print("=" * 64)
                print("Press Ctrl+C to close monitor window...")
                
                time.sleep(2.0)
        except KeyboardInterrupt:
            print("\n🌌 Telemetry monitor cleanly disconnected. Skoden.")

if __name__ == "__main__":
    monitor = ManifoldConsoleMonitor()
    monitor.run_telemetry_loop()
