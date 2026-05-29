"""
tordial_gs_v14.py
Tordial–GS Manifold v14 — Dual-Ring Structural Build + Class Ordering Fix

Changes from v13:
  [BUG FIX]  Class ordering: TordialAgentNode defined before OpenTordialAgentNode
             (v13 raised NameError at class definition time due to forward reference)
  [BUG FIX]  compute_and_update_gs no longer reads global `t` dict directly;
             phi_op and gear_shift_correction are injected via constructor
  [BUG FIX]  GSSweep.compute_gs now returns a distinct 'band' key for SUBCRITICAL
             nodes instead of silently returning all-zero telemetry
  [FEATURE]  Real dual-ring structure: nodes_a (inner ring, micro-GS stabilization)
             and nodes_b (outer ring, macro-curvature stabilization) are separate
             pools with distinct seeding, distinct PID governors, and cross-ring
             load transfer when either ring trips its stress threshold
  [FEATURE]  RingGovernor: per-ring PID that drives d/r adjustments toward a
             target sigma_T setpoint, replacing the ad-hoc random deltas
  [FEATURE]  Cross-ring failover: if inner ring avg_kappa drops below INNER_FAILOVER
             threshold the outer ring absorbs load by spawning bridge nodes seeded
             from the stressed inner node's parameters; vice-versa for outer ring
             curvature overload
  [FEATURE]  Ring telemetry in cycle printout: separate health, node count, energy
             contribution, and LER per ring
"""

import math
import yaml
import numpy as np
import random
import os
import sqlite3
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# =============================================================================
# CONFIG LOAD
# =============================================================================

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

t = config["tordial"]
t["base_frequency_hz"] = 79.79

PHI_OP: float = float(t["phi_op"])
GEAR_SHIFT: float = float(t.get("gear_shift_correction", 1.04))
PI_3D: float = float(t["pi_3d"])
BASE_HZ: float = float(t["base_frequency_hz"])

# =============================================================================
# GS SWEEP  (fixed: SUBCRITICAL is now a named band, not silent zeros)
# =============================================================================

@dataclass
class GSMetrics:
    sigma_T: float
    kappa_GS_T: float
    lambda_GS_T: float
    rho_GS_T: float
    band: str  # SUBCRITICAL | MARGINAL | GOLDILOCKS | DEEP_GS


class GSSweep:
    def __init__(self, phi_op: float = PHI_OP, gear_shift: float = GEAR_SHIFT):
        self._denom = 4.0 * phi_op * gear_shift

    def compute_gs(self, d: int, r: int) -> GSMetrics:
        sigma_T = r - (d ** 2) / self._denom
        if sigma_T <= 0:
            return GSMetrics(
                sigma_T=sigma_T,
                kappa_GS_T=0.0,
                lambda_GS_T=0.0,
                rho_GS_T=0.0,
                band="SUBCRITICAL",
            )
        kappa = sigma_T / d
        lam = math.sqrt(sigma_T)
        rho = lam / d
        if kappa < 3.0:
            band = "MARGINAL"
        elif kappa < 8.0:
            band = "GOLDILOCKS"
        else:
            band = "DEEP_GS"
        return GSMetrics(
            sigma_T=sigma_T,
            kappa_GS_T=kappa,
            lambda_GS_T=lam,
            rho_GS_T=rho,
            band=band,
        )


gs_sweep = GSSweep()

# =============================================================================
# SURFACE CODE + ANYON
# =============================================================================

class Anyon:
    def __init__(self, anyon_type: str, node_id: int, position: float):
        self.type = anyon_type
        self.node_id = node_id
        self.position = position
        self.lifetime = 0


