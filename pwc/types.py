# pwc/types.py
from dataclasses import dataclass
from typing import List, Optional, Dict
from uuid import UUID, uuid4

# Import the real substrate types from six_cylinder_boundary.py
from six_cylinder_boundary import (
    GSState,
    ManifoldState,
    PIDState,
    SafetyFlags,
    LifecycleState,
)

# ============================================================
# Core Planning & Control Types
# ============================================================

@dataclass
class DriftEnvelope:
    max_drift: float
    preferred_drift: float
    time_horizon: float


@dataclass
class CurvatureProfile:
    target_curvature_field: list[float]
    tolerance: float


@dataclass
class PressureBudget:
    global_budget: float
    per_region_budget: list[float]
    time_horizon: float


@dataclass
class SafetyPosture:
    max_trip_rate: float
    hard_quarantine_allowed: bool
    degradation_preferred: bool


@dataclass
class ManifoldPlan:
    id: UUID
    drift_envelope: DriftEnvelope
    curvature_profile: CurvatureProfile
    pressure_budget: PressureBudget
    safety_posture: SafetyPosture
    horizon_steps: int
    topological_guidance: Optional[Dict] = None


@dataclass
class RegionalControlOverride:
    region_id: int
    pressure_cap: float
    relaxation_strength: float


@dataclass
class ControlStep:
    tick_index: int
    pid_target_drift: float
    pressure_cap_global: float
    relaxation_strength_global: float
    regional_overrides: List[RegionalControlOverride]


@dataclass
class ControlSchedule:
    plan_id: UUID
    steps: List[ControlStep]


# ============================================================
# Trajectory & Scoring Types
# ============================================================

@dataclass
class TrajectorySample:
    tick_index: int
    gs_state: GSState
    manifold_state: ManifoldState
    pid_state: PIDState
    safety_flags: SafetyFlags


@dataclass
class Trajectory:
    plan_id: UUID
    samples: List[TrajectorySample]


@dataclass
class Violation:
    tick_index: int
    type: str
    severity: float
    details: str


@dataclass
class TrajectoryScore:
    plan_id: UUID
    stability_score: float
    safety_score: float
    efficiency_score: float
    integrity_score: float
    overall_score: float
    violations: List[Violation]


# ============================================================
# Context & Objective Types
# ============================================================

@dataclass
class PlannerContext:
    gs_state: GSState
    manifold_state: ManifoldState
    pid_state: PIDState
    lifecycle_state: LifecycleState
    recent_telemetry: List[dict]


@dataclass
class ExternalObjective:
    target_mode: str
    priority_safety: float
    priority_efficiency: float
    priority_exploration: float
