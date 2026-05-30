"""
six_cylinder_boundary.py
========================
6-Cylindrical Boundary System — FPT Module
Two Mile Solutions LLC / JED Protocol

True System : 6-Dimensional (6 cylindrical faces)
Leak Field  : 3D projection for rendering and intuition

Constants
---------
TOROIDAL_ROOT : 3.1730059    — toroidal geometry root (calibrated for GEAR_SHIFT=1.02)
GEAR_SHIFT    : 1.02         — universal stabilizer (fixed / immutable)
SHADOW        : 1.03         — shadow constant (dimensional remainder)
"""

import os
import sys
import math
import time
import json
import random
import socket
import select
import threading
from dataclasses import dataclass, field
from typing import List, Dict, Optional

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation

# ── Dynamic Dependencies ──────────────────────────────────────────────────────
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

# ── Core Constants ────────────────────────────────────────────────────────────
TOROIDAL_ROOT = 3.1730059     # calibrated for GEAR_SHIFT = 1.02
GEAR_SHIFT    = 1.02          # ← UNIVERSAL STABILIZER (fixed / immutable)
SHADOW        = 1.03          # shadow constant (dimensional remainder)


# ── Data Architecture ─────────────────────────────────────────────────────────

@dataclass
class FaceGeometry:
    """Computed boundary state for one cylindrical face pair."""
    axis:      str
    label:     str
    role:      str
    curvature: float
    radius:    float
    throat:    float

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


# ── Closed-Loop Boundary Geometry Solver ─────────────────────────────────────

class SixCylinderBoundary:
    """
    Computes the 6-face cylindrical boundary state from system inputs.
    All three face pairs derive from the same toroidal root —
    closed-loop by construction, delta always returns 0.
    """

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

        # Front / Rear — Core Axis (intake / exhaust)
        core_curvature = (TOROIDAL_ROOT / math.pi) * spin * SHADOW
        core_radius    = (self.base_radius * pressure) / core_curvature
        core_throat    = core_radius * (1.0 - 0.15 * temp)
        core = FaceGeometry('core', 'FRONT / REAR', 'Intake · Exhaust',
                            core_curvature, core_radius, core_throat)

        # Left / Right — Expansion Belt (centrifugal ring)
        belt_curvature = core_curvature * GEAR_SHIFT * belt_mod
        belt_radius    = core_radius * belt_curvature
        belt = FaceGeometry('belt', 'LEFT / RIGHT', 'Expansion Belt',
                            belt_curvature, belt_radius, belt_radius)

        # Top / Bottom — Containment Caps (inverse deformation)
        cap_curvature = 1.0 / (belt_curvature * SHADOW)
        cap_radius    = belt_radius * cap_curvature
        cap = FaceGeometry('cap', 'TOP / BOTTOM', 'Containment Caps',
                           cap_curvature, cap_radius, cap_radius)

        state = SystemState(spin, pressure, temp, belt_mod, core, belt, cap)
        with self._lock:
            self._last_state = state
        return state

    def closed_loop_delta(self, state: SystemState) -> float:
        """Harmony metric — returns exactly 0.0 by construction."""
        return state.belt.curvature * state.cap.curvature * SHADOW - 1.0

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

    def to_toroidal_metrics(self, state: SystemState) -> Dict:
        delta = self.closed_loop_delta(state)
        return {
            "gs_density":            abs(delta) * 100 + 1.0,
            "curvature_mean":        (state.core.curvature + state.belt.curvature
                                      + state.cap.curvature) / 3,
            "closed_loop_stability": 1.0 - abs(delta),
        }

    def sweep_spin(self, spin_range=(0.1, 5.0), steps=10, **kwargs):
        lo, hi = spin_range
        return [self.compute(spin=lo + (hi - lo) * i / max(steps - 1, 1), **kwargs)
                for i in range(steps)]

    def sweep_temp(self, temp_range=(0.0, 1.0), steps=10, **kwargs):
        lo, hi = temp_range
        return [self.compute(temp=lo + (hi - lo) * i / max(steps - 1, 1), **kwargs)
                for i in range(steps)]

    @property
    def last_state(self) -> Optional[SystemState]:
        with self._lock:
            return self._last_state


# ── 6D Particle ───────────────────────────────────────────────────────────────

@dataclass
class Particle6D:
    x: float = 0.0;  y: float = 0.0;  z: float = 0.0
    w: float = 0.0;  v: float = 0.0;  u: float = 0.0
    dx: float = 0.0; dy: float = 0.0; dz: float = 0.0
    dw: float = 0.0; dv: float = 0.0; du: float = 0.0
    phase:    int = 0       # 0=INTAKE 1=TRANSIT 2=EXHAUST 3=RETURN
    life:     int = 0
    max_life: int = 280
    color:    str = '#00ffcc'

    @property
    def phase_name(self) -> str:
        return ['INTAKE', 'TRANSIT', 'EXHAUST', 'RETURN'][self.phase]


