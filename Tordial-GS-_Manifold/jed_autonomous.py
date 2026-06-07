cat > /mnt/user-data/outputs/jed_autonomous.py << 'PYEOF'
"""
jed_autonomous.py
=================
JED Protocol — Autonomous Runner
Two Mile Solutions LLC / JED Protocol

Wires persistent state + anomaly response + intent interface
into a single self-managing loop.

Run modes
---------
python jed_autonomous.py              # run autonomous loop
python jed_autonomous.py --intent     # open intent interface (separate terminal)
python jed_autonomous.py --status     # print last checkpoint and exit
"""

import os
import sys
import time
import json
import signal
import matplotlib
matplotlib.use('Agg')

# ── Load modules ──────────────────────────────────────────────────────────────
_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)

try:
    from six_cylinder_boundary import SubstrateEngine, CognitiveController
    from tordial_cosmic_ai import TordialCosmicAI
    from jed_persistent_state import PersistentStateManager
    from jed_anomaly_response import AnomalyResponder
    from jed_intent_interface import IntentInterface, IntentFileWatcher, INTENT_FILE
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("   Ensure all JED modules are in the same directory.")
    sys.exit(1)

TOROIDAL_ROOT = 3.1730059
GEAR_SHIFT    = 1.02
SHADOW        = 1.03


