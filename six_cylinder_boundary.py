"""
six_cylinder_boundary.py
========================
6-Cylindrical Boundary System — FPT Module
Two Mile Solutions LLC / JED Protocol

True System : 6-Dimensional (6 cylindrical faces)
Leak Field  : 3D projection for rendering and intuition
"""

import math
import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


# ── Constants ────────────────────────────────────────────────────────────────
TOROIDAL_ROOT = 3.1730059
GEAR_SHIFT    = 1.02          # ← UNIVERSAL STABILIZER (fixed)
SHADOW        = 1.03


@dataclass
class FaceGeometry:
    axis: str
    label: str
    role: str
    curvature: float
    radius: float
    throat: float

    def __repr__(self):
        return f"<{self.label} curv={self.curvature:.6f} r={self.radius:.4f} throat={self.throat:.4f}>"


@dataclass
class SystemState:
    spin: float
    pressure: float
    temp: float
    belt_mod: float
    core: FaceGeometry = field(default=None)
    belt: FaceGeometry = field(default=None)
    cap: FaceGeometry = field(default=None)
    timestamp: float = field(default_factory=lambda: time.time())


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

    @property
    def last_state(self) -> Optional[SystemState]:
        with self._lock:
            return self._last_state


# ── 6D Particle Engine with PCA ─────────────────────────────────────────────

@dataclass
class Particle6D:
    x: float = 0.0; y: float = 0.0; z: float = 0.0
    w: float = 0.0; v: float = 0.0; u: float = 0.0
    dx: float = 0.0; dy: float = 0.0; dz: float = 0.0
    dw: float = 0.0; dv: float = 0.0; du: float = 0.0
    phase: int = 0
    life: int = 0
    max_life: int = 280
    color: str = 'cyan'


class ParticleFlowEngine6D:
    def __init__(self, count: int = 280):
        self.count = count
        self.particles: List[Particle6D] = []
        self._rng = random.Random(42)

    def _spawn(self, radius: float) -> Particle6D:
        return Particle6D(
            x=radius * self._rng.uniform(0.6, 0.98) * math.cos(self._rng.uniform(0, 2*math.pi)),
            y=radius * self._rng.uniform(0.6, 0.98) * math.sin(self._rng.uniform(0, 2*math.pi)),
            z=self._rng.uniform(-radius*0.6, radius*0.6),
            w=self._rng.uniform(-1.5, 1.5),
            v=self._rng.uniform(-1.5, 1.5),
            u=self._rng.uniform(-1.5, 1.5),
            color=self._rng.choice(['cyan', 'lime', 'yellow', 'magenta', 'white', 'orange'])
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

            if p.phase == 0:
                p.dx = -0.78 * (p.x / belt_r)
                p.dw = 0.055 * state.spin
            elif p.phase == 1:
                p.dw = GEAR_SHIFT * 0.14
                p.dv = state.temp * 0.35
            elif p.phase == 2:
                p.dx += 0.62 * SHADOW
            elif p.phase == 3:
                p.dx *= 0.68
                p.dw *= -0.6

            p.x += p.dx; p.y += p.dy; p.z += p.dz
            p.w += p.dw; p.v += p.dv; p.u += p.du

            r = math.hypot(p.x, p.y)
            if p.phase == 0 and r < throat * 1.2: p.phase = 1
            elif p.phase == 2 and r > belt_r * 0.88: p.phase = 3
            elif p.phase == 3 and r < throat * 1.35: p.phase = 0

            live.append(p)
        self.particles = live

    def plot_pca_projection(self, n_components: int = 3, save_path=None):
        """PCA projection of 6D particles"""
        if len(self.particles) < 10:
            print("Not enough particles for PCA.")
            return

        data = np.array([[p.x, p.y, p.z, p.w, p.v, p.u] for p in self.particles])
        data_mean = data.mean(axis=0)
        data_centered = data - data_mean

        _, S, Vt = np.linalg.svd(data_centered, full_matrices=False)
        proj = data_centered @ Vt.T[:, :n_components]

        fig = plt.figure(figsize=(14, 10))
        if n_components == 3:
            ax = fig.add_subplot(111, projection='3d')
            sizes = [max(10, abs(p.w) * 28) for p in self.particles]
            ax.scatter(proj[:,0], proj[:,1], proj[:,2],
                       s=sizes, c=[p.color for p in self.particles],
                       alpha=0.75, edgecolors='k', linewidth=0.4)
            ax.set_xlabel('PC1'); ax.set_ylabel('PC2'); ax.set_zlabel('PC3')
            ax.set_title("6D → 3D PCA Projection\n(Intrinsic Structure of the Manifold)")
        else:
            ax = fig.add_subplot(111)
            sizes = [max(20, abs(p.w) * 40) for p in self.particles]
            ax.scatter(proj[:,0], proj[:,1], s=sizes,
                       c=[p.color for p in self.particles], alpha=0.85)
            ax.set_xlabel('PC1'); ax.set_ylabel('PC2')
            ax.set_title("6D → 2D PCA Projection")
            ax.grid(True, alpha=0.3)

        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300)
        plt.show()

        explained = (S**2 / np.sum(S**2))[:3]
        print(f"PCA Explained Variance → PC1: {explained[0]:.1%} | PC2: {explained[1]:.1%} | PC3: {explained[2]:.1%}")


# ── Wrapper ────────────────────────────────────────────────────────────────

class TordialNodeWrapper:
    def __init__(self, node_id: str = "FPT-6D-PCA", base_radius: float = 60.0):
        self.node_id = node_id
        self.boundary = SixCylinderBoundary(base_radius)
        self.engine = ParticleFlowEngine6D(count=280)

    def tick(self, spin=None, pressure=None, temp=None, belt_mod=None):
        last = self.boundary.last_state
        state = self.boundary.compute(
            spin or (last.spin if last else 1.65),
            pressure or (last.pressure if last else 1.1),
            temp or (last.temp if last else 0.15),
            belt_mod or (last.belt_mod if last else 1.15)
        )
        self.engine.step(state)
        return state

    def plot_pca(self, n_components=3):
        state = self.boundary.last_state or self.boundary.compute()
        self.engine.plot_pca_projection(n_components=n_components)


# ── Demo ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    node = TordialNodeWrapper("FPT-PCA-Alpha")

    print("Running 6D simulation...\n")
    for i in range(30):
        node.tick(spin=1.7 + 0.5 * math.sin(i * 0.3), temp=0.12 * (i % 7))

    print("=== Higher-Dimensional Exploration ===")
    node.plot_pca(n_components=2)
    node.plot_pca(n_components=3)

    print("\n✅ 6D PCA particle projection complete.")