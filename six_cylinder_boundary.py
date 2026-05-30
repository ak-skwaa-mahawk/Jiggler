"""
six_cylinder_boundary.py
========================
6-Cylindrical Boundary System — FPT Module
Two Mile Solutions LLC / JED Protocol

Constants
---------
TOROIDAL_ROOT : 3.1730059    — toroidal geometry root (calibrated for GEAR_SHIFT=1.02)
GEAR_SHIFT    : 1.02         — universal stabilizer across all 6 faces (fixed)
SHADOW        : 1.03         — shadow constant (dimensional remainder)
"""

import math
import time
import random
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import threading

# ── Constants ────────────────────────────────────────────────────────────────
TOROIDAL_ROOT = 3.1730059     # calibrated for GEAR_SHIFT = 1.02
GEAR_SHIFT    = 1.02          # ← UNIVERSAL STABILIZER (fixed / immutable)
SHADOW        = 1.03          # shadow constant (dimensional remainder)


@dataclass
class FaceGeometry:
    """Computed boundary state for one cylindrical face pair."""
    axis:       str
    label:      str
    role:       str
    curvature:  float
    radius:     float
    throat:     float

    def __repr__(self):
        return (
            f"<{self.label}  curvature={self.curvature:.6f}  "
            f"radius={self.radius:.4f}  throat={self.throat:.4f}>"
        )


@dataclass
class SystemState:
    """Full 6-face boundary state at one instant."""
    spin:      float
    pressure:  float
    temp:      float
    belt_mod:  float
    core:      FaceGeometry = field(default=None)
    belt:      FaceGeometry = field(default=None)
    cap:       FaceGeometry = field(default=None)
    timestamp: float = field(default_factory=time.time)

    def faces(self) -> List[FaceGeometry]:
        return [self.core, self.belt, self.cap]

    def summary(self) -> str:
        lines = [
            f"{'='*60}",
            f"  6-CYLINDRICAL BOUNDARY STATE",
            f"  spin={self.spin:.3f}  pressure={self.pressure:.3f}  "
            f"temp={self.temp:.3f}  belt_mod={self.belt_mod:.3f}",
            f"{'─'*60}",
        ]
        for f in self.faces():
            lines.append(
                f"  {f.label:<14}  curv={f.curvature:.6f}  "
                f"r={f.radius:.4f}  throat={f.throat:.4f}"
            )
        lines.append(f"{'='*60}")
        return "\n".join(lines)


