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
from typing import List, Tuple, Optional, Dict
import threading

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


# ── Constants ────────────────────────────────────────────────────────────────
TOROIDAL_ROOT = 3.1730059
GEAR_SHIFT    = 1.02          # ← UNIVERSAL STABILIZER (fixed)
SHADOW        = 1.03


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
        return f"<{self.label} curv={self.curvature:.6f} r={self.radius:.4f} throat={self.throat:.4f}>"


@dataclass
class SystemState:
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
        lines = [f"{'='*68}", "  6-CYLINDRICAL BOUNDARY STATE", 
                 f"  spin={self.spin:.3f}  pressure={self.pressure:.3f}  "
                 f"temp={self.temp:.3f}  belt_mod={self.belt_mod:.3f}",
                 f"{'─'*68}"]
        for f in self.faces():
            lines.append(f"  {f.label:<14} curv={f.curvature:.6f}  r={f.radius:.4f}  throat={f.throat:.4f}")
        lines.append(f"{'='*68}")
        return "\n".join(lines)


class SixCylinderBoundary:
    def __init__(self, base_radius: float = 60.0):
        self.base_radius = base_radius
        self._lock = threading.Lock()
        self._last_state: Optional[SystemState] = None

    def compute(self, spin: float = 1.5, pressure: float = 1.0,
                temp: float = 0.0, belt_mod: float = 1.0) -> SystemState:
        
        spin = max(0.01, spin)
        pressure = max(0.01, pressure)
        temp = max(0.0, min(1.0, temp))
        belt_mod = max(0.1, belt_mod)

        core_curvature = (TOROIDAL_ROOT / math.pi) * spin * SHADOW
        core_radius = (self.base_radius * pressure) / core_curvature
        core_throat = core_radius * (1.0 - 0.15 * temp)

        core = FaceGeometry('core', 'FRONT / REAR', 'Intake · Exhaust',
                            core_curvature, core_radius, core_throat)

        belt_curvature = core_curvature * GEAR_SHIFT * belt_mod
        belt_radius = core_radius * belt_curvature

        belt = FaceGeometry('belt', 'LEFT / RIGHT', 'Expansion Belt',
                            belt_curvature, belt_radius, belt_radius)

        cap_curvature = 1.0 / (belt_curvature * SHADOW)
        cap_radius = belt_radius * cap_curvature

        cap = FaceGeometry('cap', 'TOP / BOTTOM', 'Containment Caps',
                           cap_curvature, cap_radius, cap_radius)

        state = SystemState(spin=spin, pressure=pressure, temp=temp,
                            belt_mod=belt_mod, core=core, belt=belt, cap=cap)

        with self._lock:
            self._last_state = state
        return state

    def flux_balance(self, state: SystemState) -> dict:
        intake_flux = state.core.throat * TOROIDAL_ROOT * state.spin
        exhaust_flux = intake_flux * SHADOW
        belt_density = state.belt.radius / (state.core.throat + 1e-9) * GEAR_SHIFT
        cap_return = 1.0 / (belt_density * SHADOW + 1e-9)
        return {
            'intake_flux': round(intake_flux, 6),
            'exhaust_flux': round(exhaust_flux, 6),
            'belt_density': round(belt_density, 6),
            'cap_return': round(cap_return, 6),
        }

    def throat_velocity(self, state: SystemState) -> float:
        return (state.spin * TOROIDAL_ROOT * GEAR_SHIFT) / (state.core.throat + 1e-9)

    def closed_loop_delta(self, state: SystemState) -> float:
        return state.belt.curvature * state.cap.curvature * SHADOW - 1.0

    def to_tordial_metrics(self, state: SystemState) -> Dict:
        delta = self.closed_loop_delta(state)
        return {
            "gs_density": abs(delta) * 100 + 1.0,
            "curvature_mean": (state.core.curvature + state.belt.curvature + state.cap.curvature) / 3,
            "throat_velocity": self.throat_velocity(state),
            "closed_loop_stability": 1.0 - abs(delta),
            "flux_intake": self.flux_balance(state)['intake_flux'],
            "face_radii": {"core": state.core.radius, "belt": state.belt.radius, "cap": state.cap.radius}
        }

    def plot_3d_boundary(self, state: Optional[SystemState] = None, title="6-Cylinder Toroidal Boundary", save_path=None):
        if state is None:
            state = self.last_state or self.compute()

        fig = plt.figure(figsize=(12, 9))
        ax = fig.add_subplot(111, projection='3d')
        ax.set_title(title)

        theta = np.linspace(0, 2*np.pi, 60)
        z = np.linspace(-1, 1, 40)
        Theta, Z = np.meshgrid(theta, z)

        core_r = state.core.throat
        belt_r = state.belt.radius
        cap_r = state.cap.radius

        ax.plot_surface(core_r * np.cos(Theta), core_r * np.sin(Theta), Z*0.8,
                        alpha=0.7, color='crimson')
        ax.plot_surface(belt_r * np.cos(Theta), belt_r * np.sin(Theta), Z*0.6,
                        alpha=0.5, color='orange')
        ax.plot_surface(cap_r * np.cos(Theta), cap_r * np.sin(Theta), Z*0.5,
                        alpha=0.4, color='royalblue')

        ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
        if save_path: plt.savefig(save_path, dpi=300)
        plt.show()

    @property
    def last_state(self) -> Optional[SystemState]:
        with self._lock: return self._last_state


