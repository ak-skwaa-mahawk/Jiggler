# pwc/types.py
from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID, uuid4

# Import substrate types (you’ll adapt these imports to your actual modules)
from tordial_gs_v15 import GSState  # or your canonical GS state class
from SystemicTordialMatrix import ManifoldState  # adapt to your actual type
from global_PID import PIDState
from Production_Lifecycle_Framework import LifecycleState
from Asynchronous_Telemetry_Architecture import TelemetryRecord
from Automated_Asynchronous_Safety_Trip_Matrix import SafetyFlags


@dataclass
class DriftEnvelope:
    max_drift: float
    preferred_drift: float
    time_horizon: float


@dataclass
class CurvatureProfile:
    target_curvature_field: list[float]  # flattened 2D
    tolerance: float


@dataclass
class PressureBudget:
    global_budget: float
    per_region_budget: list[float]  # flattened 2D
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


@dataclass
class PlannerContext:
    gs_state: GSState
    manifold_state: ManifoldState
    pid_state: PIDState
    lifecycle_state: LifecycleState
    recent_telemetry: List[TelemetryRecord]


@dataclass
class ExternalObjective:
    target_mode: str
    priority_safety: float
    priority_efficiency: float
    priority_exploration: float