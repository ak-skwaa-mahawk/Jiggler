import sys
import math
import time
import random
import threading
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

import numpy as np

# ── Global Repository Constraints ─────────────────────────────────────────────
TOROIDAL_ROOT = 3.1730059     
GEAR_SHIFT    = 1.02          
SHADOW        = 1.03          


# ── Baseline Data Substrates ──────────────────────────────────────────────────

@dataclass
class FaceGeometry:
    axis: str; label: str; role: str
    curvature: float; radius: float; throat: float

@dataclass
class SystemState:
    spin: float; pressure: float; temp: float; belt_mod: float
    core: FaceGeometry = field(default=None)
    belt: field(default=None)
    cap: field(default=None)
    timestamp: float = field(default_factory=time.time)

class SixCylinderBoundary:
    def __init__(self, base_radius: float = 60.0):
        self.base_radius = base_radius

    def compute(self, spin=1.5, pressure=1.0, temp=0.0, belt_mod=1.0) -> SystemState:
        spin = max(0.01, spin); pressure = max(0.01, pressure)
        core_curv = (TOROIDAL_ROOT / math.pi) * spin * SHADOW
        core_r = (self.base_radius * pressure) / core_curv
        core_throat = core_r * (1.0 - 0.15 * temp)
        core = FaceGeometry('core', 'FRONT / REAR', 'Intake · Exhaust', core_curv, core_r, core_throat)
        belt_curv = core_curv * GEAR_SHIFT * belt_mod
        belt_r = core_r * belt_curv
        belt = FaceGeometry('belt', 'LEFT / RIGHT', 'Expansion Belt', belt_curv, belt_r, belt_r)
        cap_curv = 1.0 / (belt_curv * SHADOW)
        cap_r = belt_r * cap_curv
        cap = FaceGeometry('cap', 'TOP / BOTTOM', 'Containment Caps', cap_curv, cap_r, cap_r)
        return SystemState(spin, pressure, temp, belt_mod, core, belt, cap)

    def closed_loop_delta(self, state: SystemState) -> float:
        return state.belt.curvature * state.cap.curvature * SHADOW - 1.0


@dataclass
class Particle6D:
    x: float = 0.0; y: float = 0.0; z: float = 0.0
    w: float = 0.0; v: float = 0.0; u: float = 0.0
    dx: float = 0.0; dy: float = 0.0; dz: float = 0.0
    dw: float = 0.0; dv: float = 0.0; du: float = 0.0
    phase: int = 0            # 0=INTAKE, 1=TRANSIT, 2=EXHAUST, 3=RETURN
    life: int = 0
    max_life: int = 280


# ── Repository DualRingTordialMatrix System Integration ────────────────────────

class DualRingTordialMatrix:
    """
    Simulates the repository's native coupling layer matrix. Maintains two 
    isolated concentric geometric tracks (Primary and Secondary Rings) to provide
    transparent fault-tolerant recovery loops for high-dimensional drift errors.
    """
    def __init__(self, capacity: int = 100):
        self.capacity = capacity
        # Primary Ring: Clockwise flow field mapping arrays
        self.primary_flux_sink = np.zeros((capacity, 3))
        # Secondary Ring: Counter-rotating backup absorption space (failsafe path)
        self.secondary_flux_sink = np.zeros((capacity, 3))
        
        self.total_absorbed_leakage_mass = 0.0

    def inject_leakage_flow(self, active_ring: str, particle_matrix: np.ndarray):
        """Dumps high-dimensional residual flux into the selected structural ring buffer."""
        # Calculate localized geometric bulk norm allocations
        flux_mass = np.sum(np.abs(particle_matrix[:, :3])) * 1e-4
        self.total_absorbed_leakage_mass += flux_mass
        
        # Linearly distribute positions onto ring slices based on current ring state
        if active_ring == "PRIMARY":
            # Primary ring accumulates standard drift vectors clockwise
            self.primary_flux_sink += np.mean(particle_matrix[:, :3], axis=0) * 0.01
        else:
            # Secondary ring absorbs the data via inverse, counter-rotating coordinates
            self.secondary_flux_sink -= np.mean(particle_matrix[:, :3], axis=0) * 0.01


# ── Redundant Failover Control State Machine ───────────────────────────────────

