#!/usr/bin/env python3
# manifold_perimeter_daemon.py — Always-On Sovereign Perimeter Guardian
import os
import sys
import json
import subprocess
import time
import signal

# Secure absolute library path resolution
TARGET_DIR = os.path.expanduser("~/Tordial-GS-_Manifold/tools")
if TARGET_DIR not in sys.path:
    sys.path.insert(0, TARGET_DIR)

from signal_triage import SignalTriageUnit

class PerimeterDaemon:
    def __init__(self):
        self.base_dir = os.path.expanduser("~/Tordial-GS-_Manifold")
        self.pipe_path = os.path.join(self.base_dir, "signals.pipe")
        self.triage = SignalTriageUnit()
        self.running = True

    def setup_pipe(self):
        """Creates the named pipe interface if it doesn't exist."""
        if os.path.exists(self.pipe_path):
            if not os.path.pobj: # Quick structural sanity check
                try:
                    os.remove(self.pipe_path)
                except:
                    pass
        
        if not os.path.exists(self.pipe_path):
            try:
                os.mkfifo(self.pipe_path)
                # Set permissions so the local operator runtime can read/write
                os.chmod(self.pipe_path, 0o600)
            except Exception as e:
                print(f"❌ [DAEMON CRITICAL]: Named pipe creation failed: {e}", file=sys.stderr)
                sys.exit(1)

    def trigger_alert(self, evaluation: dict):
        """Triggers local audio-visual terminal alerts without relying on external packages."""
        # Standard ASCII Bell control character to trigger a hardware beep/vibration if supported
        sys.stdout.write("\a")
        sys.stdout.flush()
        
        # High-visibility ANSI terminal warning banner
        print("\n" + "!" * 80)
        print(f"🚨 [PERIMETER ALERT]: CRITICAL INTERCEPT AT {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   ↳ RISK LEVEL: HIGH ADVERSARIAL MATRIX DETECTED")
        print(f"   ↳ RULE MATCH: {evaluation.get('rule_triggered')}")
        print(f"   ↳ REASON:     {evaluation.get('quarantine_reason')}")
        print(f"   ↳ SUMMARY:    {evaluation.get('signal_summary')}")
        print("!" * 80 + "\n")
        sys.stdout.flush()

    def handle_signal(self, raw_line: str):
        """Processes a single line extracted from the ingress stream pipeline."""
        clean_line = raw_line.strip()
        if not clean_line:
            return

        evaluation = self.triage.evaluate_signal(clean_line)

        if evaluation["action_taken"] == "ISOLATE_AND_LOG":
            self.triage.log_quarantine(evaluation)
            self.trigger_alert(evaluation)

        elif evaluation["action_taken"] == "PASS_TO_MANIFOLD":
            print(f"🟩 [DAEMON PASS]: Verified clean traffic frame -> Forwarding downstream.")
            sys.stdout.flush()
            
            enriched_data = {
                "raw_signal": clean_line,
                "ingress_vector": "DAEMON_FIFO_v1.3",
                "triage_classification": evaluation["classification"]
            }
            
            # Forward cleanly to the unified nervous core
            core_script = os.path.join(self.base_dir, "isst_toft_core.py")
            if os.path.exists(core_script):
                try:
                    subprocess.run(
                        [sys.executable, core_script],
                        input=json.dumps(enriched_data),
                        text=True,
                        capture_output=True,
                        check=True
                    )
                except Exception as e:
                    print(f"⚠️ [DAEMON WARN]: Core processing forwarding lag: {e}", file=sys.stderr)

    def start(self):
        """Main persistent processing loop execution block."""
        self.setup_pipe()
        print(f"🦅 [PERIMETER DAEMON ONLINE]: Watching active stream horizon at {self.pipe_path}")
        print("   -> Listening for asynchronous operational telemetry packets... (Press Ctrl+C to terminate)")
        sys.stdout.flush()

        while self.running:
            try:
                # Opening the FIFO blocks until a writer connects, preventing CPU thrashing
                with open(self.pipe_path, "r") as pipe:
                    for line in pipe:
                        if line:
                            self.handle_signal(line)
            except KeyboardInterrupt:
                self.running = False
            except Exception as e:
                # Prevent crashing on unexpected pipe flushes; reset state and continue
                time.sleep(0.5)

        print("\n🛑 [DAEMON OFFLINE]: Security interface teardown complete.")
        try:
            os.remove(self.pipe_path)
        except:
            pass

if __name__ == "__main__":
    daemon = PerimeterDaemon()
    daemon.start()
