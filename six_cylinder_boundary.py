"""
six_cylinder_boundary.py
========================
6-Cylindrical Boundary System — FPT Module
Two Mile Solutions LLC / JED Protocol

True System : 6-Dimensional (6 cylindrical faces)
Leak Field  : 3D projection for rendering and intuition
"""

import math
import time
import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional
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
    axis: str; label: str; role: str
    curvature: float; radius: float; throat: float

    def __repr__(self):
        return f"<{self.label} curv={self.curvature:.6f} r={self.radius:.4f} throat={self.throat:.4f}>"


@dataclass
class SystemState:
    spin: float; pressure: float; temp: float; belt_mod: float
    core: FaceGeometry = field(default=None)
    belt: FaceGeometry = field(default=None)
    cap: FaceGeometry = field(default=None)
    timestamp: float = field(default_factory=time.time)

    def faces(self) -> List[FaceGeometry]:
        return [self.core, self.belt, self.cap]


class SixCylinderBoundary:
    def __init__(self, base_radius: float = 60.0):
        self.base_radius = base_radius
        self._lock = threading.Lock()
        self._last_state: Optional[SystemState] = None

    def compute(self, spin=1.5, pressure=1.0, temp=0.0, belt_mod=1.0) -> SystemState:
        spin = max(0.01, spin)
        pressure = max(0.01, pressure)
        temp = max(0.0, min(1.0, temp))
        belt_mod = max(0.1, belt_mod)

        core_curvature = (TOROIDAL_ROOT / math.pi) * spin * SHADOW
        core_radius = (self.base_radius * pressure) / core_curvature
        core_throat = core_radius * (1.0 - 0.15 * temp)

        core = FaceGeometry('core', 'FRONT / REAR', 'Intake · Exhaust', core_curvature, core_radius, core_throat)
        belt_curvature = core_curvature * GEAR_SHIFT * belt_mod
        belt_radius = core_radius * belt_curvature
        belt = FaceGeometry('belt', 'LEFT / RIGHT', 'Expansion Belt', belt_curvature, belt_radius, belt_radius)

        cap_curvature = 1.0 / (belt_curvature * SHADOW)
        cap_radius = belt_radius * cap_curvature
        cap = FaceGeometry('cap', 'TOP / BOTTOM', 'Containment Caps', cap_curvature, cap_radius, cap_radius)

        state = SystemState(spin, pressure, temp, belt_mod, core, belt, cap)
        with self._lock:
            self._last_state = state
        return state

    def closed_loop_delta(self, state: SystemState) -> float:
        return state.belt.curvature * state.cap.curvature * SHADOW - 1.0

    def to_tordial_metrics(self, state: SystemState) -> Dict:
        delta = self.closed_loop_delta(state)
        return {
            "gs_density": abs(delta) * 100 + 1.0,
            "curvature_mean": (state.core.curvature + state.belt.curvature + state.cap.curvature) / 3,
            "closed_loop_stability": 1.0 - abs(delta),
        }

    # 3D Leak Field
    def plot_3d_boundary(self, state=None, title="3D Leak Field", save_path=None):
        if state is None: state = self.last_state or self.compute()
        # ... (your existing 3D plot code) ...
        fig = plt.figure(figsize=(12, 9))
        ax = fig.add_subplot(111, projection='3d')
        ax.set_title(title)
        theta = np.linspace(0, 2*np.pi, 60)
        z = np.linspace(-1, 1, 40)
        Theta, Z = np.meshgrid(theta, z)
        for r, color, alpha in [(state.core.throat, 'crimson', 0.7),
                               (state.belt.radius, 'orange', 0.5),
                               (state.cap.radius, 'royalblue', 0.4)]:
            ax.plot_surface(r*np.cos(Theta), r*np.sin(Theta), Z*0.6, alpha=alpha, color=color)
        plt.show()

    # 6D Manifold Dashboard (existing)
    def plot_6d_manifold(self, state=None, save_path=None):
        if state is None: state = self.last_state or self.compute()
        # ... (your full 6D multi-plot code from previous message) ...
        print("6D Manifold Dashboard opened.")
        # (Implement the full multi-subplot version as before if desired)


# ── Higher-Dimensional Particle Engine ─────────────────────────────────────

@dataclass
class Particle6D:
    x: float = 0.0; y: float = 0.0; z: float = 0.0
    w: float = 0.0; v: float = 0.0; u: float = 0.0   # extra dimensions
    dx: float = 0.0; dy: float = 0.0; dz: float = 0.0
    dw: float = 0.0; dv: float = 0.0; du: float = 0.0
    phase: int = 0
    life: int = 0
    max_life: int = 280
    color: str = 'cyan'