# ── 6D Particle Flow Engine (acceleration-based) ─────────────────────────────

class ParticleFlowEngine6D:
    """
    Simulates particle flow through the 6-cylinder geometry in full 6D space.
    x,y,z = spatial axes; w,v,u = extended dimensional axes.

    Physics: acceleration-based state machine with viscous drag.
    Projection: PCA (always), t-SNE (sklearn), UMAP (umap-learn).
    """

    # Palette matches the HTML visualizer
    COLORS = ['#00ffcc', '#ff3366', '#ffcc00', '#ae00ff', '#0077ff', '#ff6600']

    def __init__(self, count: int = 300):
        self.count = count
        self.particles: List[Particle6D] = []
        self._rng = random.Random(42)

    def _spawn(self, radius: float) -> Particle6D:
        r = self._rng
        theta = r.uniform(0, 2 * math.pi)
        return Particle6D(
            x=radius * r.uniform(0.6, 0.98) * math.cos(theta),
            y=radius * r.uniform(0.6, 0.98) * math.sin(theta),
            z=r.uniform(-radius * 0.6, radius * 0.6),
            w=r.uniform(-1.5, 1.5),
            v=r.uniform(-1.5, 1.5),
            u=r.uniform(-1.5, 1.5),
            color=r.choice(self.COLORS),
            max_life=220 + r.randint(0, 120),
        )

    def step(self, state: SystemState, dt: float = 0.05):
        """
        Acceleration-based 6D state-machine step.
        Force vectors are derived from SixCylinderBoundary geometry.
        Viscous drag stabilizes the system against blow-up at high spin.
        """
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

            r = math.hypot(p.x, p.y)
            ax = ay = az = aw = av = au = 0.0

            # ── Phase-space force vectors ─────────────────────────────────────
            if p.phase == 0:
                # INTAKE: collapse into core throat
                tf = throat / (r + 1e-9)
                ax = -1.5 * (p.x / belt_r) * tf
                ay = -1.5 * (p.y / belt_r) * tf
                az = -0.5 * p.z
                aw =  0.3 * state.spin
                if r < throat * 1.1:
                    p.phase = 1

            elif p.phase == 1:
                # TRANSIT: tangential orbital spin-up on extended axes
                ax = -1.0 * p.y * state.spin * GEAR_SHIFT
                ay =  1.0 * p.x * state.spin * GEAR_SHIFT
                az =  0.1 * (p.w - p.v)
                aw = (GEAR_SHIFT - p.w) * 0.5
                av = (state.temp  - p.v) * 0.5
                if r > belt_r * 0.75:
                    p.phase = 2

            elif p.phase == 2:
                # EXHAUST: radial dispersion through shadow remainder
                ax = 2.0 * (p.x / (r + 1e-9)) * SHADOW
                ay = 2.0 * (p.y / (r + 1e-9)) * SHADOW
                az = 0.8 * p.z * state.pressure
                if r > belt_r * 0.95 or abs(p.z) > belt_r * 0.6:
                    p.phase = 3

            elif p.phase == 3:
                # RETURN: inverse containment pressure snap-back
                inv_p = 1.0 / (state.pressure + 1e-9)
                ax = -2.5 * p.x * inv_p
                ay = -2.5 * p.y * inv_p
                az = -1.5 * p.z
                p.dw *= 0.1; p.dv *= 0.1; p.du *= 0.1
                if r < throat * 1.4:
                    p.phase = 0

            # ── Kinematic integration ─────────────────────────────────────────
            p.dx += ax * dt; p.dy += ay * dt; p.dz += az * dt
            p.dw += aw * dt; p.dv += av * dt; p.du += au * dt

            # Viscous drag — stabilizes high-spin states
            drag = max(0.5, 1.0 - 0.04 * state.pressure)
            p.dx *= drag; p.dy *= drag; p.dz *= drag
            p.dw *= drag; p.dv *= drag; p.du *= drag

            p.x += p.dx; p.y += p.dy; p.z += p.dz
            p.w += p.dw; p.v += p.dv; p.u += p.du

            live.append(p)
        self.particles = live

    def phase_counts(self) -> Dict:
        counts = {'INTAKE': 0, 'TRANSIT': 0, 'EXHAUST': 0, 'RETURN': 0}
        for p in self.particles:
            counts[p.phase_name] += 1
        return counts

    def get_data_matrix(self) -> np.ndarray:
        return np.array([[p.x, p.y, p.z, p.w, p.v, p.u] for p in self.particles])

    # ── Projection: PCA ───────────────────────────────────────────────────────

    def plot_pca_projection(self, n_components: int = 3, save_path=None):
        if len(self.particles) < 10:
            print("Not enough particles for PCA."); return
        data = self.get_data_matrix()
        data_c = data - data.mean(axis=0)
        _, S, Vt = np.linalg.svd(data_c, full_matrices=False)
        proj = data_c @ Vt.T[:, :n_components]
        explained = (S**2 / np.sum(S**2))[:3]
        colors = [p.color for p in self.particles]

        fig = plt.figure(figsize=(10, 7), facecolor='#0f0f14')
        if n_components == 3:
            ax = fig.add_subplot(111, projection='3d', facecolor='#0f0f14')
            sizes = [max(10, abs(p.w) * 25) for p in self.particles]
            ax.scatter(proj[:,0], proj[:,1], proj[:,2], s=sizes, c=colors, alpha=0.7)
            ax.set_title("6D Particles → 3D PCA Leak Field", color='white')
            ax.set_xlabel('PC1'); ax.set_ylabel('PC2'); ax.set_zlabel('PC3')
        else:
            ax = fig.add_subplot(111, facecolor='#13131a')
            ax.scatter(proj[:,0], proj[:,1], c=colors, s=30, alpha=0.7)
            ax.set_title("6D Particles → 2D PCA Leak Field", color='white')
            ax.set_xlabel('PC1'); ax.set_ylabel('PC2')
            ax.grid(True, alpha=0.3)
        plt.tight_layout()
        if save_path: plt.savefig(save_path, dpi=300, facecolor=fig.get_facecolor()); plt.close()
        else: plt.show()
        print(f"PCA Variance → PC1:{explained[0]:.1%} PC2:{explained[1]:.1%} PC3:{explained[2]:.1%}")

    # ── Projection: t-SNE ─────────────────────────────────────────────────────

    def plot_tsne_projection(self, perplexity: float = 30.0, save_path=None):
        if not TSNE_AVAILABLE:
            print("t-SNE unavailable — install scikit-learn."); return
        data = self.get_data_matrix()
        perp = min(perplexity, len(data) - 1)
        proj = TSNE(n_components=2, perplexity=perp, random_state=42, init='pca').fit_transform(data)
        colors = [p.color for p in self.particles]
        fig, ax = plt.subplots(figsize=(10, 7), facecolor='#0f0f14')
        ax.set_facecolor('#13131a')
        ax.scatter(proj[:,0], proj[:,1],
                   s=[max(20, abs(p.w)*40) for p in self.particles],
                   c=colors, alpha=0.85, edgecolors='k', linewidth=0.3)
        ax.set_title(f"6D Manifold → 2D t-SNE (perplexity={perp:.0f})", color='white')
        ax.grid(True, alpha=0.2)
        plt.tight_layout()
        if save_path: plt.savefig(save_path, dpi=300, facecolor=fig.get_facecolor()); plt.close()
        else: plt.show()

    # ── Projection: UMAP ─────────────────────────────────────────────────────

    def plot_umap_projection(self, n_neighbors=15, min_dist=0.1, save_path=None):
        if not UMAP_AVAILABLE:
            print("UMAP unavailable — falling back.")
            if TSNE_AVAILABLE: self.plot_tsne_projection()
            else:              self.plot_pca_projection(n_components=2)
            return
        if len(self.particles) < 20:
            print("Insufficient particle density for UMAP."); return
        data = self.get_data_matrix()
        proj = umap.UMAP(n_neighbors=n_neighbors, min_dist=min_dist,
                         n_components=2, random_state=42).fit_transform(data)
        colors = [p.color for p in self.particles]
        fig, ax = plt.subplots(figsize=(10, 7), facecolor='#0f0f14')
        ax.set_facecolor('#13131a')
        ax.scatter(proj[:,0], proj[:,1],
                   s=[max(20, abs(p.w)*45) for p in self.particles],
                   c=colors, alpha=0.85, edgecolors='k', linewidth=0.4)
        ax.set_title(f"6D → 2D UMAP (n_neighbors={n_neighbors}, min_dist={min_dist})", color='white')
        ax.set_xlabel('UMAP 1'); ax.set_ylabel('UMAP 2')
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        if save_path: plt.savefig(save_path, dpi=300, facecolor=fig.get_facecolor()); plt.close()
        else: plt.show()

    # ── Unified manifold router: UMAP → t-SNE → PCA ──────────────────────────

    def plot_manifold_projection(self, method: str = 'tsne', save_path: str = None):
        if len(self.particles) < 10:
            print("❌ Insufficient particles for manifold projection."); return
        data   = self.get_data_matrix()
        colors = [p.color for p in self.particles]
        method = method.lower()
        proj   = None

        if method == 'umap':
            if UMAP_AVAILABLE:
                try:
                    proj = umap.UMAP(n_neighbors=15, min_dist=0.1,
                                     n_components=2, random_state=42).fit_transform(data)
                except Exception as e:
                    print(f"⚠️  UMAP failed ({e}). Falling back to t-SNE.")
                    method = 'tsne'
            else:
                method = 'tsne'

        if method == 'tsne' and proj is None:
            if TSNE_AVAILABLE:
                try:
                    perp = min(30, max(5, len(data) // 5))
                    proj = TSNE(n_components=2, perplexity=perp,
                                random_state=42, init='pca').fit_transform(data)
                except Exception as e:
                    print(f"⚠️  t-SNE failed ({e}). Falling back to PCA.")
                    method = 'pca'
            else:
                method = 'pca'

        if method == 'pca' or proj is None:
            method = 'pca (fallback)'
            data_c = data - data.mean(axis=0)
            _, _, Vt = np.linalg.svd(data_c, full_matrices=False)
            proj = data_c @ Vt.T[:, :2]

        fig, ax = plt.subplots(figsize=(10, 7), facecolor='#0f0f14')
        ax.set_facecolor('#13131a')
        ax.scatter(proj[:,0], proj[:,1], c=colors, s=35, alpha=0.8,
                   edgecolors='#ffffff', linewidths=0.2)
        ax.set_title(f"6D Flow → 2D Manifold ({method.upper()})", color='white', fontsize=12)
        ax.tick_params(colors='gray', labelsize=9)
        ax.grid(True, color='#2a2a35', linestyle=':', alpha=0.6)
        for spine in ax.spines.values(): spine.set_color('#2a2a35')
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
            plt.close()
            print(f"💾 Manifold exported: {save_path}")
        else:
            plt.show()


# ── Real-Time Animation ───────────────────────────────────────────────────────

class RealTimeEngineAnimator:
    def __init__(self, boundary: SixCylinderBoundary, engine: ParticleFlowEngine6D):
        self.boundary = boundary
        self.engine   = engine
        self.state    = self.boundary.compute()
        self.ani      = None

    def start_live_render(self, frames: int = 200, interval: int = 30):
        fig = plt.figure(figsize=(13, 6), facecolor='#0b0b0e')
        ax3d = fig.add_subplot(121, projection='3d', facecolor='#0b0b0e')
        ax2d = fig.add_subplot(122, facecolor='#111115')

        def update(frame):
            self.state = self.boundary.compute(
                spin=1.5 + 0.4 * math.sin(frame * 0.05),
                temp=0.3 + 0.2 * math.cos(frame * 0.03),
            )
            self.engine.step(self.state, dt=0.04)
            data   = self.engine.get_data_matrix()
            colors = [p.color for p in self.engine.particles]
            sizes  = [max(8, abs(p.w) * 22) for p in self.engine.particles]

            ax3d.clear(); ax2d.clear()
            ax3d.set_facecolor('#0b0b0e')
            for pane in (ax3d.w_xaxis, ax3d.w_yaxis, ax3d.w_zaxis):
                pane.set_pane_color((0.0, 0.0, 0.0, 0.0))

            if len(data) >= 10:
                data_c = data - data.mean(axis=0)
                _, _, Vt = np.linalg.svd(data_c, full_matrices=False)
                proj3d = data_c @ Vt.T[:, :3]
                ax3d.scatter(proj3d[:,0], proj3d[:,1], proj3d[:,2], s=sizes, c=colors, alpha=0.7)
                ax2d.scatter(data[:,0], data[:,1], c=colors, s=15, alpha=0.6)

            ax3d.set_title("3D PCA Leak Field", color='#e0e0e0', fontsize=11)
            ax3d.tick_params(colors='gray', labelsize=8)
            ax3d.view_init(elev=22, azim=frame * 0.5)

            limit_r = self.state.belt.radius * 1.2
            ax2d.set_xlim(-limit_r, limit_r); ax2d.set_ylim(-limit_r, limit_r)
            ax2d.set_title(f"X-Y Cross-Section  spin={self.state.spin:.2f}",
                           color='#e0e0e0', fontsize=11)
            ax2d.grid(True, color='#22222d', linestyle='--')
            ax2d.tick_params(colors='gray', labelsize=8)
            ax2d.add_patch(plt.Circle((0, 0), self.state.core.throat * 0.5,
                                      color='#ff3366', fill=False, linestyle=':', alpha=0.7))
            plt.tight_layout()

        self.ani = FuncAnimation(fig, update, frames=frames, interval=interval, repeat=False)
        plt.show()


# ── JED Network Broker (JSON-RPC + telemetry logger) ─────────────────────────

class JEDNetworkBroker:
    """
    Asynchronous JSON-RPC command broker and telemetry flat-file logger.
    Methods: update_geometry, get_status
    Streams telemetry JSON to all connected clients and logs to disk.
    """

    def __init__(self, solver: SixCylinderBoundary, host='127.0.0.1', port=8888,
                 log_file='manifold_telemetry.log'):
        self.solver   = solver
        self.host     = host
        self.port     = port
        self.log_file = log_file
        self.clients  = []
        self._running = False

        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n# --- NEW MANIFOLD SESSION: {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        print(f"📂 Telemetry log: {os.path.abspath(self.log_file)}")

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.server_socket.setblocking(False)
        self._running = True
        self._thread  = threading.Thread(target=self._pump, daemon=True, name='JED-NetPump')
        self._thread.start()
        print(f"📡 RPC Pipeline live on tcp://{self.host}:{self.port}")

    def _pump(self):
        while self._running:
            socks = [self.server_socket] + self.clients
            try:
                readable, _, errorable = select.select(socks, [], socks, 0.2)
            except (ValueError, socket.error):
                continue
            for sock in readable:
                if sock is self.server_socket:
                    try:
                        c, _ = self.server_socket.accept()
                        c.setblocking(False)
                        self.clients.append(c)
                    except socket.error: pass
                else:
                    try:
                        data = sock.recv(4096)
                        if data: self._handle_rpc(sock, data.decode('utf-8'))
                        else:    self._drop(sock)
                    except socket.error: self._drop(sock)
            for sock in errorable: self._drop(sock)

    def _handle_rpc(self, sock, raw: str):
        try:
            req    = json.loads(raw)
            method = req.get('method')
            params = req.get('params', {})
            rid    = req.get('id')

            if method == 'update_geometry':
                curr = self.solver.last_state or self.solver.compute()
                self.solver.compute(
                    spin=params.get('spin', curr.spin),
                    pressure=params.get('pressure', curr.pressure),
                    temp=params.get('temp', curr.temp),
                    belt_mod=params.get('belt_mod', curr.belt_mod),
                )
                resp = {'jsonrpc': '2.0', 'result': 'GEOMETRY_MUTATION_OK', 'id': rid}
            elif method == 'get_status':
                curr = self.solver.last_state or self.solver.compute()
                resp = {'jsonrpc': '2.0',
                        'result': {'spin': curr.spin, 'pressure': curr.pressure,
                                   'temp': curr.temp}, 'id': rid}
            else:
                resp = {'jsonrpc': '2.0',
                        'error': {'code': -32601, 'message': 'Method not found'}, 'id': rid}

            sock.sendall((json.dumps(resp) + '\n').encode('utf-8'))
        except Exception as e:
            err = {'jsonrpc': '2.0', 'error': {'code': -32700, 'message': str(e)}, 'id': None}
            try: sock.sendall((json.dumps(err) + '\n').encode('utf-8'))
            except socket.error: pass

    def push_telemetry(self, state: SystemState, metrics: dict):
        """Append to disk log and broadcast to all connected clients."""
        frame = {
            'timestamp':   state.timestamp,
            'spin':        state.spin,
            'pressure':    state.pressure,
            'temp':        state.temp,
            'stability':   metrics['closed_loop_stability'],
            'core_throat': state.core.throat,
            'belt_radius': state.belt.radius,
        }
        serialized = json.dumps(frame)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(serialized + '\n')
        packet = (serialized + '\n').encode('utf-8')
        for client in list(self.clients):
            try:    client.sendall(packet)
            except socket.error: self._drop(client)

    def _drop(self, sock):
        if sock in self.clients:
            self.clients.remove(sock)
            try: sock.close()
            except socket.error: pass

    def stop(self):
        self._running = False
        if hasattr(self, 'server_socket'): self.server_socket.close()
        for c in self.clients: c.close()


# ── Telemetry Stream Dashboard ────────────────────────────────────────────────

class TelemetryStreamDashboard:
    """
    Connects to the JED broker socket stream and renders a live
    3-panel Matplotlib dashboard: spin / stability / belt radius.
    """

    def __init__(self, host='127.0.0.1', port=8888, max_points=100):
        self.host       = host
        self.port       = port
        self.max_points = max_points
        self.spin_hist  = []
        self.stab_hist  = []
        self.rad_hist   = []
        self.sock       = None
        self._buffer    = ''

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            self.sock.setblocking(False)
            print("🚀 Telemetry dashboard connected.")
        except socket.error as e:
            print(f"❌ Connection failed: {e}")
            sys.exit(1)

    def _read_stream(self):
        if not self.sock: return
        try:
            ready = select.select([self.sock], [], [], 0.0)
            if ready[0]:
                chunk = self.sock.recv(4096).decode('utf-8')
                if not chunk: return
                self._buffer += chunk
                while '\n' in self._buffer:
                    line, self._buffer = self._buffer.split('\n', 1)
                    if line.strip():
                        frame = json.loads(line)
                        self.spin_hist.append(frame['spin'])
                        self.stab_hist.append(frame['stability'])
                        self.rad_hist.append(frame['belt_radius'])
                        for buf in (self.spin_hist, self.stab_hist, self.rad_hist):
                            if len(buf) > self.max_points: buf.pop(0)
        except socket.error: pass

    def launch(self):
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 8), facecolor='#0f0f14')
        fig.suptitle("JED Protocol — 6C Manifold Telemetry Stream", color='white', fontsize=12)
        for ax in (ax1, ax2, ax3):
            ax.set_facecolor('#13131a')
            ax.grid(True, color='#252530', linestyle=':')
            ax.tick_params(colors='gray', labelsize=8)
            for s in ax.spines.values(): s.set_color('#252530')

        l1, = ax1.plot([], [], color='#00ffcc', linewidth=1.5)
        ax1.set_ylabel("Spin Vector", color='white')
        l2, = ax2.plot([], [], color='#ff3366', linewidth=1.5)
        ax2.set_ylabel("Stability", color='white')
        l3, = ax3.plot([], [], color='#ffcc00', linewidth=1.5)
        ax3.set_ylabel("Belt Radius", color='white')
        ax3.set_xlabel("Rolling Telemetry Window", color='gray')

        def update(frame):
            self._read_stream()
            if not self.spin_hist: return l1, l2, l3
            x = np.arange(len(self.spin_hist))
            l1.set_data(x, self.spin_hist)
            l2.set_data(x, self.stab_hist)
            l3.set_data(x, self.rad_hist)
            for ax, hist in zip((ax1, ax2, ax3),
                                (self.spin_hist, self.stab_hist, self.rad_hist)):
                ax.set_xlim(0, max(10, len(hist) - 1))
                lo, hi = min(hist), max(hist)
                pad = max(0.05, (hi - lo) * 0.1)
                ax.set_ylim(lo - pad, hi + pad)
            return l1, l2, l3

        self._ani = FuncAnimation(fig, update, interval=40, blit=True, cache_frame_data=False)
        plt.tight_layout()
        plt.show()