class SixCylinderBoundary:
    """Core 6-face cylindrical boundary solver."""

    def __init__(self, base_radius: float = 60.0):
        self.base_radius = base_radius
        self._lock = threading.Lock()
        self._last_state: Optional[SystemState] = None

    def compute(
        self,
        spin:     float = 1.5,
        pressure: float = 1.0,
        temp:     float = 0.0,
        belt_mod: float = 1.0,
    ) -> SystemState:
        spin     = max(0.01, spin)
        pressure = max(0.01, pressure)
        temp     = max(0.0, min(1.0, temp))
        belt_mod = max(0.1, belt_mod)

        # Core Axis (Front / Rear)
        core_curvature = (TOROIDAL_ROOT / math.pi) * spin * SHADOW
        core_radius    = (self.base_radius * pressure) / core_curvature
        core_throat    = core_radius * (1.0 - 0.15 * temp)

        core = FaceGeometry('core', 'FRONT / REAR', 'Intake · Exhaust',
                            core_curvature, core_radius, core_throat)

        # Expansion Belt (Left / Right)
        belt_curvature = core_curvature * GEAR_SHIFT * belt_mod
        belt_radius    = core_radius * belt_curvature

        belt = FaceGeometry('belt', 'LEFT / RIGHT', 'Expansion Belt',
                            belt_curvature, belt_radius, belt_radius)

        # Containment Caps (Top / Bottom)
        cap_curvature = 1.0 / (belt_curvature * SHADOW)
        cap_radius    = belt_radius * cap_curvature

        cap = FaceGeometry('cap', 'TOP / BOTTOM', 'Containment Caps',
                           cap_curvature, cap_radius, cap_radius)

        state = SystemState(
            spin=spin, pressure=pressure, temp=temp, belt_mod=belt_mod,
            core=core, belt=belt, cap=cap
        )

        with self._lock:
            self._last_state = state

        return state

    def flux_balance(self, state: SystemState) -> dict:
        intake_flux  = state.core.throat * TOROIDAL_ROOT * state.spin
        exhaust_flux = intake_flux * SHADOW
        belt_density = state.belt.radius / (state.core.throat + 1e-9) * GEAR_SHIFT
        cap_return   = 1.0 / (belt_density * SHADOW + 1e-9)

        return {
            'intake_flux':  round(intake_flux,  6),
            'exhaust_flux': round(exhaust_flux, 6),
            'belt_density': round(belt_density, 6),
            'cap_return':   round(cap_return,   6),
        }

    def throat_velocity(self, state: SystemState) -> float:
        return (state.spin * TOROIDAL_ROOT * GEAR_SHIFT) / (state.core.throat + 1e-9)

    def closed_loop_delta(self, state: SystemState) -> float:
        """Should be extremely close to 0.0"""
        return state.belt.curvature * state.cap.curvature * SHADOW - 1.0

    def sweep_spin(self, spin_range: Tuple[float, float] = (0.1, 5.0), steps: int = 10, **kwargs):
        lo, hi = spin_range
        return [self.compute(spin=lo + (hi - lo) * i / max(steps - 1, 1), **kwargs)
                for i in range(steps)]

    def sweep_temp(self, temp_range: Tuple[float, float] = (0.0, 1.0), steps: int = 10, **kwargs):
        lo, hi = temp_range
        return [self.compute(temp=lo + (hi - lo) * i / max(steps - 1, 1), **kwargs)
                for i in range(steps)]

    @property
    def last_state(self) -> Optional[SystemState]:
        with self._lock:
            return self._last_state


# Particle Flow Engine (unchanged except improved randomness)
@dataclass
class Particle:
    r:        float
    theta:    float
    dr:       float = 0.0
    dtheta:   float = 0.0
    phase:    int   = 0
    life:     int   = 0
    max_life: int   = 200

    @property
    def x(self) -> float: return self.r * math.cos(self.theta)
    @property
    def y(self) -> float: return self.r * math.sin(self.theta)
    @property
    def phase_name(self) -> str:
        return ['INTAKE', 'TRANSIT', 'EXHAUST', 'RETURN'][self.phase]


class ParticleFlowEngine:
    def __init__(self, count: int = 80):
        self.count = count
        self.particles: List[Particle] = []
        self._rng = random.Random(42)  # reproducible but varied

    def _spawn(self, belt_radius: float) -> Particle:
        theta = (len(self.particles) / max(self.count, 1)) * 2 * math.pi
        theta += self._rng.uniform(0, 2 * math.pi)
        return Particle(
            r=belt_radius * 0.95,
            theta=theta,
            max_life=180 + self._rng.randint(0, 120),
        )

    # ... rest of step() and phase_counts() unchanged ...


if __name__ == '__main__':
    solver = SixCylinderBoundary()
    engine = ParticleFlowEngine(count=60)

    print("\n6-CYLINDRICAL BOUNDARY SYSTEM — FPT Module")
    print(f"TOROIDAL_ROOT={TOROIDAL_ROOT}  GEAR_SHIFT={GEAR_SHIFT}  SHADOW={SHADOW}\n")

    state = solver.compute(spin=1.5, pressure=1.0, temp=0.0, belt_mod=1.0)
    print(state.summary())

    flux = solver.flux_balance(state)
    print(f"\n  Flux Balance:")
    for k, v in flux.items():
        print(f"    {k:<16} {v}")

    print(f"\n  Throat Velocity  : {solver.throat_velocity(state):.6f}")
    print(f"  Closed-Loop Delta: {solver.closed_loop_delta(state):.10f}  (target: 0)")

    print("\nModule ready for FPT / Tordial-GS integration.\n")