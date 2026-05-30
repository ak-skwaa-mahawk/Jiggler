"""
six_cylinder_boundary.py
========================
6-Cylindrical Boundary System — FPT Module
Two Mile Solutions LLC / JED Protocol

Constants
---------
TOROIDAL_ROOT : 3.20442315   — toroidal geometry root
GEAR_SHIFT    : 1.04         — universal stabilizer across all 6 faces
SHADOW        : 1.03         — shadow constant (dimensional remainder)

Axis pairs
----------
Front / Rear  — Core Axis      (intake / exhaust cylinders)
Left  / Right — Expansion Belt (centrifugal ring)
Top   / Bottom— Containment Caps (pressure return)
"""

import math
import time
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import threading

# ── Constants ────────────────────────────────────────────────────────────────
TOROIDAL_ROOT = 3.20442315
GEAR_SHIFT    = 1.04
SHADOW        = 1.03

# ── Face geometry ─────────────────────────────────────────────────────────────

@dataclass
class FaceGeometry:
    """Computed boundary state for one cylindrical face pair."""
    axis:       str           # 'core' | 'belt' | 'cap'
    label:      str           # human label
    role:       str           # functional description
    curvature:  float
    radius:     float
    throat:     float         # narrowest cross-section (core) or effective radius

    def __repr__(self):
        return (
            f"<{self.label}  curvature={self.curvature:.6f}  "
            f"radius={self.radius:.4f}  throat={self.throat:.4f}>"
        )


@dataclass
class SystemState:
    """Full 6-face boundary state at one instant."""
    spin:     float
    pressure: float
    temp:     float
    belt_mod: float
    core:     FaceGeometry = field(default=None)
    belt:     FaceGeometry = field(default=None)
    cap:      FaceGeometry = field(default=None)
    timestamp: float = field(default_factory=time.time)

    def faces(self) -> List[FaceGeometry]:
        return [self.core, self.belt, self.cap]

    def summary(self) -> str:
        lines = [
            f"{'='*55}",
            f"  6-CYLINDRICAL BOUNDARY STATE",
            f"  spin={self.spin:.3f}  pressure={self.pressure:.3f}  "
            f"temp={self.temp:.3f}  belt_mod={self.belt_mod:.3f}",
            f"{'─'*55}",
        ]
        for f in self.faces():
            lines.append(
                f"  {f.label:<14}  curv={f.curvature:.6f}  "
                f"r={f.radius:.4f}  throat={f.throat:.4f}"
            )
        lines.append(f"{'='*55}")
        return "\n".join(lines)


# ── Core solver ───────────────────────────────────────────────────────────────