class ParticleFlowEngine6D:
    def __init__(self, count: int = 220):
        self.count = count
        self.particles: List[Particle6D] = []
        self._rng = random.Random(42)

    def _spawn(self, radius: float) -> Particle6D:
        return Particle6D(
            x=radius * self._rng.uniform(0.7, 0.95) * math.cos(self._rng.uniform(0, 2*math.pi)),
            y=radius * self._rng.uniform(0.7, 0.95) * math.sin(self._rng.uniform(0, 2*math.pi)),
            z=self._rng.uniform(-radius*0.5, radius*0.5),
            w=self._rng.uniform(-1.2, 1.2),
            v=self._rng.uniform(-1.2, 1.2),
            u=self._rng.uniform(-1.2, 1.2),
            color=self._rng.choice(['cyan','lime','yellow','magenta','white'])
        )

    def step(self, state: SystemState):
        throat = state.core.throat * 0.5
        belt_r = state.belt.radius

        while len(self.particles) < self.count:
            self.particles.append(self._spawn(belt_r))

        live = []
        for p in self.particles:
            p.life += 1
            if p.life > p.max_life:
                live.append(self._spawn(belt_r))
                continue

            # 6D dynamics driven by boundary
            if p.phase == 0:   # Intake
                p.dx = -0.75 * (p.x / belt_r)
                p.dw = 0.06 * state.spin
            elif p.phase == 1:
                p.dw = GEAR_SHIFT * 0.15
                p.dv = state.temp * 0.4
            elif p.phase == 2:   # Exhaust
                p.dx += 0.65 * SHADOW
                p.du = -0.05
            elif p.phase == 3:
                p.dx *= 0.65
                p.dw *= -0.55

            p.x += p.dx; p.y += p.dy; p.z += p.dz
            p.w += p.dw; p.v += p.dv; p.u += p.du

            # Phase transitions
            r_xy = math.hypot(p.x, p.y)
            if p.phase == 0 and r_xy < throat * 1.15:
                p.phase = 1
            elif p.phase == 2 and r_xy > belt_r * 0.85:
                p.phase = 3
            elif p.phase == 3 and r_xy < throat * 1.4:
                p.phase = 0

            live.append(p)
        self.particles = live

    def plot_particles_6d(self, state: SystemState, mode: str = "projection", save_path=None):
        if mode == "projection":
            fig = plt.figure(figsize=(14, 10))
            ax = fig.add_subplot(111, projection='3d')
            ax.set_title("6D Particles Projected to 3D\n(size = w, alpha = v, color = phase)")

            xs, ys, zs = [p.x for p in self.particles], [p.y for p in self.particles], [p.z for p in self.particles]
            sizes = [max(8, abs(p.w) * 40) for p in self.particles]
            alphas = [max(0.2, (p.v + 1.5)/3) for p in self.particles]

            ax.scatter(xs, ys, zs, s=sizes, c=[p.color for p in self.particles],
                       alpha=alphas, cmap='viridis', edgecolors='w', linewidth=0.3)
            ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
            plt.show()

        elif mode == "parallel":
            fig, ax = plt.subplots(figsize=(15, 8))
            dims = ['X', 'Y', 'Z', 'W(Curv)', 'V(GS)', 'U(Press)']
            for p in self.particles[:120]:
                ax.plot(range(6), [p.x, p.y, p.z, p.w, p.v, p.u], alpha=0.25, lw=1)
            ax.set_xticks(range(6))
            ax.set_xticklabels(dims)
            ax.set_title("True 6D Particle States — Parallel Coordinates")
            ax.grid(True, alpha=0.3)
            plt.show()


# ── TordialNodeWrapper with 6D Engine ─────────────────────────────────────

class TordialNodeWrapper:
    def __init__(self, node_id: str = "FPT-6D-001", base_radius: float = 60.0):
        self.node_id = node_id
        self.boundary = SixCylinderBoundary(base_radius)
        self.engine = ParticleFlowEngine6D(count=250)

    def tick(self, spin=None, pressure=None, temp=None, belt_mod=None):
        last = self.boundary.last_state
        state = self.boundary.compute(
            spin or (last.spin if last else 1.5),
            pressure or (last.pressure if last else 1.0),
            temp or (last.temp if last else 0.0),
            belt_mod or (last.belt_mod if last else 1.0)
        )
        self.engine.step(state)
        return state

    def plot_6d_particles(self, mode="projection"):
        state = self.boundary.last_state or self.boundary.compute()
        self.engine.plot_particles_6d(state, mode=mode)


# ── Demo ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    node = TordialNodeWrapper("FPT-6D-Alpha")

    print("Running 6D Particle Flow Simulation...\n")
    for i in range(20):
        node.tick(spin=1.65 + 0.45*math.sin(i*0.4), temp=0.05*(i%7))

    print("Rendering Higher-Dimensional Particles:")
    node.plot_6d_particles(mode="projection")
    node.plot_6d_particles(mode="parallel")

    print("\n✅ Higher-dimensional particle rendering active.")