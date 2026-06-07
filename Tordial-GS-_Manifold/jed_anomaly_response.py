cat > /mnt/user-data/outputs/jed_anomaly_response.py << 'PYEOF'
"""
jed_anomaly_response.py
=======================
Automated anomaly response for the JED substrate.
Watches for delta drift, stability warnings, pressure spikes,
and phase lockout — responds without human intervention.
"""

import time
import threading
from dataclasses import dataclass
from typing import List, Optional, Callable

# jed_anomaly_response.py (extended)

from jed_pid_bandit import update_pid_bandit
from jed_persistent_state import load_pid_bandit, save_pid_bandit

def compute_pid_reward(stability, safety, performance,
                       alpha=0.5, beta=0.3, gamma=0.2):
    return alpha * stability + beta * safety + gamma * performance

def evaluate_transition(plan, before, after, memory,
                        pid_gain_index: int = None):
    stability, safety, performance = compute_scores(plan, before, after)
    reward = compute_reward(stability, safety, performance)

    # GS regime bandit update (as before)
    bandit = load_regime_bandit(memory)
    update_regime_bandit(bandit, plan.gs_regime, reward)
    save_regime_bandit(memory, bandit)

    # PID bandit update (if we used a specific gain index this cycle)
    if pid_gain_index is not None:
        pid_bandit = load_pid_bandit(memory)
        pid_reward = compute_pid_reward(stability, safety, performance)
        update_pid_bandit(pid_bandit, pid_gain_index, pid_reward)
        save_pid_bandit(memory, pid_bandit)

    result = CriticResult(
        score=reward,
        stability_score=stability,
        safety_score=safety,
        performance_score=performance,
        anomalies=detect_anomalies(before, after),
        policy_adjustments={},
    )
    return result


@dataclass
class AnomalyEvent:
    """A recorded anomaly and the response taken."""
    tick:        int
    timestamp:   float
    anomaly:     str    # what was detected
    severity:    str    # 'warn' | 'critical'
    response:    str    # what was done
    resolved:    bool   = False


