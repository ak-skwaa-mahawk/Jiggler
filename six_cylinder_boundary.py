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
        lines = [f"{'='*65}", "  6-CYLINDRICAL BOUNDARY STATE", 
                 f"  spin={self.spin:.3f}  pressure={self.pressure:.3f}  "
                 f"temp={self.temp:.3f}  belt_mod={self.belt_mod:.3f}",
                 f"{'─'*65}"]
        for f in self.faces():
            lines.append(f"  {f.label:<14} curv={f.curvature:.6f}  r={f.radius:.4f}  throat={f.throat:.4f}")
        lines.append(f"{'='*65}")
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

        # Core Axis
        core_curvature = (TOROIDAL_ROOT / math.pi) * spin * SHADOW
        core_radius = (self.base_radius * pressure) / core_curvature
        core_throat = core_radius * (1.0 - 0.15 * temp)

        core = FaceGeometry('core', 'FRONT / REAR', 'Intake · Exhaust',
                            core_curvature, core_radius, core_throat)

        # Expansion Belt
        belt_curvature = core_curvature * GEAR_SHIFT * belt_mod
        belt_radius = core_radius * belt_curvature

        belt = FaceGeometry('belt', 'LEFT / RIGHT', 'Expansion Belt',
                            belt_curvature, belt_radius, belt_radius)

        # Containment Caps
        cap_curvature = 1.0 / (belt_curvature * SHADOW)
        cap_radius = belt_radius * cap_curvature

        cap = FaceGeometry('cap', 'TOP / BOTTOM', 'Containment Caps',
                           cap_curvature, cap_radius, cap_radius)

        state = SystemState(spin=spin, pressure=pressure, temp=temp,
                            belt_mod=belt_mod, core=core, belt=belt, cap=cap)

        with self._lock:
            self._last_state = state
        return state

    # Derived metrics (unchanged)
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

    # Sweeps (unchanged)
    def sweep_spin(self, spin_range=(0.1, 5.0), steps=10, **kwargs):
        lo, hi = spin_range
        return [self.compute(spin=lo + (hi-lo)*i/max(steps-1,1), **kwargs) for i in range(steps)]

    def sweep_temp(self, temp_range=(0.0, 1.0), steps=10, **kwargs):
        lo, hi = temp_range
        return [self.compute(temp=lo + (hi-lo)*i/max(steps-1,1), **kwargs) for i in range(steps)]

    @property
    def last_state(self) -> Optional[SystemState]:
        with self._lock: return self._last_state


# ── 3D Visualization ────────────────────────────────────────────────────────

    def plot_3d(self, state: Optional[SystemState] = None, title="6-Cylinder Toroidal Boundary", save_path=None):
        if state is None:
            state = self.last_state or self.compute()

        fig = plt.figure(figsize=(12, 9))
        ax = fig.add_subplot(111, projection='3d')
        ax.set_title(title)

        # Core (inner cylinder)
        core_r = state.core.throat
        theta = np.linspace(0, 2*np.pi, 50)
        z = np.linspace(-core_r*0.6, core_r*0.6, 30)
        Theta, Z = np.meshgrid(theta, z)
        Xc = core_r * np.cos(Theta)
        Yc = core_r * np.sin(Theta)
        ax.plot_surface(Xc, Yc, Z, alpha=0.6, color='red', label='Core')

        # Belt (mid expansion)
        belt_r = state.belt.radius
        Xb = belt_r * np.cos(Theta)
        Yb = belt_r * np.sin(Theta)
        ax.plot_surface(Xb, Yb, Z*1.8, alpha=0.5, color='orange')

        # Caps (outer)
        cap_r = state.cap.radius
        Xcap = cap_r * np.cos(Theta)
        Ycap = cap_r * np.sin(Theta)
        ax.plot_surface(Xcap, Ycap, Z*2.2, alpha=0.4, color='blue')

        ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
        ax.set_box_aspect([1,1,0.6])

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()


# ── Tordial-GS Integration Hooks ───────────────────────────────────────────

    def to_tordial_metrics(self, state: SystemState) -> Dict:
        """Return metrics compatible with TordialNode / GS seeding"""
        delta = self.closed_loop_delta(state)
        return {
            "gs_density": abs(delta) * 100 + 1.0,           # modulate GS growth
            "curvature_mean": (state.core.curvature + state.belt.curvature + state.cap.curvature) / 3,
            "throat_velocity": self.throat_velocity(state),
            "closed_loop_stability": 1.0 - abs(delta),
            "flux_intake": self.flux_balance(state)['intake_flux'],
            "face_radii": {
                "core": state.core.radius,
                "belt": state.belt.radius,
                "cap": state.cap.radius
            }
        }


# ParticleFlowEngine remains the same as previous version (with improved RNG)


if __name__ == '__main__':
    solver = SixCylinderBoundary()
    state = solver.compute(spin=1.8, pressure=1.1, temp=0.2, belt_mod=1.15)

    print(state.summary())
    print("Closed-Loop Delta:", f"{solver.closed_loop_delta(state):.10f}")
    
    # 3D Plot
    solver.plot_3d(state, title="Tordial 6-Cylinder Boundary (GEAR_SHIFT=1.02)")
    
    # Tordial-GS metrics
    metrics = solver.to_tordial_metrics(state)
    print("\nTordial-GS Metrics:", metrics)