class FailoverParticleFlowEngine6D:
    def __init__(self, count: int = 300, stability_threshold: float = 0.85):
        self.count = count
        self.stability_threshold = stability_threshold
        self.particles: List[Particle6D] = []
        self._rng = random.Random(42)
        
        # Operational Mode Tracking: "ONLINE_PRIMARY" | "FAILOVER_SECONDARY"
        self.routing_state = "ONLINE_PRIMARY"
        # Dynamic modifier applied to damp mechanics in backup loops
        self.emergency_drag_override = 1.0

    def _spawn(self, radius: float) -> Particle6D:
        theta = self._rng.uniform(0, 2 * math.pi)
        return Particle6D(
            x=radius * self._rng.uniform(0.6, 0.98) * math.cos(theta),
            y=radius * r = self._rng.uniform(0.6, 0.98) * math.sin(theta),
            z=self._rng.uniform(-radius * 0.4, radius * 0.4),
            w=self._rng.uniform(-1.0, 1.0), v=self._rng.uniform(-1.0, 1.0)
        )

    def evaluate_failover_logic(self, closed_loop_stability: float):
        """Evaluates compliance parameters against current manifold integrity constraints."""
        if self.routing_state == "ONLINE_PRIMARY" and closed_loop_stability < self.stability_threshold:
            self.routing_state = "FAILOVER_SECONDARY"
            self.emergency_drag_override = 0.75  # Ramp up viscous fluid friction instantly
            print(f"⚠️ [CRITICAL] Stability Index fell to {closed_loop_stability:.4f} (< {self.stability_threshold}). ACTIVATING SECONDARY COUNTER-ROTATING FAILOVER RING.")
            
        elif self.routing_state == "FAILOVER_SECONDARY" and closed_loop_stability >= (self.stability_threshold + 0.05):
            # Enforce hysteresis margin (+0.05) to prevent network state chattering
            self.routing_state = "ONLINE_PRIMARY"
            self.emergency_drag_override = 1.0
            print(f"✅ [RECOVERY] Stability re-anchored at {closed_loop_stability:.4f}. Rerouting traffic matrices back to PRIMARY RING.")

    def step(self, state: SystemState, dt: float = 0.05):
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
            ax = ay = az = 0.0

            # ── 6D Phase Velocity Logic Modified by Failover Routing ──
            if p.phase == 0:     # INTAKE
                f_scale = -1.5 if self.routing_state == "ONLINE_PRIMARY" else -3.0
                ax = f_scale * (p.x / belt_r)
                ay = f_scale * (p.y / belt_r)
                if r < throat * 1.1: p.phase = 1
            elif p.phase == 1:   # TRANSIT
                # If we drop into failover mode, invert the flow direction around the torus
                direction_multiplier = 1.0 if self.routing_state == "ONLINE_PRIMARY" else -1.0
                ax = -1.0 * p.y * state.spin * GEAR_SHIFT * direction_multiplier
                ay = 1.0 * p.x * state.spin * GEAR_SHIFT * direction_multiplier
                if r > belt_r * 0.75: p.phase = 2
            elif p.phase == 2:   # EXHAUST
                ax = 2.0 * (p.x / (r + 1e-9)) * SHADOW
                ay = 2.0 * (p.y / (r + 1e-9)) * SHADOW
                if r > belt_r * 0.95: p.phase = 3
            elif p.phase == 3:   # RETURN
                ax = -2.5 * p.x
                ay = -2.5 * p.y
                if r < throat * 1.4: p.phase = 0

            # Kinematic Euler updates
            p.dx += ax * dt; p.dy += ay * dt
            
            # Apply base system drag compounded by emergency dampening metrics
            drag_coefficient = (1.0 - (0.04 * state.pressure)) * self.emergency_drag_override
            p.dx *= drag_coefficient; p.dy *= drag_coefficient
            
            p.x += p.dx; p.y += p.dy
            live.append(p)
            
        self.particles = live

    def extract_numpy_matrix(self) -> np.ndarray:
        return np.array([[p.x, p.y, p.z] for p in self.particles])


# ── Execution Harness ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🚀 Mounting Dual-Ring Redundant Failover Management Mesh...")
    
    # Instantiate functional blocks
    solver = SixCylinderBoundary(base_radius=50.0)
    failover_engine = FailoverParticleFlowEngine6D(count=150, stability_threshold=0.88)
    dual_ring_matrix = DualRingTordialMatrix(capacity=100)

    # Induce an execution path sequence across 15 cycles
    for cycle in range(1, 16):
        # Artificially alter geometry variables to force containment breakdown
        if cycle >= 6 and cycle <= 11:
            # Emulate micro-layer turbulence by inflating spin and dropping pressure
            active_spin = 4.2 
            active_belt_mod = 0.45  # Induces high closed-loop deviation error
        else:
            active_spin = 1.5
            active_belt_mod = 1.0   # Resynchronizes closed-loop stability parameters

        # 1. Compute geometry states
        state = solver.compute(spin=active_spin, belt_mod=active_belt_mod)
        metrics = solver.to_toroidal_metrics(state)
        stability_index = metrics["closed_loop_stability"]

        # 2. Process metrics through the failover state machine validation logic
        failover_engine.evaluate_failover_logic(stability_index)

        # 3. Step particle flow engine physics
        failover_engine.step(state, dt=0.05)
        raw_particles = failover_engine.extract_numpy_matrix()

        # 4. Route extracted flow parameters to the active target ring
        target_ring_channel = "PRIMARY" if failover_engine.routing_state == "ONLINE_PRIMARY" else "SECONDARY"
        dual_ring_matrix.inject_leakage_flow(target_ring_channel, raw_particles)

        # Output telemetry frame summaries

print(f" Frame {cycle:02d} | Stability: {stability_index:.4f} | Route: {failover_engine.routing_state:<20} | Absorbed Mass Sink: {dual_ring_matrix.total_absorbed_leakage_mass:.4f}")time.sleep(0.1)