class SixCylinderBoundary:
    """
    Computes the 6-face cylindrical boundary state from system inputs.

    All three face pairs are derived from the same toroidal root,
    so any change in one axis propagates through the other two
    automatically — closed-loop by construction.

    Parameters
    ----------
    base_radius : float
        Scaling reference for radius calculations (default 60.0).
    """

    def __init__(self, base_radius: float = 60.0):
        self.base_radius = base_radius
        self._lock = threading.Lock()
        self._last_state: Optional[SystemState] = None

    # ── Primary compute ───────────────────────────────────────────────────────

    def compute(
        self,
        spin:     float = 1.5,
        pressure: float = 1.0,
        temp:     float = 0.0,
        belt_mod: float = 1.0,
    ) -> SystemState:
        """
        Compute all 6 face geometries from current system parameters.

        Parameters
        ----------
        spin     : rotational velocity scalar (0.1 – 5.0)
        pressure : system pressure scalar    (0.2 – 2.0)
        temp     : temperature spike 0-1     (0.0 – 1.0)
        belt_mod : expansion belt modifier   (0.5 – 2.0)

        Returns
        -------
        SystemState with core / belt / cap FaceGeometry filled.
        """
        spin     = max(0.01, spin)
        pressure = max(0.01, pressure)
        temp     = max(0.0, min(1.0, temp))
        belt_mod = max(0.1, belt_mod)

        # ── Core Axis (Front / Rear) ─────────────────────────────────────────
        # Intake and exhaust cylinders.
        # Curvature driven by toroidal root × spin × shadow constant.
        core_curvature = (TOROIDAL_ROOT / math.pi) * spin * SHADOW
        core_radius    = (self.base_radius * pressure) / core_curvature
        # Throat contracts under heat (matter compresses)
        core_throat    = core_radius * (1.0 - 0.15 * temp)

        core = FaceGeometry(
            axis='core',
            label='FRONT / REAR',
            role='Intake · Exhaust',
            curvature=core_curvature,
            radius=core_radius,
            throat=core_throat,
        )

        # ── Expansion Belt (Left / Right) ─────────────────────────────────────
        # Centrifugal ring — gear shift amplifies outward expansion.
        belt_curvature = core_curvature * GEAR_SHIFT * belt_mod
        belt_radius    = core_radius    * belt_curvature

        belt = FaceGeometry(
            axis='belt',
            label='LEFT / RIGHT',
            role='Expansion Belt',
            curvature=belt_curvature,
            radius=belt_radius,
            throat=belt_radius,   # belt throat = full radius (open ring)
        )

        # ── Containment Caps (Top / Bottom) ───────────────────────────────────
        # Inverse deformation — automatically compensates belt expansion.
        # Shadow constant keeps the closed-loop balanced.
        cap_curvature = 1.0 / (belt_curvature * SHADOW)
        cap_radius    = belt_radius * cap_curvature

        cap = FaceGeometry(
            axis='cap',
            label='TOP / BOTTOM',
            role='Containment Caps',
            curvature=cap_curvature,
            radius=cap_radius,
            throat=cap_radius,
        )

        state = SystemState(
            spin=spin, pressure=pressure, temp=temp, belt_mod=belt_mod,
            core=core, belt=belt, cap=cap,
        )

        with self._lock:
            self._last_state = state

        return state

    # ── Derived metrics ───────────────────────────────────────────────────────

    def flux_balance(self, state: SystemState) -> dict:
        """
        Compute intake/exhaust flux and cap return force from a state.
        Uses toroidal root and gear shift as the scaling operators.
        """
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
        """
        Particle velocity at the core throat.
        v = spin × TOROIDAL_ROOT × GEAR_SHIFT / throat_radius
        """
        return (state.spin * TOROIDAL_ROOT * GEAR_SHIFT) / (state.core.throat + 1e-9)

    def closed_loop_delta(self, state: SystemState) -> float:
        """
        Harmony metric: deviation from perfect closed-loop balance.
        Target = 0.0 (system fully self-compensating).
        delta = belt_curvature × cap_curvature × SHADOW − 1
        """
        return state.belt.curvature * state.cap.curvature * SHADOW - 1.0

    # ── Sweep utilities ───────────────────────────────────────────────────────

    def sweep_spin(
        self,
        spin_range: Tuple[float, float] = (0.1, 5.0),
        steps: int = 10,
        **kwargs,
    ) -> List[SystemState]:
        """Return states across a spin sweep, all other params fixed."""
        lo, hi = spin_range
        results = []
        for i in range(steps):
            s = lo + (hi - lo) * i / max(steps - 1, 1)
            results.append(self.compute(spin=s, **kwargs))
        return results

    def sweep_temp(
        self,
        temp_range: Tuple[float, float] = (0.0, 1.0),
        steps: int = 10,
        **kwargs,
    ) -> List[SystemState]:
        """Return states across a temperature sweep."""
        lo, hi = temp_range
        results = []
        for i in range(steps):
            t = lo + (hi - lo) * i / max(steps - 1, 1)
            results.append(self.compute(temp=t, **kwargs))
        return results

    @property
    def last_state(self) -> Optional[SystemState]:
        with self._lock:
            return self._last_state


# ── Particle flow model ───────────────────────────────────────────────────────

@dataclass
class Particle:
    """Single particle in the 6-cylinder flow circuit."""
    r:      float          # radial position
    theta:  float          # angular position (radians)
    dr:     float = 0.0    # radial velocity
    dtheta: float = 0.0    # angular velocity
    phase:  int   = 0      # 0=intake 1=transit 2=exhaust 3=return
    life:   int   = 0
    max_life: int = 200

    @property
    def x(self) -> float:
        return self.r * math.cos(self.theta)

    @property
    def y(self) -> float:
        return self.r * math.sin(self.theta)

    @property
    def phase_name(self) -> str:
        return ['INTAKE', 'TRANSIT', 'EXHAUST', 'RETURN'][self.phase]


