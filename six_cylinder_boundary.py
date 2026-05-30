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
import threading
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# ── Dynamic Dependencies Check ────────────────────────────────────────────────
try:
    from sklearn.manifold import TSNE
    TSNE_AVAILABLE = True
except ImportError:
    TSNE_AVAILABLE = False

try:
    import umap
    UMAP_AVAILABLE = True
except ImportError:
    UMAP_AVAILABLE = False
    print("⚠️  umap-learn not available. UMAP fallback routes activated.")


# ── Core Baseline Constants ──────────────────────────────────────────────────
TOROIDAL_ROOT = 3.1730059
GEAR_SHIFT    = 1.02          # ← UNIVERSAL STABILIZER (fixed)
SHADOW        = 1.03


# ── Data Architecture ─────────────────────────────────────────────────────────

@dataclass
class FaceGeometry:
    axis: str                 # 'core' | 'belt' | 'cap'
    label: str                # Human label for tracking
    role: str                 # Fluid mechanics description
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


# ── Closed-Loop Boundary Geometry Solver ──────────────────────────────────────

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

        # Front / Rear Core Axis Intake/Exhaust Curvature calculation
        core_curvature = (TOROIDAL_ROOT / math.pi) * spin * SHADOW
        core_radius = (self.base_radius * pressure) / core_curvature
        core_throat = core_radius * (1.0 - 0.15 * temp)
        core = FaceGeometry('core', 'FRONT / REAR', 'Intake · Exhaust', core_curvature, core_radius, core_throat)

        # Left / Right Expansion Centrifugal Belt
        belt_curvature = core_curvature * GEAR_SHIFT * belt_mod
        belt_radius = core_radius * belt_curvature
        belt = FaceGeometry('belt', 'LEFT / RIGHT', 'Expansion Belt', belt_curvature, belt_radius, belt_radius)

        # Top / Bottom Inverse Containment Pressure Caps
        cap_curvature = 1.0 / (belt_curvature * SHADOW)
        cap_radius = belt_radius * cap_curvature
        cap = FaceGeometry('cap', 'TOP / BOTTOM', 'Containment Caps', cap_curvature, cap_radius, cap_radius)

        state = SystemState(spin, pressure, temp, belt_mod, core, belt, cap)
        with self._lock:
            self._last_state = state
        return state

    def closed_loop_delta(self, state: SystemState) -> float:
        # Returns exactly 0.0 by construction — verification ledger
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


# ── 6D Particle Flow Engine ───────────────────────────────────────────────────

@dataclass
class Particle6D:
    x: float = 0.0; y: float = 0.0; z: float = 0.0
    w: float = 0.0; v: float = 0.0; u: float = 0.0
    dx: float = 0.0; dy: float = 0.0; dz: float = 0.0
    dw: float = 0.0; dv: float = 0.0; du: float = 0.0
    phase: int = 0            # 0=INTAKE, 1=TRANSIT, 2=EXHAUST, 3=RETURN
    life: int = 0
    max_life: int = 280
    color: str = 'cyan'