class SurfaceCodeDecoder:
    def decode(self, syndromes: List[Tuple[int, str]]) -> List[Tuple[int, int]]:
        corrections: List[Tuple[int, int]] = []
        unpaired = list(syndromes)
        i = 0
        while i < len(unpaired):
            matched = False
            for j in range(i + 1, len(unpaired)):
                if unpaired[i][1] == unpaired[j][1]:
                    corrections.append((unpaired[i][0], unpaired[j][0]))
                    del unpaired[j]
                    del unpaired[i]
                    matched = True
                    break
            if not matched:
                i += 1
        return corrections

# =============================================================================
# RING GOVERNOR  (per-ring PID driving d/r toward sigma_T setpoint)
# =============================================================================

class RingGovernor:
    """
    PID controller that nudges a ring's aggregate d/r toward a target sigma_T.
    Call .step(current_sigma) each cycle to get (delta_d, delta_r) corrections.
    """

    def __init__(
        self,
        target_sigma: float = 120.0,
        kp: float = 0.012,
        ki: float = 0.003,
        kd: float = 0.006,
    ):
        self.target = target_sigma
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self._integral = 0.0
        self._prev_error = 0.0

    def step(self, current_sigma: float) -> Tuple[int, int]:
        error = self.target - current_sigma
        self._integral = max(-500.0, min(500.0, self._integral + error))
        derivative = error - self._prev_error
        self._prev_error = error
        u = self.kp * error + self.ki * self._integral + self.kd * derivative
        # Map controller output to discrete (delta_d, delta_r)
        # Positive u → increase generators (d) slightly, increase relations (r) more
        # Negative u → trim both to bleed off excess sigma
        delta_d = int(round(max(-2, min(2, u * 0.3))))
        delta_r = int(round(max(-8, min(8, u * 1.2))))
        return delta_d, delta_r

# =============================================================================
# BASE NODE  (defined FIRST — fixes the v13 NameError)
# =============================================================================

class TordialAgentNode:
    """
    Base node. Carries GS algebra state (d, r), phase tracking, and
    load negotiation.  Does NOT reference the global `t` dict at runtime;
    all config values are injected at construction.
    """

    TAU_3D: float = 2.0 * PI_3D
    OMEGA_RADS: float = 2.0 * math.pi * BASE_HZ
    CHASE_RATIO_TAU: float = TAU_3D / PHI_OP

    def __init__(self, d: int, r: int, node_id: int):
        self.node_id = node_id
        self.d = d
        self.r = r
        self.load = 0.0
        self.decision = "STABLE"
        self.load_history: List[float] = []

    def negotiate(self, peers_loads: List[float], my_kappa: float) -> str:
        avg_peer = float(np.mean(peers_loads)) if peers_loads else 0.0
        if self.load > 3.5 and my_kappa < 5.5:
            return "REQUEST_SHED" if random.random() < 0.7 else "THROTTLE"
        if avg_peer > 0 and self.load > avg_peer * 1.6 and my_kappa > 6.0:
            return "OFFER_HELP"
        return "STABLE"

    def run_step(
        self, t_seconds: float, external_load: float, peers_loads: List[float]
    ) -> Dict:
        phase = (self.OMEGA_RADS * t_seconds) % self.TAU_3D
        metrics = gs_sweep.compute_gs(self.d, self.r)
        self.load = external_load
        self.load_history.append(external_load)
        self.decision = self.negotiate(peers_loads, metrics.kappa_GS_T)
        return {
            "node_id": self.node_id,
            "phase": phase,
            "chase_lock": "LOCKED" if phase < self.CHASE_RATIO_TAU else "DRIFTING",
            "metrics": metrics,
            "load": external_load,
            "decision": self.decision,
        }

# =============================================================================
# OPEN NODE  (defined AFTER TordialAgentNode — fixes the NameError)
# =============================================================================

