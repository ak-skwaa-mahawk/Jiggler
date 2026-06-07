# intent/intent.py
from dataclasses import dataclass, field
from typing import Optional, Dict, Literal

GSRegimeBand = Literal["SUBCRITICAL", "MARGINAL", "GOLDILOCKS", "DEEP_GS"]

@dataclass
class Intent:
    """
    Sovereign Intent with support for GS-regime targeting
    and soft preferences via preference_strength.
    """
    name: str

    # Classical targets
    target_spin: Optional[float] = None
    target_pressure: Optional[float] = None
    target_temp: Optional[float] = None

    # GS-Regime targets
    gs_regime_target: Optional[GSRegimeBand] = None
    gs_direction: Optional[Literal["increase", "maintain", "decrease"]] = None
    gs_pressure_preference: Optional[float] = None
    preference_strength: float = 1.0   # 0.0 = ignore, 1.0 = hard

    # Invariants
    max_drift: float = 2.5
    max_amplification: float = 1.8
    min_stability: float = 0.92

    priority: float = 1.0
    metadata: Dict = field(default_factory=dict)

    def has_gs_target(self) -> bool:
        return any([
            self.gs_regime_target,
            self.gs_pressure_preference,
            self.gs_direction
        ])