class ParticleFlowEngine6D:
    def __init__(self, count: int = 300):
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
            color=self._rng.choice(['cyan','lime','yellow','magenta','white','orange'])
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

            # ── Multi-Axis Velocity Propagation ──
            if p.phase == 0:     # INTAKE
                p.dx = -0.78 * (p.x / belt_r)
                p.dw = 0.055 * state.spin
            elif p.phase == 1:   # TRANSIT
                p.dw = GEAR_SHIFT * 0.14
                p.dv = state.temp * 0.35
            elif p.phase == 2:   # EXHAUST
                p.dx += 0.62 * SHADOW
            elif p.phase == 3:   # RETURN
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

    # ── Projection Methods ────────────────────────────────────────────────────

    def plot_pca_projection(self, n_components: int = 3, save_path=None):
        """Project 6D particles onto linear principal component vectors."""
        if len(self.particles) < 10:
            print("Not enough particles for PCA.")
            return

        data = np.array([[p.x, p.y, p.z, p.w, p.v, p.u] for p in self.particles])
        data_mean = data.mean(axis=0)
        data_centered = data - data_mean

        _, S, Vt = np.linalg.svd(data_centered, full_matrices=False)
        proj = data_centered @ Vt.T[:, :n_components]

        fig = plt.figure(figsize=(12, 8))
        if n_components == 3:
            ax = fig.add_subplot(111, projection='3d')
            sizes = [max(10, abs(p.w) * 28) for p in self.particles]
            ax.scatter(proj[:,0], proj[:,1], proj[:,2],
                       s=sizes, c=[p.color for p in self.particles],
                       alpha=0.75, edgecolors='k', linewidth=0.4)
            ax.set_xlabel('PC1'); ax.set_ylabel('PC2'); ax.set_zlabel('PC3')
            ax.set_title("6D Particles → 3D Linear PCA Leak-Field View")
        else:
            ax = fig.add_subplot(111)
            sizes = [max(20, abs(p.w) * 40) for p in self.particles]
            ax.scatter(proj[:,0], proj[:,1], s=sizes,
                       c=[p.color for p in self.particles], alpha=0.85)
            ax.set_xlabel('PC1'); ax.set_ylabel('PC2')
            ax.set_title("6D Particles → 2D Linear PCA Leak-Field View")
            ax.grid(True, alpha=0.3)

        plt.tight_layout()
        if save_path: plt.savefig(save_path, dpi=300)
        plt.show()

        explained = (S**2 / np.sum(S**2))[:3]
        print(f"PCA Explained Variance Ratio → PC1: {explained[0]:.1%} | PC2: {explained[1]:.1%} | PC3: {explained[2]:.1%}")

    def plot_tsne_projection(self, perplexity: float = 30.0, save_path=None):
        """Project 6D manifold onto 2D plane via t-SNE."""
        if not TSNE_AVAILABLE:
            print("t-SNE components not available. Install scikit-learn.")
            return

        data = np.array([[p.x, p.y, p.z, p.w, p.v, p.u] for p in self.particles])
        perp = min(perplexity, len(data) - 1)
        
        tsne = TSNE(n_components=2, perplexity=perp, random_state=42)
        proj = tsne.fit_transform(data)

        fig, ax = plt.subplots(figsize=(12, 8))
        sizes = [max(20, abs(p.w) * 40) for p in self.particles]
        ax.scatter(proj[:, 0], proj[:, 1], s=sizes, c=[p.color for p in self.particles], alpha=0.85, edgecolors='k', linewidth=0.3)
        ax.set_title(f"6D Manifold → 2D t-SNE Cluster Projection (Perplexity={perp:.1f})")
        ax.grid(True, alpha=0.2)
        plt.tight_layout()
        if save_path: plt.savefig(save_path, dpi=300)
        plt.show()

    def plot_umap_projection(self, n_neighbors=15, min_dist=0.1, random_state=42, save_path=None):
        """Project 6D particles onto non-linear spaces using topological UMAP."""
        if not UMAP_AVAILABLE:
            print("UMAP library unlinked. Reverting to t-SNE/PCA fallbacks.")
            if TSNE_AVAILABLE:
                self.plot_tsne_projection()
            else:
                self.plot_pca_projection(n_components=2)
            return

        if len(self.particles) < 20:
            print("Insufficient system density to resolve UMAP manifold structures.")
            return

        data = np.array([[p.x, p.y, p.z, p.w, p.v, p.u] for p in self.particles])

        reducer = umap.UMAP(
            n_neighbors=n_neighbors,
            min_dist=min_dist,
            n_components=2,
            random_state=random_state
        )
        proj = reducer.fit_transform(data)

        fig, ax = plt.subplots(figsize=(12, 8))
        sizes = [max(20, abs(p.w) * 45) for p in self.particles]

        ax.scatter(proj[:, 0], proj[:, 1], s=sizes,
                   c=[p.color for p in self.particles],
                   alpha=0.85, edgecolors='k', linewidth=0.4)

        ax.set_title(f"6D Continuous Medium → 2D UMAP Manifold Projection\n(n_neighbors={n_neighbors}, min_dist={min_dist})")
        ax.set_xlabel('UMAP Axis 1'); ax.set_ylabel('UMAP Axis 2')
        ax.grid(True, alpha=0.3)
        plt.tight_layout()

        if save_path: plt.savefig(save_path, dpi=300)
        plt.show()
        print(f"UMAP projection completed natively (n_neighbors={n_neighbors})")


# ── Toroidal Node Deployment Wrapper ──────────────────────────────────────────

class TordialNodeWrapper:
    def __init__(self, node_id: str = "FPT-6D-CORE", base_radius: float = 60.0, count: int = 300):
        self.node_id = node_id
        self.boundary = SixCylinderBoundary(base_radius)
        self.engine = ParticleFlowEngine6D(count=count)

    def tick(self, spin=None, pressure=None, temp=None, belt_mod=None) -> SystemState:
        last = self.boundary.last_state
        state = self.boundary.compute(
            spin or (last.spin if last else 1.7),
            pressure or (last.pressure if last else 1.1),
            temp or (last.temp if last else 0.15),
            belt_mod or (last.belt_mod if last else 1.15)
        )
        self.engine.step(state)
        return state

    def display_metrics(self, state: SystemState):
        metrics = self.boundary.to_tordial_metrics(state)
        print(f"Node [{self.node_id}] Tracking Metrics:")
        for k, v in metrics.items():
            print(f"  -> {k:<25}: {v:.6f}")

    def plot_umap(self, n_neighbors=15):
        self.engine.plot_umap_projection(n_neighbors=n_neighbors)

    def plot_pca(self, n_components=3):
        self.engine.plot_pca_projection(n_components=n_components)

    def plot_tsne(self, perplexity=35):
        self.engine.plot_tsne_projection(perplexity=perplexity)


# ── Active Verification Execution ─────────────────────────────────────────────

if __name__ == '__main__':
    # Initialize unified processing pipeline node
    node = TordialNodeWrapper(node_id="FPT-Unified-Alpha", count=300)

    print("Executing 6D dynamic simulation runtime loop...")
    for i in range(40):
        # Drive non-linear parameters into the system state calculation
        current_state = node.tick(
            spin=1.75 + 0.45 * math.sin(i * 0.35), 
            temp=0.1 * (i % 10)
        )
        
    print("\nSimulation complete. Final verification state captured.")
    print(current_state.summary())
    node.display_metrics(current_state)

    print("\n=== Executing Multi-Dimensional Topology Reductions ===")
    
    # 1. Non-linear Topology Projection (UMAP)
    print("\n1. Generating Topologically Aligned UMAP Space Projection...")
    node.plot_umap(n_neighbors=20)

    # 2. Non-linear Clustering Projection (t-SNE)
    if TSNE_AVAILABLE:
        print("\n2. Generating Local Distance t-SNE Projection...")
        node.plot_tsne(perplexity=35)

    # 3. Linear Orthogonal Blueprint Projections (PCA)
    print("\n3. Generating Linear Dimensionality Shovel Projections (PCA)...")
    node.plot_pca(n_components=2)
    node.plot_pca(n_components=3)

    print("\n✅ Unified runtime execution completed with zero calculation bleed.")