# ── Particle Flow Engine (Full 3D) ─────────────────────────────────────────

@dataclass
class Particle:
    r:        float
    theta:    float
    z:        float = 0.0
    dr:       float = 0.0
    dtheta:   float = 0.0
    dz:       float = 0.0
    phase:    int   = 0
    life:     int   = 0
    max_life: int   = 200
    color:    str   = 'cyan'

    @property
    def x(self) -> float: return self.r * math.cos(self.theta)
    @property
    def y(self) -> float: return self.r * math.sin(self.theta)
    @property
    def phase_name(self) -> str:
        return ['INTAKE', 'TRANSIT', 'EXHAUST', 'RETURN'][self.phase]


class ParticleFlowEngine:
    def __init__(self, count: int = 150):
        self.count = count
        self.particles: List[Particle] = []
        self._rng = random.Random(42)

    def _spawn(self, belt_radius: float) -> Particle:
        return Particle(
            r=belt_radius * 0.95,
            theta=self._rng.uniform(0, 2 * math.pi),
            z=self._rng.uniform(-0.9, 0.9),
            max_life=180 + self._rng.randint(60, 180),
            color=self._rng.choice(['cyan', 'lime', 'yellow', 'magenta', 'white'])
        )

    def step(self, state: SystemState) -> List[Particle]:
        throat_r = state.core.throat * 0.5
        belt_r = state.belt.radius

        while len(self.particles) < self.count:
            self.particles.append(self._spawn(belt_r))

        live = []
        for p in self.particles:
            p.life += 1
            if p.life > p.max_life:
                live.append(self._spawn(belt_r))
                continue

            # Phase logic (same as before, with z movement)
            if p.phase == 0:   # INTAKE
                spd = 0.6 + state.spin * 0.4
                p.dr = -spd * (p.r / belt_r)
                p.dtheta = spd * TOROIDAL_ROOT * 0.08
                p.dz = 0.03 * math.sin(p.life * 0.15)
                p.r += p.dr; p.theta += p.dtheta; p.z += p.dz
                if p.r <= throat_r * 1.12: p.phase = 1

            elif p.phase == 1:  # TRANSIT
                compress = 1.0 + state.temp * 2.5
                p.dtheta = GEAR_SHIFT * compress * 0.18
                p.dz = 0.06 * math.cos(p.life * 0.4)
                p.theta += p.dtheta; p.z += p.dz
                p.r = throat_r * (0.85 + 0.13 * math.sin(p.life * 0.45))
                if p.life % max(1, int(12 / (state.spin + 0.3))) == 0: p.phase = 2

            elif p.phase == 2:  # EXHAUST
                jet = (1.0 + state.spin * 0.5) * SHADOW
                p.dr = jet * 0.9
                p.dtheta = 0.045
                p.dz = 0.04 * math.sin(p.life)
                p.r += p.dr; p.theta += p.dtheta; p.z += p.dz
                if p.r >= belt_r * 0.9: p.phase = 3

            elif p.phase == 3:  # RETURN
                p.dr = -(0.35 + state.spin * 0.14)
                p.dtheta = GEAR_SHIFT * 0.07
                p.dz = -0.05 * math.cos(p.life * 0.25)
                p.r += p.dr; p.theta += p.dtheta; p.z += p.dz
                if p.r <= throat_r * 1.4:
                    p.phase = 0
                    p.r = belt_r * 0.94

            p.r = max(throat_r * 0.3, min(belt_r * 1.25, p.r))
            p.z = max(-1.3, min(1.3, p.z))
            live.append(p)

        self.particles = live
        return self.particles

    def phase_counts(self) -> dict:
        counts = {'INTAKE':0, 'TRANSIT':0, 'EXHAUST':0, 'RETURN':0}
        for p in self.particles:
            counts[p.phase_name] += 1
        return counts

    def plot_3d_particles(self, state: SystemState, title="Particle Flow in 6-Cylinder Boundary", save_path=None):
        fig = plt.figure(figsize=(13, 10))
        ax = fig.add_subplot(111, projection='3d')
        ax.set_title(title)

        xs = [p.x for p in self.particles]
        ys = [p.y for p in self.particles]
        zs = [p.z for p in self.particles]
        colors = [p.color for p in self.particles]

        ax.scatter(xs, ys, zs, c=colors, s=20, alpha=0.85)

        theta = np.linspace(0, 2*np.pi, 100)
        for r, c in [(state.core.throat, 'red'), (state.belt.radius, 'orange'), (state.cap.radius, 'blue')]:
            ax.plot(r*np.cos(theta), r*np.sin(theta), zs=0, color=c, alpha=0.6, lw=1.5)

        ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
        if save_path: plt.savefig(save_path, dpi=300)
        plt.show()