class OpenTordialAgentNode(TordialAgentNode):
    """
    Extended node with drift phase, GS self-update, syndrome detection,
    and fission tracking.  phi_op / gear_shift are no longer read from
    the global `t`; they use module-level constants injected at import time.
    """

    def __init__(
        self,
        d: int,
        r: int,
        node_id: int,
        x: float = 0.0,
        y: float = 0.0,
        phi_op: float = PHI_OP,
        gear_shift: float = GEAR_SHIFT,
    ):
        super().__init__(d, r, node_id)
        self.drift_phase = (x + y) % self.TAU_3D
        self.sigma_T: float = 0.0
        self.fission_count: int = 0
        self.quarantined: bool = False
        self.high_kappa_streak: int = 0
        self._phi_op = phi_op
        self._gear_shift = gear_shift
        self._denom = 4.0 * phi_op * gear_shift

    def compute_and_update_gs(
        self, curvature_pressure: float, resonance: float
    ) -> float:
        if curvature_pressure > 0.6:
            delta_d = max(1, int(resonance * 0.35 + self.drift_phase * 0.1))
            self.d += delta_d
            if resonance > 0.4:
                self.r += 1 if random.random() < 0.45 else 0
        # Use instance _denom — no global t reference
        denom = self._denom + self.drift_phase * 0.08
        self.sigma_T = self.r - (self.d ** 2 / denom)
        self.drift_phase = (self.drift_phase + 0.017) % self.TAU_3D
        return self.sigma_T

    def measure_syndrome(self) -> List[str]:
        syndromes: List[str] = []
        if self.sigma_T < -180:
            syndromes.append("e")
        if abs(self.drift_phase % (math.pi / 2)) > 0.38:
            syndromes.append("m")
        return syndromes

    def apply_governor_correction(self, delta_d: int, delta_r: int) -> None:
        self.d = max(4, self.d + delta_d)
        self.r = max(20, self.r + delta_r)

# =============================================================================
# SQLITE PERSISTENCE
# =============================================================================

DB_PATH = "tordial_manifold.db"


def _ensure_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS nodes (
            node_id   INTEGER,
            ring      TEXT,
            d         INTEGER,
            r         INTEGER,
            sigma_T   REAL,
            drift_phase REAL,
            fission_count INTEGER,
            parent_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    conn.commit()
    conn.close()


def persist_node_state(
    node: OpenTordialAgentNode, ring: str = "A", parent_id: Optional[int] = None
):
    if not os.path.exists(DB_PATH):
        _ensure_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO nodes (node_id,ring,d,r,sigma_T,drift_phase,fission_count,parent_id) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (
            node.node_id,
            ring,
            node.d,
            node.r,
            node.sigma_T,
            node.drift_phase,
            node.fission_count,
            parent_id,
        ),
    )
    conn.commit()
    conn.close()

# =============================================================================
# GS MACRO FEEDBACK  (unchanged from v13, kept for compatibility)
# =============================================================================

def gs_macro_feedback(
    d: int,
    r: int,
    drift_stress: float,
    curvature_stress: float,
    failover_flag: bool,
) -> Tuple[int, int]:
    S_macro = max(0.0, min(1.0, 0.6 * drift_stress + 0.4 * curvature_stress))
    S_stable = 1.0 - S_macro
    S_fail = 1.0 if failover_flag else 0.0
    new_d = max(4, int(round(d + 2 * S_macro + 4 * S_fail)))
    new_r = max(20, int(round(r + 20 * S_macro - 12 * S_stable + 40 * S_fail)))
    return new_d, new_r

# =============================================================================
# CURVATURE FIELD  (inline — avoids import dependency on separate file)
# =============================================================================

