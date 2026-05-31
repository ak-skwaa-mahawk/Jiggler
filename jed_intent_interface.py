cat > /mnt/user-data/outputs/jed_intent_interface.py << 'PYEOF'
"""
jed_intent_interface.py
=======================
Clean interface for setting intent without touching code.
Terminal UI — no dependencies beyond standard library.
"""

import os
import sys
import time
import json
import threading

INTENT_FILE = 'jed_intent.json'


def _load_intent() -> dict:
    if os.path.exists(INTENT_FILE):
        try:
            with open(INTENT_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_intent(intent: dict):
    with open(INTENT_FILE, 'w') as f:
        json.dump(intent, f, indent=2)


def print_status(substrate):
    snap = substrate.snapshot_substrate()
    gs   = snap.gs_state
    lc   = snap.lifecycle_state
    pid  = snap.pid_state
    sf   = snap.safety_flags

    print(f"\n{'─'*55}")
    print(f"  SUBSTRATE STATUS")
    print(f"{'─'*55}")
    print(f"  spin     {gs.spin:.4f}   setpoint → {pid.spin_setpoint:.4f}")
    print(f"  pressure {gs.pressure:.4f}   setpoint → {pid.pressure_setpoint:.4f}")
    print(f"  temp     {gs.temp:.4f}   setpoint → {pid.temp_setpoint:.4f}")
    print(f"  belt_r   {gs.belt_radius:.4f}   throat → {gs.core_throat:.4f}")
    print(f"  delta    {gs.closed_loop_delta:.2e}")
    print(f"  ticks    {lc.tick_count}   uptime {lc.uptime_seconds:.1f}s")
    print(f"  healthy  {lc.healthy}")
    if sf.spin_quarantine:     print(f"  ⚠️  spin quarantined")
    if sf.pressure_quarantine: print(f"  ⚠️  pressure quarantined")
    if sf.temp_quarantine:     print(f"  ⚠️  temp quarantined")
    if sf.pressure_cap_active: print(f"  ⚠️  pressure cap active")
    print(f"{'─'*55}")


PRESETS = {
    '1': {'name': 'Baseline',
          'spin': 1.5,  'pressure': 1.0, 'temp': 0.0,
          'desc': 'Steady state. Low stress, moderate authority.'},
    '2': {'name': 'Correspondence Region',
          'spin': 2.2,  'pressure': 1.2, 'temp': 0.3,
          'desc': 'Blended state. Stress and order in dialogue.'},
    '3': {'name': 'Cosmic Lock Approach',
          'spin': 3.5,  'pressure': 1.4, 'temp': 0.18,
          'desc': 'High authority, low stress. Approaching lock.'},
    '4': {'name': 'Stress Burn',
          'spin': 1.0,  'pressure': 0.8, 'temp': 0.85,
          'desc': 'Let high stress burn through. Relax containment.'},
    '5': {'name': 'Full Authority',
          'spin': 3.8,  'pressure': 1.48, 'temp': 0.15,
          'desc': 'Maximum authority. Target: Cosmic Lock.'},
}


class IntentInterface:
    """
    Terminal interface for setting substrate intent.
    Can run standalone (no substrate) to write intent files,
    or live (with substrate) to apply changes in real time.
    """

    def __init__(self, substrate=None):
        self.substrate = substrate

    def _apply(self, spin=None, pressure=None, temp=None, label=''):
        intent = _load_intent()
        if spin     is not None: intent['spin']     = spin
        if pressure is not None: intent['pressure'] = pressure
        if temp     is not None: intent['temp']     = temp
        intent['label']      = label
        intent['set_at']     = time.time()
        _save_intent(intent)

        if self.substrate:
            self.substrate.set_setpoints(spin=spin, pressure=pressure, temp=temp)
            print(f"  ✓ Applied live: spin={spin}  pressure={pressure}  temp={temp}")
        else:
            print(f"  ✓ Saved to {INTENT_FILE} — will apply on next runner start")

    def run(self):
        print("\n" + "═"*55)
        print("  JED INTENT INTERFACE")
        print("  Set system intent without touching code.")
        print("═"*55)

        while True:
            if self.substrate:
                print_status(self.substrate)

            print("\n  PRESETS")
            for k, p in PRESETS.items():
                print(f"  [{k}] {p['name']:<25} {p['desc']}")
            print(f"  [c] Custom values")
            print(f"  [s] Show current status")
            print(f"  [r] Reset to baseline")
            print(f"  [q] Quit")
            print()

            try:
                choice = input("  Choice: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\n  Exiting intent interface.")
                break

            if choice == 'q':
                break

            elif choice == 's':
                if self.substrate:
                    print_status(self.substrate)
                else:
                    intent = _load_intent()
                    print(f"\n  Last intent: {intent}")

            elif choice == 'r':
                p = PRESETS['1']
                self._apply(p['spin'], p['pressure'], p['temp'], p['name'])

            elif choice in PRESETS:
                p = PRESETS[choice]
                print(f"\n  Setting: {p['name']}")
                print(f"  {p['desc']}")
                self._apply(p['spin'], p['pressure'], p['temp'], p['name'])

            elif choice == 'c':
                try:
                    spin     = float(input("  Spin     (0.1–5.0): ").strip())
                    pressure = float(input("  Pressure (0.2–2.0): ").strip())
                    temp     = float(input("  Temp     (0.0–1.0): ").strip())
                    label    = input("  Label (optional): ").strip() or 'custom'
                    spin     = max(0.1, min(5.0, spin))
                    pressure = max(0.2, min(2.0, pressure))
                    temp     = max(0.0, min(1.0, temp))
                    self._apply(spin, pressure, temp, label)
                except ValueError:
                    print("  ⚠️  Invalid input — numbers only.")
            else:
                print("  ⚠️  Unknown choice.")

        print("  Intent interface closed.\n")


class IntentFileWatcher:
    """
    Background thread that watches jed_intent.json and applies
    changes to the substrate automatically.
    Lets you edit the intent file from any text editor or script
    and have it take effect without restarting.
    """

    def __init__(self, substrate, poll_interval: float = 2.0):
        self.substrate     = substrate
        self.poll_interval = poll_interval
        self._last_mtime   = 0.0
        self._running      = False
        self._thread       = None

    def start(self):
        self._running = True
        self._thread  = threading.Thread(
            target=self._watch_loop, daemon=True, name='JED-IntentWatcher')
        self._thread.start()
        print(f"👁️  Intent watcher active — monitoring {INTENT_FILE}")

    def _watch_loop(self):
        while self._running:
            try:
                if os.path.exists(INTENT_FILE):
                    mtime = os.path.getmtime(INTENT_FILE)
                    if mtime > self._last_mtime:
                        self._last_mtime = mtime
                        intent = _load_intent()
                        spin     = intent.get('spin')
                        pressure = intent.get('pressure')
                        temp     = intent.get('temp')
                        label    = intent.get('label', '')
                        if any(v is not None for v in [spin, pressure, temp]):
                            self.substrate.set_setpoints(
                                spin=spin, pressure=pressure, temp=temp)
                            print(f"  ↳ Intent applied: '{label}'  "
                                  f"spin={spin}  pressure={pressure}  temp={temp}")
            except Exception as e:
                print(f"⚠️  Intent watcher error: {e}")
            time.sleep(self.poll_interval)

    def stop(self):
        self._running = False


if __name__ == '__main__':
    # Standalone mode — no substrate needed
    # Just writes intent files for the runner to pick up
    ui = IntentInterface(substrate=None)
    ui.run()
PYEOF
echo "done"