# ── Toroidal Node Wrapper ─────────────────────────────────────────────────────

class ToroidalNodeWrapper:
    """Unified access point: boundary solver + 6D particle engine."""

    def __init__(self, node_id='FPT-6D-CORE', base_radius=60.0, count=300):
        self.node_id  = node_id
        self.boundary = SixCylinderBoundary(base_radius)
        self.engine   = ParticleFlowEngine6D(count=count)

    def tick(self, spin=None, pressure=None, temp=None, belt_mod=None,
             dt: float = 0.05) -> SystemState:
        last  = self.boundary.last_state
        state = self.boundary.compute(
            spin     = spin     or (last.spin     if last else 1.7),
            pressure = pressure or (last.pressure if last else 1.1),
            temp     = temp     or (last.temp     if last else 0.15),
            belt_mod = belt_mod or (last.belt_mod if last else 1.15),
        )
        self.engine.step(state, dt=dt)
        return state

    def display_metrics(self, state: SystemState):
        metrics = self.boundary.to_toroidal_metrics(state)
        print(f"Node [{self.node_id}] Metrics:")
        for k, v in metrics.items():
            print(f"  -> {k:<26}: {v:.6f}")


# ── Entry Points ──────────────────────────────────────────────────────────────

def run_demo():
    print("🚀 6-Cylindrical Boundary System — FPT Module")
    print(f"   TR={TOROIDAL_ROOT}  GS={GEAR_SHIFT}  SH={SHADOW}\n")

    node = ToroidalNodeWrapper(node_id='FPT-Unified-Alpha', count=300)

    print("Running 40 kinematic cycles (acceleration physics, dt=0.04)...")
    for i in range(40):
        state = node.tick(
            spin=1.75 + 0.45 * math.sin(i * 0.35),
            temp=0.1 * (i % 10),
            dt=0.04,
        )

    print(state.summary())
    node.display_metrics(state)
    print(f"\n  Closed-Loop Delta : {node.boundary.closed_loop_delta(state):.12f}")
    print(f"  Flux Balance      : {node.boundary.flux_balance(state)}")
    print(f"  Phase Counts      : {node.engine.phase_counts()}")

    print("\n🧬 Manifold projection...")
    node.engine.plot_manifold_projection(method='pca')

    print("\n🖥️  Real-time animator...")
    RealTimeEngineAnimator(node.boundary, node.engine).start_live_render(frames=200, interval=30)