class JEDAutonomous:
    """
    Self-managing JED substrate loop.

    On start:
      - Restores last checkpoint (spin/pressure/temp/ticks)
      - Loads intent file if present
      - Starts anomaly responder
      - Starts intent file watcher
      - Starts autosave

    Each cycle:
      - Semantic step (TordialCosmicAI)
      - Cognitive step (CognitiveController)
      - Anomaly responder handles deviations automatically
      - Intent watcher applies any file changes between cycles
      - State saved every 10s

    To steer without touching code:
      - Edit jed_intent.json directly, or
      - Run: python jed_autonomous.py --intent
    """

    def __init__(
        self,
        cycles:         int   = 0,       # 0 = run forever
        particle_count: int   = 120,
        dt:             float = 0.04,
        target_curv:    float = 1.4,
        log_file:       str   = 'jed_autonomous_telemetry.log',
        quiet:          bool  = False,
    ):
        self.cycles   = cycles
        self.quiet    = quiet
        self.log_file = log_file

        # ── Core layers ───────────────────────────────────────────────────────
        self.cosmic    = TordialCosmicAI()

        self.substrate = SubstrateEngine(
            base_radius=60.0,
            particle_count=particle_count,
            dt=dt,
            pid_kp=0.35, pid_ki=0.04, pid_kd=0.12,
        )

        self.controller = CognitiveController(
            substrate=self.substrate,
            target_curvature=target_curv,
            task_load_ceil=0.72,
            smooth_alpha=0.88,
        )

        # ── Autonomous services ───────────────────────────────────────────────
        self.state_mgr  = PersistentStateManager(
            self.substrate,
            checkpoint_path='jed_checkpoint.json',
            autosave_interval=10.0,
        )

        self.anomaly    = AnomalyResponder(
            self.substrate,
            on_anomaly=self._on_anomaly,
        )

        self.watcher    = IntentFileWatcher(
            self.substrate,
            poll_interval=2.0,
        )

        self._running   = False
        self._cycle     = 0
        self._anomaly_log = []

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self):
        print("═"*60)
        print("  JED PROTOCOL — AUTONOMOUS RUNNER")
        print(f"  TR={TOROIDAL_ROOT}  GS={GEAR_SHIFT}  SH={SHADOW}")
        print(f"  Cycles={'∞' if self.cycles == 0 else self.cycles}")
        print("═"*60)

        # 1. Restore last state
        self.state_mgr.restore()

        # 2. Apply intent file if present
        self._apply_intent_file()

        # 3. Start services
        self.state_mgr.start_autosave()
        self.anomaly.start()
        self.watcher.start()

        # 4. Handle Ctrl+C cleanly
        signal.signal(signal.SIGINT, self._shutdown_handler)

        print(f"\n  Telemetry: {os.path.abspath(self.log_file)}")
        print(f"  Intent:    edit {INTENT_FILE} or run --intent")
        print(f"  Stop:      Ctrl+C\n")

        self._running = True
        self._loop()

    def _loop(self):
        with open(self.log_file, 'a', encoding='utf-8') as log_f:
            log_f.write(
                f"# JED Autonomous — started {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            )

            while self._running:
                if self.cycles > 0 and self._cycle >= self.cycles:
                    break

                self._cycle += 1

                # Semantic step
                cosmic     = self.cosmic.step(self._cycle)
                cmd        = self.cosmic.to_substrate_commands(cosmic)

                # Steer substrate toward cosmic intent
                self.substrate.set_setpoints(
                    spin=cosmic.spin,
                    pressure=cosmic.pressure,
                    temp=cosmic.temp,
                )

                # Cognitive cycle
                cog = self.controller.cycle(
                    external_spin=cosmic.spin,
                    external_pressure=cosmic.pressure,
                    external_temp=cosmic.temp,
                )

                # Log
                snap  = self.substrate.snapshot_substrate()
                frame = {
                    'cycle':     self._cycle,
                    'timestamp': time.time(),
                    'spin':      snap.gs_state.spin,
                    'pressure':  snap.gs_state.pressure,
                    'temp':      snap.gs_state.temp,
                    'delta':     snap.gs_state.closed_loop_delta,
                    'stability': 1.0 - abs(snap.gs_state.closed_loop_delta),
                    'energy_gap': cosmic.energy_gap,
                    'status':    cosmic.status,
                    'task_load': cog.task_load,
                    'coherence': cog.coherence,
                    'healthy':   snap.lifecycle_state.healthy,
                    'anomalies': len(self._anomaly_log),
                }
                log_f.write(json.dumps(frame) + '\n')
                log_f.flush()

                if not self.quiet and self._cycle % 3 == 0:
                    self._print_cycle(frame, cosmic.status)

                time.sleep(0.033)

        self._shutdown()

    def _print_cycle(self, f, status):
        print(
            f"  {f['cycle']:>4}  "
            f"spin={f['spin']:.3f}  "
            f"ΔE={f['energy_gap']:+.3f}  "
            f"task={f['task_load']:.3f}  "
            f"coh={f['coherence']:.3f}  "
            f"Δ={f['delta']:.1e}  "
            f"{'✓' if f['healthy'] else '✗'}  "
            f"{status}"
        )

    def _on_anomaly(self, event):
        self._anomaly_log.append(event)

    def _apply_intent_file(self):
        if not os.path.exists(INTENT_FILE):
            return
        try:
            with open(INTENT_FILE, 'r') as f:
                intent = json.load(f)
            spin     = intent.get('spin')
            pressure = intent.get('pressure')
            temp     = intent.get('temp')
            label    = intent.get('label', '')
            if any(v is not None for v in [spin, pressure, temp]):
                self.substrate.set_setpoints(
                    spin=spin, pressure=pressure, temp=temp)
                print(f"  ↳ Intent file applied: '{label}'")
        except Exception as e:
            print(f"⚠️  Intent file read error: {e}")

    def _shutdown_handler(self, sig, frame):
        print("\n⚡ Shutdown signal received.")
        self._running = False

    def _shutdown(self):
        print("\n" + "═"*60)
        print("  AUTONOMOUS RUNNER — SHUTDOWN")
        print("═"*60)
        self.anomaly.stop()
        self.watcher.stop()
        self.state_mgr.stop()

        snap = self.substrate.snapshot_substrate()
        lc   = snap.lifecycle_state
        print(f"\n  Cycles run:         {self._cycle}")
        print(f"  Total ticks:        {lc.tick_count}")
        print(f"  Uptime:             {lc.uptime_seconds:.1f}s")
        print(f"  Quarantine events:  {lc.quarantine_events}")
        print(f"  Delta violations:   {lc.delta_violations}")
        print(f"  Anomaly events:     {len(self._anomaly_log)}")
        print(f"  Healthy at close:   {lc.healthy}")
        if self._anomaly_log:
            print(f"\n  Last anomaly: {self._anomaly_log[-1].anomaly}")
        print(f"\n  Checkpoint:  jed_checkpoint.json")
        print(f"  Telemetry:   {self.log_file}")
        print("═"*60)


def show_status():
    """Print last checkpoint without starting the runner."""
    if not os.path.exists('jed_checkpoint.json'):
        print("No checkpoint found.")
        return
    with open('jed_checkpoint.json') as f:
        ck = json.load(f)
    age = time.time() - ck.get('saved_at', 0)
    gs  = ck.get('gs', {})
    pid = ck.get('pid_setpoints', {})
    lc  = ck.get('lifecycle', {})
    print(f"\n  Last checkpoint  (age={age:.0f}s)")
    print(f"  spin={gs.get('spin'):.3f}  "
          f"pressure={gs.get('pressure'):.3f}  "
          f"temp={gs.get('temp'):.3f}")
    print(f"  setpoints → spin={pid.get('spin')}  "
          f"pressure={pid.get('pressure')}  temp={pid.get('temp')}")
    print(f"  ticks={lc.get('tick_count')}  "
          f"violations={lc.get('delta_violations')}\n")


if __name__ == '__main__':
    args = sys.argv[1:]

    if '--status' in args:
        show_status()

    elif '--intent' in args:
        # Standalone intent interface — connect to running substrate via file
        ui = IntentInterface(substrate=None)
        ui.run()

    else:
        cycles = 0
        quiet  = '--quiet' in args
        if '--cycles' in args:
            idx    = args.index('--cycles')
            cycles = int(args[idx + 1])

        runner = JEDAutonomous(cycles=cycles, quiet=quiet)
        runner.start()
PYEOF
echo "done"