# ── TordialNode Wrapper ─────────────────────────────────────────────────────

@dataclass
class TordialNodeState:
    node_id: str
    spin: float = 1.5
    pressure: float = 1.0
    temp: float = 0.0
    belt_mod: float = 1.0
    gs_density: float = 1.0
    curvature: float = 1.0
    stability: float = 1.0
    timestamp: float = field(default_factory=time.time)


class TordialNodeWrapper:
    def __init__(self, node_id: str = "FPT-6Cyl-001", base_radius: float = 60.0):
        self.node_id = node_id
        self.boundary = SixCylinderBoundary(base_radius)
        self.engine = ParticleFlowEngine(count=150)
        self.state_history: List[TordialNodeState] = []

    def tick(self, spin=None, pressure=None, temp=None, belt_mod=None, **kwargs):
        last = self.boundary.last_state
        state = self.boundary.compute(
            spin=spin or (last.spin if last else 1.5),
            pressure=pressure or (last.pressure if last else 1.0),
            temp=temp or (last.temp if last else 0.0),
            belt_mod=belt_mod or (last.belt_mod if last else 1.0)
        )

        self.engine.step(state)
        metrics = self.boundary.to_tordial_metrics(state)
        delta = self.boundary.closed_loop_delta(state)

        node_state = TordialNodeState(
            node_id=self.node_id,
            spin=state.spin,
            pressure=state.pressure,
            temp=state.temp,
            belt_mod=state.belt_mod,
            gs_density=metrics["gs_density"],
            curvature=metrics["curvature_mean"],
            stability=metrics["closed_loop_stability"]
        )
        self.state_history.append(node_state)

        return {
            "node_id": self.node_id,
            "system_state": state,
            "tordial_metrics": metrics,
            "closed_loop_delta": delta,
            "throat_velocity": self.boundary.throat_velocity(state),
            "phase_counts": self.engine.phase_counts(),
            "stability": node_state.stability
        }

    def plot(self, mode: str = "both"):
        state = self.boundary.last_state or self.boundary.compute()
        if mode in ["boundary", "both"]:
            self.boundary.plot_3d_boundary(state)
        if mode in ["particles", "both"]:
            self.engine.plot_3d_particles(state)


# ── Demo ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    node = TordialNodeWrapper(node_id="FPT-Node-Alpha")

    print("Running Tordial 6-Cylinder Node...\n")
    for i in range(10):
        result = node.tick(
            spin=1.7 + 0.4 * math.sin(i * 0.5),
            temp=0.15 * (i % 4)
        )
        print(f"Cycle {i+1:2d} | Δ={result['closed_loop_delta']:.2e} | "
              f"Stability={result['stability']:.5f} | GS={result['tordial_metrics']['gs_density']:.2f}")

    node.plot(mode="both")
    print("\n✅ TordialNodeWrapper successfully integrated.")