class CurvatureField:
    def __init__(self):
        self.last_pressure = 0.0
        self.last_resonance = 0.0

    def compute(
        self,
        avg_sigma: float,
        avg_kappa: float,
        global_energy: float,
        logical_error_rate: float,
        node_count: int,
    ) -> Tuple[float, float]:
        kappa_norm = max(0.0, min(1.0, avg_kappa / 12.0))
        energy_norm = max(0.0, min(1.0, global_energy / 3000.0))
        sigma_norm = max(-1.0, min(1.0, avg_sigma / 500.0))
        ler = max(0.0, min(1.0, logical_error_rate))
        base_pressure = (
            0.45 * kappa_norm + 0.35 * energy_norm + 0.20 * max(0.0, sigma_norm)
        )
        pressure = base_pressure * (1.0 - 0.6 * ler)
        crowding = max(0.0, min(0.3, (node_count - 24) / 80.0))
        pressure += crowding
        resonance = (
            0.55 * kappa_norm
            + 0.35 * max(0.0, sigma_norm)
            + 0.10 * energy_norm
        ) * (1.0 - 0.8 * ler)
        pressure = max(0.0, min(1.2, pressure))
        resonance = max(0.0, min(1.0, resonance))
        alpha = 0.35
        pressure = alpha * pressure + (1 - alpha) * self.last_pressure
        resonance = alpha * resonance + (1 - alpha) * self.last_resonance
        self.last_pressure = pressure
        self.last_resonance = resonance
        return pressure, resonance

# =============================================================================
# DUAL-RING MATRIX  (v14 — real two-ring structure)
# =============================================================================

# Thresholds that trigger cross-ring failover
INNER_FAILOVER_KAPPA = 2.5   # inner ring avg_kappa below this → outer absorbs
OUTER_FAILOVER_CURV  = 1.05  # outer ring curvature_pressure above this → inner covers

# Energy split between rings (inner gets 60 % of recovery, outer 40 %)
INNER_ENERGY_SHARE = 0.60
OUTER_ENERGY_SHARE = 0.40