def run_engine_server():
    print("🏗️  Initializing JED manifold engine server...")
    solver = SixCylinderBoundary(base_radius=50.0)
    engine = ParticleFlowEngine6D(count=300)
    broker = JEDNetworkBroker(solver=solver)
    broker.start()

    print(f"\n💡 Dashboard client:  python {os.path.basename(__file__)} --plotter")
    print("   RPC inject example:")
    print('   echo \'{"method":"update_geometry","params":{"spin":2.8,"temp":0.65},"id":1}\' '
          '| nc 127.0.0.1 8888\n')
    print("Ctrl+C to stop.")
    try:
        while True:
            state   = solver.last_state or solver.compute(spin=1.5, pressure=1.0, temp=0.15)
            engine.step(state, dt=0.04)
            metrics = solver.to_toroidal_metrics(state)
            broker.push_telemetry(state, metrics)
            time.sleep(0.033)
    except KeyboardInterrupt:
        print("\n⚡ Shutdown signal received.")
    finally:
        broker.stop()
        print("🏁 Engine cleanly closed.")


def run_plotter_client():
    dash = TelemetryStreamDashboard(port=8888)
    dash.connect()
    dash.launch()


if __name__ == '__main__':
    if   len(sys.argv) > 1 and sys.argv[1] == '--plotter': run_plotter_client()
    elif len(sys.argv) > 1 and sys.argv[1] == '--server':  run_engine_server()
    else:                                                   run_demo()
            w=r.uniform(-1.5, 1.5),
            v=r.uniform(-1.5, 1.5),
            u=r.uniform(-1.5, 1.5),
            color=r.choice(self.COLORS)
        )

    def step(self, state: SystemState, dt: float = 0.05):
        """
        Executes an acceleration-based state machine step across all 6 coordinates.
        Uses physical boundary constraints derived from the SixCylinderBoundary solver.
        """
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

            r = math.hypot(p.x, p.y)
            ax = ay = az = aw = av = au = 0.0

            # ── 6D State-Machine Phase Space Accelerations ──
            if p.phase == 0:     # INTAKE: Force vectors collapse particles into core throat
                target_factor = throat / (r + 1e-9)
                ax = -1.5 * (p.x / belt_r) * target_factor
                ay = -1.5 * (p.y / belt_r) * target_factor
                az = -0.5 * p.z
                aw = 0.3 * state.spin
                if r < throat * 1.1:
                    p.phase = 1

            elif p.phase == 1:   # TRANSIT: Tangential orbital forces spin up extended axes
                ax = -1.0 * p.y * state.spin * GEAR_SHIFT
                ay = 1.0 * p.x * state.spin * GEAR_SHIFT
                az = 0.1 * (p.w - p.v)
                aw = (GEAR_SHIFT - p.w) * 0.5
                av = (state.temp - p.v) * 0.5
                if r > belt_r * 0.75:
                    p.phase = 2

            elif p.phase == 2:   # EXHAUST: High radial dispersion through shadow remainder
                ax = 2.0 * (p.x / (r + 1e-9)) * SHADOW
                ay = 2.0 * (p.y / (r + 1e-9)) * SHADOW
                az = 0.8 * p.z * state.pressure
                if r > belt_r * 0.95 or abs(p.z) > belt_r * 0.6:
                    p.phase = 3

            elif p.phase == 3:   # RETURN: Inverse containment pressure fields snap back
                ax = -2.5 * p.x * (1.0 / (state.pressure + 1e-9))
                ay = -2.5 * p.y * (1.0 / (state.pressure + 1e-9))
                az = -1.5 * p.z
                p.dw *= 0.1
                p.dv *= 0.1
                p.du *= 0.1
                if r < throat * 1.4:
                    p.phase = 0

            # Kinematic numerical Integration
            p.dx += ax * dt; p.dy += ay * dt; p.dz += az * dt
            p.dw += aw * dt; p.dv += av * dt; p.du += au * dt

            # Fluid viscous drag application to maintain system stability
            drag = 1.0 - (0.04 * state.pressure)
            p.dx *= drag; p.dy *= drag; p.dz *= drag
            p.dw *= drag; p.dv *= drag; p.du *= drag

            p.x += p.dx; p.y += p.dy; p.z += p.dz
            p.w += p.dw; p.v += p.dv; p.u += p.du

            live.append(p)
        self.particles = live

    # ── Dimensional Reduction Projections ─────────────────────────────────────

    def get_data_matrix(self) -> np.ndarray:
        return np.array([[p.x, p.y, p.z, p.w, p.v, p.u] for p in self.particles])

    def plot_pca_projection(self, n_components: int = 3, save_path=None):
        """Project 6D particles onto linear principal component vectors via SVD."""
        if len(self.particles) < 10: return
        data = self.get_data_matrix()
        data_centered = data - data.mean(axis=0)

        _, _, Vt = np.linalg.svd(data_centered, full_matrices=False)
        proj = data_centered @ Vt.T[:, :n_components]

        fig = plt.figure(figsize=(10, 7), facecolor='#0f0f14')
        colors = [p.color for p in self.particles]

        if n_components == 3:
            ax = fig.add_subplot(111, projection='3d', facecolor='#0f0f14')
            sizes = [max(10, abs(p.w) * 25) for p in self.particles]
            ax.scatter(proj[:,0], proj[:,1], proj[:,2], s=sizes, c=colors, alpha=0.7)
            ax.set_title("6D Particle Flow — 3D PCA Projection Leak Field", color='white')
        else:
            ax = fig.add_subplot(111, facecolor='#13131a')
            ax.scatter(proj[:,0], proj[:,1], c=colors, s=30, alpha=0.7)
            ax.set_title("6D Particle Flow — 2D PCA Projection", color='white')

        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, facecolor=fig.get_facecolor())
            plt.close()
        else:
            plt.show()

    def plot_manifold_projection(self, method: str = 'tsne', save_path: str = None):
        """Projects 6D particles to 2D using non-linear reduction with fallbacks."""
        if len(self.particles) < 10: return
        data = self.get_data_matrix()
        colors = [p.color for p in self.particles]
        method = method.lower()
        proj = None

        if method == 'umap':
            if UMAP_AVAILABLE:
                try:
                    reducer = umap.UMAP(n_neighbors=15, min_dist=0.1, n_components=2, random_state=42)
                    proj = reducer.fit_transform(data)
                except Exception: method = 'tsne'
            else: method = 'tsne'

        if method == 'tsne' and proj is None:
            if TSNE_AVAILABLE:
                try:
                    perp = min(30, max(5, len(data) // 5))
                    tsne = TSNE(n_components=2, perplexity=perp, random_state=42, init='pca')
                    proj = tsne.fit_transform(data)
                except Exception: method = 'pca'
            else: method = 'pca'

        if method == 'pca' or proj is None:
            method = 'pca (fallback)'
            data_centered = data - data.mean(axis=0)
            _, _, Vt = np.linalg.svd(data_centered, full_matrices=False)
            proj = data_centered @ Vt.T[:, :2]

        fig, ax = plt.subplots(figsize=(10, 7), facecolor='#0f0f14')
        ax.set_facecolor('#13131a')
        ax.scatter(proj[:, 0], proj[:, 1], c=colors, s=35, alpha=0.8, edgecolors='#ffffff', linewidths=0.2)
        ax.set_title(f"6D Particle Flow — 2D Manifold Space ({method.upper()})", color='white')
        ax.grid(True, color='#252530', linestyle=':')
        
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, facecolor=fig.get_facecolor())
            plt.close()
        else:
            plt.show()


# ── JSON-RPC Network Automation and Disk Logging Broker ───────────────────────

class JEDNetworkBroker:
    """Asynchronous JSON-RPC command broker and telemetry flat-file logger."""
    def __init__(self, solver: SixCylinderBoundary, host: str = '127.0.0.1', port: int = 8888, log_file: str = "manifold_telemetry.log"):
        self.solver = solver
        self.host = host
        self.port = port
        self.log_file = log_file
        self.clients = []
        self._running = False
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"\n# --- NEW MANIFOLD RECORDING SESSION: {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.server_socket.setblocking(False)
        self._running = True
        self._thread = threading.Thread(target=self._pump, daemon=True, name="JED-NetPump")
        self._thread.start()
        print(f"📡 RPC Pipeline Server listening on tcp://{self.host}:{self.port}")

    def _pump(self):
        while self._running:
            socks = [self.server_socket] + self.clients
            try: readable, _, errorable = select.select(socks, [], socks, 0.2)
            except (ValueError, socket.error): continue

            for sock in readable:
                if sock is self.server_socket:
                    try:
                        c_sock, _ = self.server_socket.accept()
                        c_sock.setblocking(False)
                        self.clients.append(c_sock)
                    except socket.error: pass
                else:
                    try:
                        data = sock.recv(4096)
                        if data: self._handle_rpc(sock, data.decode('utf-8'))
                        else: self._drop(sock)
                    except socket.error: self._drop(sock)
            for sock in errorable: self._drop(sock)

    def _handle_rpc(self, sock, raw_str: str):
        try:
            req = json.loads(raw_str)
            method = req.get("method")
            params = req.get("params", {})
            req_id = req.get("id")
            
            if method == "update_geometry":
                curr = self.solver.last_state or self.solver.compute()
                self.solver.compute(
                    spin=params.get("spin", curr.spin),
                    pressure=params.get("pressure", curr.pressure),
                    temp=params.get("temp", curr.temp),
                    belt_mod=params.get("belt_mod", curr.belt_mod)
                )
                resp = {"jsonrpc": "2.0", "result": "GEOMETRY_MUTATION_OK", "id": req_id}
            elif method == "get_status":
                curr = self.solver.last_state or self.solver.compute()
                resp = {"jsonrpc": "2.0", "result": {"spin": curr.spin, "pressure": curr.pressure, "temp": curr.temp}, "id": req_id}
            else:
                resp = {"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": req_id}
            sock.sendall((json.dumps(resp) + "\n").encode('utf-8'))
        except Exception as e:
            err = {"jsonrpc": "2.0", "error": {"code": -32700, "message": str(e)}, "id": None}
            try: sock.sendall((json.dumps(err) + "\n").encode('utf-8'))
            except socket.error: pass

