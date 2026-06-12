"""
jed_unified_runner.py
=====================
JED Protocol — Unified Semantic + Physics Runner
Two Mile Solutions LLC / JED Protocol
"""

import os
import sys
import math
import time
import json
import importlib.util
import matplotlib
matplotlib.use('Agg')

# ── Load substrate module ─────────────────────────────────────────────────────
_here = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_here)

try:
    from six_cylinder_boundary import (
        SixCylinderBoundary, ParticleFlowEngine6D,
        SubstrateEngine, CognitiveController, SubstrateSnapshot
    )
    from tordial_cosmic_ai import TordialCosmicAI, CosmicState
except ImportError:
    def _load_mod(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    _mod = _load_mod('six_cylinder_boundary', os.path.join(_here, 'six_cylinder_boundary.py'))
    SixCylinderBoundary  = _mod.SixCylinderBoundary
    ParticleFlowEngine6D = _mod.ParticleFlowEngine6D
    SubstrateEngine      = _mod.SubstrateEngine
    CognitiveController  = _mod.CognitiveController
    SubstrateSnapshot    = _mod.SubstrateSnapshot

    _mod2 = _load_mod('tordial_cosmic_ai', os.path.join(_here, 'tordial_cosmic_ai.py'))
    TordialCosmicAI = _mod2.TordialCosmicAI
    CosmicState     = _mod2.CosmicState

# ── Constants ─────────────────────────────────────────────────────────────────
TOROIDAL_ROOT = 3.1730059
GEAR_SHIFT    = 1.02
SHADOW        = 1.03


# ── Unified frame ─────────────────────────────────────────────────────────────

class UnifiedFrame:
    """One cycle of output across all three layers."""
    __slots__ = [
        'cycle', 'timestamp',
        'cosmic_spin', 'cosmic_temp', 'cosmic_pressure',
        'energy_gap', 'cosmic_status', 'relaxation', 'quarantine_pressure',
        'gs_spin', 'gs_pressure', 'gs_temp',
        'core_throat', 'belt_radius', 'cap_radius',
        'closed_loop_delta', 'stability',
        'curvature_drift', 'task_load', 'arousal', 'coherence',
        'phase_balance', 'phase_momentum', 'cog_spin_cmd', 'cog_pressure_cmd',
        'healthy', 'warnings',
    ]

    def __init__(self, cycle, cosmic: CosmicState, snap: SubstrateSnapshot,
                 cog_report, cmd: dict):
        self.cycle     = cycle
        self.timestamp = time.time()

        self.cosmic_spin         = cosmic.spin
        self.cosmic_temp         = cosmic.temp
        self.cosmic_pressure     = cosmic.pressure
        self.energy_gap          = cosmic.energy_gap
        self.cosmic_status       = cosmic.status
        self.relaxation          = cmd.get('relaxation_strength', 1.0)
        self.quarantine_pressure = cmd.get('quarantine_pressure', False)

        gs = snap.gs_state
        self.gs_spin           = gs.spin
        self.gs_pressure       = gs.pressure
        self.gs_temp           = gs.temp
        self.core_throat       = gs.core_throat
        self.belt_radius       = gs.belt_radius
        self.cap_radius        = gs.cap_radius
        self.closed_loop_delta = gs.closed_loop_delta
        self.stability         = 1.0 - abs(gs.closed_loop_delta)

        self.curvature_drift  = cog_report.curvature_drift
        self.task_load        = cog_report.task_load
        self.arousal          = cog_report.arousal
        self.coherence        = cog_report.coherence
        self.phase_balance    = cog_report.phase_balance
        self.phase_momentum   = cog_report.phase_momentum
        self.cog_spin_cmd     = cog_report.spin_command
        self.cog_pressure_cmd = cog_report.pressure_command

        self.healthy  = snap.lifecycle_state.healthy
        self.warnings = cog_report.warnings

    def to_dict(self) -> dict:
        return {s: getattr(self, s) for s in self.__slots__}

    def print_line(self):
        gap_str = f"{self.energy_gap:+.3f}"
        print(
            f"  {self.cycle:>2}  "
            f"ΔE={gap_str:<7}  "
            f"spin={self.gs_spin:.3f}  "
            f"temp={self.gs_temp:.3f}  "
            f"throat={self.core_throat:.2f}  "
            f"belt={self.belt_radius:.2f}  "
            f"task={self.task_load:.3f}  "
            f"coh={self.coherence:.3f}  "
            f"relax={self.relaxation:.2f}  "
            f"{self.cosmic_status}"
        )


# ── Unified runner ────────────────────────────────────────────────────────────

class JEDUnifiedRunner:
    """
    Couples TordialCosmicAI → SubstrateEngine → CognitiveController.

    Each cycle:
      1. Semantic step  — CosmicAI produces CosmicState + substrate commands
      2. Setpoints      — substrate steered from cosmic spin/temp/pressure
      3. Cognitive cycle — sense → predict → gauge → adjust → step
      4. Frame assembly — unified snapshot across all three layers
      5. Telemetry      — JSON log flushed per cycle
    """

    def __init__(
        self,
        cycles:         int   = 18,
        particle_count: int   = 120,
        dt:             float = 0.04,
        target_curv:    float = 1.4,
        log_file:       str   = 'jed_unified_telemetry.log',
        quiet:          bool  = False,
    ):
        self.cycles   = cycles
        self.quiet    = quiet
        self.log_file = log_file

        self.cosmic = TordialCosmicAI()

        self.substrate = SubstrateEngine(
            base_radius=60.0, particle_count=particle_count, dt=dt,
            pid_kp=0.35, pid_ki=0.04, pid_kd=0.12,
        )

        self.controller = CognitiveController(
            substrate=self.substrate,
            target_curvature=target_curv,
            task_load_ceil=0.72,
            smooth_alpha=0.88,
        )

        self.frames: list = []

    def run(self) -> list:
        if not self.quiet:
            print("=" * 95)
            print("  JED PROTOCOL — UNIFIED SEMANTIC + PHYSICS RUN")
            print(f"  TR={TOROIDAL_ROOT}  GS={GEAR_SHIFT}  SH={SHADOW}")
            print(f"  Cycles={self.cycles}  Target curvature=1.4")
            print("=" * 95)
            print(f"  {'Cy':>2}  {'ΔE':<8}  {'Spin':<7}  {'Temp':<7}  "
                  f"{'Throat':<8}  {'Belt':<7}  {'Task':<7}  "
                  f"{'Coh':<6}  {'Relax':<7}  Status")
            print("-" * 95)

        # Log file opened once — no per-cycle open/close overhead
        with open(self.log_file, 'w', encoding='utf-8') as log_f:
            log_f.write(
                f"# JED Unified Telemetry — {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            )

            for cycle in range(1, self.cycles + 1):

                # 1. Semantic step
                cosmic = self.cosmic.step(cycle)
                cmd    = self.cosmic.to_substrate_commands(cosmic)

                # 2. Transmit setpoints to substrate
                self.substrate.set_setpoints(
                    spin=cosmic.spin,
                    pressure=cosmic.pressure,
                    temp=cosmic.temp,
                )

                # 3. Cognitive execution cycle
                cog_report = self.controller.cycle(
                    external_spin=cosmic.spin,
                    external_pressure=cosmic.pressure,
                    external_temp=cosmic.temp,
                )

                # 4. Snapshot + frame assembly
                snap  = self.substrate.snapshot_substrate()
                frame = UnifiedFrame(cycle, cosmic, snap, cog_report, cmd)
                self.frames.append(frame)

                # 5. Flush to telemetry log
                log_f.write(json.dumps(frame.to_dict()) + '\n')

                if not self.quiet:
                    frame.print_line()

        if not self.quiet and self.frames:
            self._print_summary()

        return self.frames

    def _print_summary(self):
        print("\n" + "=" * 95)
        print("  UNIFIED RUN COMPLETE")
        print("=" * 95)

        first = self.frames[0]
        last  = self.frames[-1]

        print(f"\n  SEMANTIC ARC")
        print(f"    ΔE:     {first.energy_gap:+.3f} → {last.energy_gap:+.3f}")
        print(f"    Spin:   {first.cosmic_spin:.3f} → {last.cosmic_spin:.3f}")
        print(f"    Temp:   {first.cosmic_temp:.3f} → {last.cosmic_temp:.3f}")
        print(f"    Status: {last.cosmic_status}")

        print(f"\n  PHYSICS ARC")
        print(f"    Throat: {first.core_throat:.3f} → {last.core_throat:.3f}")
        print(f"    Belt:   {first.belt_radius:.3f} → {last.belt_radius:.3f}")
        print(f"    Delta:  {last.closed_loop_delta:.2e}  (target 0)")
        print(f"    Stable: {last.stability:.8f}")

        print(f"\n  COGNITIVE ARC")
        print(f"    Coherence:    {first.coherence:.4f} → {last.coherence:.4f}")
        print(f"    Task load:    {first.task_load:.4f} → {last.task_load:.4f}")
        print(f"    Curv drift:   {first.curvature_drift:.4f} → {last.curvature_drift:.4f}")

        # Safe fallback for short runs that don't reach a phase
        corr_cycle = next(
            (f.cycle for f in self.frames if '🔀' in f.cosmic_status),
            "N/A (not reached)"
        )
        lock_cycle = next(
            (f.cycle for f in self.frames if '🌌' in f.cosmic_status),
            "N/A (not reached)"
        )
        print(f"\n  TRANSITIONS")
        print(f"    Correspondence Region entered: cycle {corr_cycle}")
        print(f"    Cosmic Lock achieved:          cycle {lock_cycle}")

        snap = self.substrate.snapshot_substrate()
        lc   = snap.lifecycle_state
        print(f"\n  SUBSTRATE HEALTH")
        print(f"    Total ticks:        {lc.tick_count}")
        print(f"    Uptime:             {lc.uptime_seconds:.3f}s")
        print(f"    Quarantine events:  {lc.quarantine_events}")
        print(f"    Delta violations:   {lc.delta_violations}")
        print(f"    Healthy:            {lc.healthy}")
        print(f"\n  Telemetry log:  {os.path.abspath(self.log_file)}")
        print("=" * 95)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    cycles = 18
    quiet  = False

    args = sys.argv[1:]
    if '--cycles' in args:
        idx    = args.index('--cycles')
        cycles = int(args[idx + 1])
    if '--quiet' in args:
        quiet = True

    runner = JEDUnifiedRunner(cycles=cycles, quiet=quiet)
    runner.run()

# 💎 Module-level PWC Bridge Functions to satisfy native orchestration layer imports
class MockSnapshot:
    def __init__(self):
        self.radius = 0.5
        self.drift = 0.01
        self.velocity = 0.0

def capture_manifold_snapshot():
    return MockSnapshot()

def configure_gs_regime(regime, safety_profile):
    pass

def apply_curvature_profile(profile, drift_budget):
    pass

def apply_node_policy(policy):
    pass

def step_tordial_nodes():
    pass

def step_gs_engine():
    pass

def run_dual_ring_controller():
    pass

def run_safety_trip_matrix():
    pass