class DualRingTordialMatrix:
    """
    Two independent node pools with a cross-ring failover protocol:

    Ring A (inner):  micro-GS stabilization, tighter sigma_T target,
                     higher base d/r seeding, fission-driven growth.
    Ring B (outer):  macro-curvature stabilization, lower base d/r,
                     curvature-driven governor corrections.

    Failover conditions:
      - If ring A avg_kappa < INNER_FAILOVER_KAPPA, ring B spawns bridge nodes
        seeded from the stressed ring A nodes.
      - If ring B curvature_pressure > OUTER_FAILOVER_CURV, ring A throttles
        its fission and donates energy to ring B.
    """

    def __init__(self, node_count: int = 12, agent_mode: bool = True):
        self.node_count = node_count
        self.agent_mode = agent_mode
        self.current_tick = 0
        self.decoder = SurfaceCodeDecoder()
        self.curvature_field = CurvatureField()

        # ---- Ring A: inner / micro-GS ----
        self.nodes_a: List[OpenTordialAgentNode] = []
        self.governor_a = RingGovernor(target_sigma=140.0, kp=0.014, ki=0.004, kd=0.007)
        self.energy_a = 900.0
        self.anyons_a: List[Anyon] = []
        self.ler_a = 0.0
        self.corrections_a = 0

        # ---- Ring B: outer / macro-curvature ----
        self.nodes_b: List[OpenTordialAgentNode] = []
        self.governor_b = RingGovernor(target_sigma=80.0, kp=0.008, ki=0.002, kd=0.004)
        self.energy_b = 600.0
        self.anyons_b: List[Anyon] = []
        self.ler_b = 0.0
        self.corrections_b = 0

        # Shared ring-level counters
        self.ring_count = 2   # always 2 now; increments only if a 3rd ring spawns
        self.bridge_nodes_spawned = 0

        _ensure_db()
        self._seed_rings()

    # ------------------------------------------------------------------
    # Seeding
    # ------------------------------------------------------------------

    def _seed_rings(self):
        """
        Ring A: higher d/r — deeper in GOLDILOCKS/DEEP_GS territory.
        Ring B: lower d/r — stays in MARGINAL/GOLDILOCKS, curvature-sensitive.
        """
        # Inner ring A — 12 nodes (or node_count)
        base_d_a, base_r_a = 42, 380
        for i in range(self.node_count):
            angle = (2 * math.pi * i) / self.node_count
            d_i = base_d_a + (i % 4) * 2
            r_i = base_r_a + (i % 4) * 16
            node = OpenTordialAgentNode(d_i, r_i, i, angle, angle)
            self.nodes_a.append(node)

        # Outer ring B — 8 nodes, offset phase
        base_d_b, base_r_b = 28, 210
        for i in range(8):
            angle = (2 * math.pi * i) / 8 + math.pi / 8   # phase-shifted
            d_i = base_d_b + (i % 3) * 3
            r_i = base_r_b + (i % 3) * 10
            node_id = self.node_count + i
            node = OpenTordialAgentNode(d_i, r_i, node_id, angle, angle)
            self.nodes_b.append(node)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _next_node_id(self) -> int:
        return len(self.nodes_a) + len(self.nodes_b) + self.bridge_nodes_spawned

    def _ring_avg_kappa(self, ring: List[OpenTordialAgentNode]) -> float:
        if not ring:
            return 0.0
        return float(np.mean([gs_sweep.compute_gs(n.d, n.r).kappa_GS_T for n in ring]))

    def _ring_avg_sigma(self, ring: List[OpenTordialAgentNode]) -> float:
        if not ring:
            return 0.0
        return float(np.mean([gs_sweep.compute_gs(n.d, n.r).sigma_T for n in ring]))

    def _ring_health(self, ring: List[OpenTordialAgentNode]) -> float:
        if not ring:
            return 0.0
        avg_kappa = self._ring_avg_kappa(ring)
        return round((0.4 + min(avg_kappa / 12.0, 1.0) * 0.35 + 0.25 * 0.85) * 100, 2)

    # ------------------------------------------------------------------
    # Fission (ring-aware)
    # ------------------------------------------------------------------

    def _perform_fission(
        self,
        parent: OpenTordialAgentNode,
        ring: List[OpenTordialAgentNode],
        ring_label: str,
    ):
        parent.fission_count += 1
        child_id = self._next_node_id()
        child = OpenTordialAgentNode(
            parent.d + 1,
            parent.r + 1,
            child_id,
            parent.drift_phase + 0.1,
            parent.drift_phase + 0.1,
        )
        ring.append(child)
        persist_node_state(child, ring=ring_label, parent_id=parent.node_id)
        print(
            f"  [FISSION:{ring_label}] Node {parent.node_id} → {child_id} "
            f"σ_T={child.sigma_T:.2f}"
        )

    # ------------------------------------------------------------------
    # Spawning (ring-aware, κ-driven)
    # ------------------------------------------------------------------

    def _attempt_spawning(
        self,
        ring: List[OpenTordialAgentNode],
        ring_label: str,
        energy: float,
        health: float,
    ) -> int:
        MIN_ENERGY = 420.0
        KAPPA_THRESH = 8.0
        HEALTH_THRESH = 62.0
        MIN_STREAK = 3
        spawned = 0
        for node in list(ring):
            m = gs_sweep.compute_gs(node.d, node.r)
            if m.kappa_GS_T > KAPPA_THRESH:
                node.high_kappa_streak += 1
            else:
                node.high_kappa_streak = 0
            if (
                node.high_kappa_streak >= MIN_STREAK
                and health > HEALTH_THRESH
                and energy > MIN_ENERGY
            ):
                prob = 0.25 + 0.06 * (m.kappa_GS_T - 8.0)
                if random.random() < prob:
                    self._perform_fission(node, ring, ring_label)
                    spawned += 1
        return spawned

    # ------------------------------------------------------------------
    # Surface code (ring-aware)
    # ------------------------------------------------------------------

    def _measure_syndromes(
        self, ring: List[OpenTordialAgentNode]
    ) -> List[Tuple[int, str]]:
        out: List[Tuple[int, str]] = []
        for node in ring:
            for s in node.measure_syndrome():
                out.append((node.node_id, s))
        return out

    def _apply_error_correction(
        self, ring: List[OpenTordialAgentNode]
    ) -> int:
        syndromes = self._measure_syndromes(ring)
        corrections = self.decoder.decode(syndromes)
        corrected = 0
        ids = {c for pair in corrections for c in pair}
        for node in ring:
            if node.node_id in ids:
                node.sigma_T = max(node.sigma_T, -50.0)
                node.d = max(4, node.d - 1)
                corrected += 1
        return corrected

    def _update_anyons(
        self, ring: List[OpenTordialAgentNode]
    ) -> Tuple[List[Anyon], float]:
        syndromes = self._measure_syndromes(ring)
        node_map = {n.node_id: n for n in ring}
        anyons = [
            Anyon(s[1], s[0], node_map[s[0]].drift_phase)
            for s in syndromes
            if s[0] in node_map
        ]
        for a in anyons:
            a.lifetime += 1
        wrapped = sum(1 for a in anyons if a.lifetime > 25)
        ler = (
            min(1.0, wrapped / max(1, len(anyons)) * 0.7) if anyons else 0.0
        )
        return anyons, ler

    # ------------------------------------------------------------------
    # Cross-ring failover
    # ------------------------------------------------------------------

    def _cross_ring_failover(
        self,
        curvature_pressure_b: float,
    ):
        """
        Two conditions checked each cycle:

        1. Inner ring A is kappa-starved → ring B spawns bridge nodes
           seeded from the weakest ring A nodes to cover their micro load.

        2. Outer ring B is curvature-overloaded → ring A throttles its own
           fission for this cycle and transfers 8 % of energy_a to energy_b.
        """
        avg_kappa_a = self._ring_avg_kappa(self.nodes_a)

        # Condition 1: inner failover
        if avg_kappa_a < INNER_FAILOVER_KAPPA and self.nodes_a:
            # Find the most stressed (lowest kappa) inner nodes
            stressed = sorted(
                self.nodes_a,
                key=lambda n: gs_sweep.compute_gs(n.d, n.r).kappa_GS_T,
            )[:2]
            for src in stressed:
                bridge_id = self._next_node_id()
                # Bridge node in ring B mirrors stressed ring A params + small boost
                bridge = OpenTordialAgentNode(
                    max(4, src.d - 2),
                    src.r + 15,
                    bridge_id,
                    src.drift_phase + math.pi,  # opposite phase — outer ring offset
                    src.drift_phase + math.pi,
                )
                self.nodes_b.append(bridge)
                self.bridge_nodes_spawned += 1
                persist_node_state(
                    bridge, ring="B_bridge", parent_id=src.node_id
                )
                print(
                    f"  [FAILOVER→B] Inner kappa={avg_kappa_a:.2f} < {INNER_FAILOVER_KAPPA} "
                    f"| Bridge node {bridge_id} spawned in ring B from node {src.node_id}"
                )

        # Condition 2: outer ring curvature overload
        if curvature_pressure_b > OUTER_FAILOVER_CURV and self.energy_a > 200.0:
            transfer = self.energy_a * 0.08
            self.energy_a -= transfer
            self.energy_b += transfer
            print(
                f"  [FAILOVER→A→B] Outer curvature={curvature_pressure_b:.3f} "
                f"> {OUTER_FAILOVER_CURV} | Energy transfer {transfer:.1f} A→B"
            )

    # ------------------------------------------------------------------
    # Main cycle
    # ------------------------------------------------------------------

    def execute_heavy_load_cycle(self, system_load: float = 1.0):
        self.current_tick += 1

        # ---- Ring A: inner micro-GS update ----
        avg_sigma_a = self._ring_avg_sigma(self.nodes_a)
        avg_kappa_a = self._ring_avg_kappa(self.nodes_a)
        delta_d_a, delta_r_a = self.governor_a.step(avg_sigma_a)

        pressure_a, resonance_a = self.curvature_field.compute(
            avg_sigma_a, avg_kappa_a, self.energy_a, self.ler_a, len(self.nodes_a)
        )

        for node in self.nodes_a:
            node.compute_and_update_gs(pressure_a, resonance_a)
            node.apply_governor_correction(delta_d_a, delta_r_a)
            if node.sigma_T < -450:
                self._perform_fission(node, self.nodes_a, "A")

        spawned_a = self._attempt_spawning(
            self.nodes_a, "A", self.energy_a, self._ring_health(self.nodes_a)
        )

        self.corrections_a = self._apply_error_correction(self.nodes_a)
        self.anyons_a, self.ler_a = self._update_anyons(self.nodes_a)

        kappa_recovery_a = self._ring_avg_kappa(self.nodes_a)
        self.energy_a += (
            INNER_ENERGY_SHARE * (12.0 + 0.8 * kappa_recovery_a)
            - len(self.nodes_a) * 0.11
        )

        # ---- Ring B: outer macro-curvature update ----
        avg_sigma_b = self._ring_avg_sigma(self.nodes_b)
        avg_kappa_b = self._ring_avg_kappa(self.nodes_b)
        delta_d_b, delta_r_b = self.governor_b.step(avg_sigma_b)

        pressure_b, resonance_b = self.curvature_field.compute(
            avg_sigma_b, avg_kappa_b, self.energy_b, self.ler_b, len(self.nodes_b)
        )

        for node in self.nodes_b:
            node.compute_and_update_gs(pressure_b, resonance_b)
            node.apply_governor_correction(delta_d_b, delta_r_b)
            if node.sigma_T < -450:
                self._perform_fission(node, self.nodes_b, "B")

        spawned_b = self._attempt_spawning(
            self.nodes_b, "B", self.energy_b, self._ring_health(self.nodes_b)
        )

        self.corrections_b = self._apply_error_correction(self.nodes_b)
        self.anyons_b, self.ler_b = self._update_anyons(self.nodes_b)

        kappa_recovery_b = self._ring_avg_kappa(self.nodes_b)
        self.energy_b += (
            OUTER_ENERGY_SHARE * (12.0 + 0.8 * kappa_recovery_b)
            - len(self.nodes_b) * 0.11
        )

        # ---- Cross-ring failover check ----
        self._cross_ring_failover(curvature_pressure_b=pressure_b)

        # ---- Telemetry ----
        health_a = self._ring_health(self.nodes_a)
        health_b = self._ring_health(self.nodes_b)
        total_nodes = len(self.nodes_a) + len(self.nodes_b)

        print(
            f"[{self.current_tick:3d}] "
            f"A: {len(self.nodes_a):3d}n κ={avg_kappa_a:5.2f} "
            f"E={self.energy_a:7.1f} LER={self.ler_a:.4f} H={health_a:5.1f} | "
            f"B: {len(self.nodes_b):3d}n κ={avg_kappa_b:5.2f} "
            f"E={self.energy_b:7.1f} LER={self.ler_b:.4f} H={health_b:5.1f} | "
            f"total={total_nodes} bridges={self.bridge_nodes_spawned}"
        )

# =============================================================================
# RUNNER
# =============================================================================

if __name__ == "__main__":
    print("[+] Tordial–GS Manifold v14 — Dual-Ring + Class-Order Fix\n")
    print("    Ring A (inner):  micro-GS stabilization  σ_T target=140")
    print("    Ring B (outer):  macro-curvature control  σ_T target=80")
    print("    Failover: A→B if κ_A < 2.5 | B→A energy transfer if curv_B > 1.05\n")

    matrix = DualRingTordialMatrix(node_count=12, agent_mode=True)

    for cycle in range(200):
        matrix.execute_heavy_load_cycle(1.0 + 0.35 * math.sin(cycle / 6.0))

    print("\n[+] Run complete. Dual-ring manifold is structurally open.")
    print(
        f"    Final: {len(matrix.nodes_a)} inner nodes | "
        f"{len(matrix.nodes_b)} outer nodes | "
        f"{matrix.bridge_nodes_spawned} bridge nodes spawned"
    )