class AnomalyResponder:
    """
    Watches substrate telemetry and responds to anomalies automatically.

    Anomaly types and responses
    ---------------------------
    DELTA_DRIFT      — closed_loop_delta > threshold
                       Response: quarantine pressure, reduce spin 10%
    STABILITY_WARN   — stability < 0.99
                       Response: back off relaxation to 0.5
    PRESSURE_SPIKE   — pressure hit the cap 3+ ticks running
                       Response: reduce pressure setpoint by 0.1
    PHASE_LOCKOUT    — all particles stuck in INTAKE for N ticks
                       Response: brief temp spike to break the jam
    TEMP_RUNAWAY     — temp stayed at max for N ticks
                       Response: force temp setpoint down

    Usage
    -----
    responder = AnomalyResponder(substrate)
    responder.start()    # background monitor
    responder.stop()     # clean shutdown
    """

    # Thresholds
    DELTA_THRESHOLD      = 1e-9
    STABILITY_FLOOR      = 0.99
    PRESSURE_SPIKE_TICKS = 3
    PHASE_LOCKOUT_TICKS  = 10
    TEMP_RUNAWAY_TICKS   = 5
    POLL_INTERVAL        = 0.5   # seconds between checks

    def __init__(self, substrate, on_anomaly: Optional[Callable] = None):
        self.substrate   = substrate
        self.on_anomaly  = on_anomaly   # optional callback
        self.events:  List[AnomalyEvent] = []
        self._running = False
        self._thread  = None

        # Rolling counters
        self._pressure_spike_count = 0
        self._phase_lockout_count  = 0
        self._temp_runaway_count   = 0
        self._last_tick            = 0

    # ── Start / stop ──────────────────────────────────────────────────────────

    def start(self):
        self._running = True
        self._thread  = threading.Thread(
            target=self._monitor_loop, daemon=True, name='JED-Anomaly')
        self._thread.start()
        print("🔍 Anomaly responder active.")

    def stop(self):
        self._running = False
        print(f"🔍 Anomaly responder stopped. "
              f"Total events: {len(self.events)}")

    # ── Monitor loop ──────────────────────────────────────────────────────────

    def _monitor_loop(self):
        while self._running:
            try:
                self._check()
            except Exception as e:
                print(f"⚠️  Anomaly monitor error: {e}")
            time.sleep(self.POLL_INTERVAL)

    def _check(self):
        snap = self.substrate.snapshot_substrate()
        gs   = snap.gs_state
        mf   = snap.manifold_state
        sf   = snap.safety_flags
        lc   = snap.lifecycle_state

        # Skip if no new ticks
        if lc.tick_count == self._last_tick:
            return
        self._last_tick = lc.tick_count

        # ── 1. Delta drift ────────────────────────────────────────────────────
        if abs(gs.closed_loop_delta) > self.DELTA_THRESHOLD:
            self._respond(
                tick=lc.tick_count,
                anomaly=f"DELTA_DRIFT delta={gs.closed_loop_delta:.2e}",
                severity='critical',
                response="quarantine_pressure + spin -10%",
            )
            new_spin = max(0.1, gs.spin * 0.9)
            self.substrate.set_setpoints(spin=new_spin)
            self.substrate.closed_loop_tick(quarantine_pressure=True)

        # ── 2. Stability warning ──────────────────────────────────────────────
        elif sf.stability_warning:
            self._respond(
                tick=lc.tick_count,
                anomaly=f"STABILITY_WARN stability<{self.STABILITY_FLOOR}",
                severity='warn',
                response="relaxation → 0.5",
            )
            self.substrate.closed_loop_tick(relaxation_strength=0.5)

        # ── 3. Pressure spike (cap hit N ticks running) ───────────────────────
        if sf.pressure_cap_active:
            self._pressure_spike_count += 1
        else:
            self._pressure_spike_count = 0

        if self._pressure_spike_count >= self.PRESSURE_SPIKE_TICKS:
            snap2 = self.substrate.snapshot_substrate()
            cur_p = snap2.pid_state.pressure_setpoint
            new_p = max(0.2, cur_p - 0.1)
            self._respond(
                tick=lc.tick_count,
                anomaly=f"PRESSURE_SPIKE {self._pressure_spike_count} ticks at cap",
                severity='warn',
                response=f"pressure setpoint {cur_p:.2f} → {new_p:.2f}",
            )
            self.substrate.set_setpoints(pressure=new_p)
            self._pressure_spike_count = 0

        # ── 4. Phase lockout (all particles in INTAKE) ────────────────────────
        if mf.total_particles > 0 and mf.intake_count == mf.total_particles:
            self._phase_lockout_count += 1
        else:
            self._phase_lockout_count = 0

        if self._phase_lockout_count >= self.PHASE_LOCKOUT_TICKS:
            self._respond(
                tick=lc.tick_count,
                anomaly=f"PHASE_LOCKOUT all {mf.total_particles} in INTAKE",
                severity='warn',
                response="temp spike 0.3 to break jam",
            )
            self.substrate.closed_loop_tick(temp=min(1.0, gs.temp + 0.3))
            self._phase_lockout_count = 0

        # ── 5. Temp runaway ───────────────────────────────────────────────────
        if gs.temp >= 0.95:
            self._temp_runaway_count += 1
        else:
            self._temp_runaway_count = 0

        if self._temp_runaway_count >= self.TEMP_RUNAWAY_TICKS:
            snap3 = self.substrate.snapshot_substrate()
            cur_t = snap3.pid_state.temp_setpoint
            new_t = max(0.0, cur_t - 0.15)
            self._respond(
                tick=lc.tick_count,
                anomaly=f"TEMP_RUNAWAY {self._temp_runaway_count} ticks at max",
                severity='warn',
                response=f"temp setpoint {cur_t:.2f} → {new_t:.2f}",
            )
            self.substrate.set_setpoints(temp=new_t)
            self._temp_runaway_count = 0

    def _respond(self, tick, anomaly, severity, response):
        event = AnomalyEvent(
            tick=tick,
            timestamp=time.time(),
            anomaly=anomaly,
            severity=severity,
            response=response,
        )
        self.events.append(event)
        icon = '🚨' if severity == 'critical' else '⚠️ '
        print(f"{icon} [{tick}] {anomaly}  →  {response}")
        if self.on_anomaly:
            self.on_anomaly(event)

    def recent_events(self, n: int = 10) -> List[AnomalyEvent]:
        return list(self.events[-n:])

    def summary(self) -> str:
        if not self.events:
            return "No anomalies recorded."
        critical = sum(1 for e in self.events if e.severity == 'critical')
        warn     = sum(1 for e in self.events if e.severity == 'warn')
        return (f"Anomaly summary: {len(self.events)} total  "
                f"critical={critical}  warn={warn}  "
                f"last='{self.events[-1].anomaly}'")
PYEOF
echo "done"