class ParticleFlowEngine:
    """
    Simulates particle flow through the 6-cylinder boundary geometry.

    Particles cycle through four phases:
        INTAKE  → spiral inward to core throat
        TRANSIT → compress and spin inside throat
        EXHAUST → jet outward to belt boundary
        RETURN  → cap deflects back to intake

    Parameters
    ----------
    count : int — number of particles to maintain
    """

    def __init__(self, count: int = 80):
        self.count = count
        self.particles: List[Particle] = []

    def _spawn(self, belt_radius: float) -> Particle:
        theta = (len(self.particles) / max(self.count, 1)) * 2 * math.pi
        theta += (hash(id(object())) % 1000) / 1000.0 * 2 * math.pi  # jitter
        return Particle(
            r=belt_radius * 0.95,
            theta=theta,
            max_life=180 + (id(object()) % 120),
        )

    def step(self, state: SystemState) -> List[Particle]:
        """
        Advance all particles one time step using the current SystemState.
        Returns the updated particle list.
        """
        throat_r = state.core.throat * 0.5
        belt_r   = state.belt.radius

        # Maintain count
        while len(self.particles) < self.count:
            self.particles.append(self._spawn(belt_r))

        live = []
        for p in self.particles:
            p.life += 1
            if p.life > p.max_life:
                live.append(self._spawn(belt_r))
                continue

            if p.phase == 0:   # INTAKE — spiral inward
                spd    = 0.6 + state.spin * 0.4
                p.dr   = -spd * (p.r / belt_r)
                p.dtheta = spd * TOROIDAL_ROOT * 0.08
                p.r    += p.dr
                p.theta += p.dtheta
                if p.r <= throat_r * 1.1:
                    p.phase = 1

            elif p.phase == 1:  # TRANSIT — compress in throat
                compress = 1.0 + state.temp * 2.5
                p.dtheta = GEAR_SHIFT * compress * 0.18
                p.theta += p.dtheta
                p.r = throat_r * (0.85 + 0.15 * math.sin(p.life * 0.4))
                if p.life % max(1, int(15 / (state.spin * 0.5 + 0.5))) == 0:
                    p.phase = 2

            elif p.phase == 2:  # EXHAUST — jet outward
                jet_spd = (1.0 + state.spin * 0.5) * SHADOW
                p.dr    = jet_spd * 0.9
                p.dtheta = 0.04
                p.r    += p.dr
                p.theta += p.dtheta
                if p.r >= belt_r * 0.9:
                    p.phase = 3

            elif p.phase == 3:  # RETURN — cap arc back
                p.dr    = -(0.3 + state.spin * 0.15)
                p.dtheta = GEAR_SHIFT * 0.06
                p.r    += p.dr
                p.theta += p.dtheta
                if p.r <= throat_r * 1.4:
                    p.phase = 0
                    p.r = belt_r * 0.95

            # Clamp
            p.r = max(throat_r * 0.4, min(belt_r * 1.15, p.r))
            live.append(p)

        self.particles = live
        return self.particles

    def phase_counts(self) -> dict:
        counts = {'INTAKE': 0, 'TRANSIT': 0, 'EXHAUST': 0, 'RETURN': 0}
        for p in self.particles:
            counts[p.phase_name] += 1
        return counts


# ── Quick demo ────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    solver  = SixCylinderBoundary()
    engine  = ParticleFlowEngine(count=60)

    print("\n6-CYLINDRICAL BOUNDARY SYSTEM — FPT Module")
    print(f"TOROIDAL_ROOT={TOROIDAL_ROOT}  GEAR_SHIFT={GEAR_SHIFT}  SHADOW={SHADOW}\n")

    # ── Baseline state ────────────────────────────────────────────────────────
    state = solver.compute(spin=1.5, pressure=1.0, temp=0.0, belt_mod=1.0)
    print(state.summary())

    flux = solver.flux_balance(state)
    print(f"\n  Flux Balance:")
    for k, v in flux.items():
        print(f"    {k:<16} {v}")

    print(f"\n  Throat Velocity  : {solver.throat_velocity(state):.6f}")
    print(f"  Closed-Loop Delta: {solver.closed_loop_delta(state):.8f}  (target: 0)")

    # ── Temp spike response ───────────────────────────────────────────────────
    print("\n── Temp Spike Sweep (spin=2.0, belt_mod=1.2) ──")
    for s in solver.sweep_temp(steps=5, spin=2.0, belt_mod=1.2):
        delta = solver.closed_loop_delta(s)
        print(
            f"  temp={s.temp:.2f}  throat={s.core.throat:.4f}  "
            f"belt_r={s.belt.radius:.4f}  cap_r={s.cap.radius:.4f}  "
            f"delta={delta:.8f}"
        )

    # ── Particle sim (5 steps) ────────────────────────────────────────────────
    print("\n── Particle Flow (5 steps) ──")
    for step in range(5):
        engine.step(state)
        counts = engine.phase_counts()
        print(f"  step {step+1}: {counts}")

    print("\nModule ready for FPT integration.\n")
