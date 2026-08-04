# jed_bandit.py

from dataclasses import dataclass, field
import math
import random

GS_REGIMES = ["SUBCRITICAL", "EDGE_GS", "DEEP_GS"]

@dataclass
class RegimeStats:
    count: int = 0
    total_reward: float = 0.0

    @property
    def mean_reward(self) -> float:
        if self.count == 0:
            return 0.0
        return self.total_reward / self.count

@dataclass
class RegimeBandit:
    regimes: dict = field(default_factory=lambda: {r: RegimeStats() for r in GS_REGIMES})
    total_pulls: int = 0
def select_regime_ucb(bandit: RegimeBandit) -> str:
    bandit.total_pulls += 1
    t = bandit.total_pulls

    best_regime = None
    best_score = float("-inf")

    for regime, stats in bandit.regimes.items():
        if stats.count == 0:
            # Force exploration
            return regime

        ucb = stats.mean_reward + math.sqrt(2.0 * math.log(t) / stats.count)
        if ucb > best_score:
            best_score = ucb
            best_regime = regime

    return best_regime
def update_regime_bandit(bandit: RegimeBandit, regime: str, reward: float):
    stats = bandit.regimes[regime]
    stats.count += 1
    stats.total_reward += reward
# jed_autonomous.py (conceptual)

from jed_bandit import select_regime_ucb
from jed_persistent_state import load_regime_bandit

def generate_plan(intent, snapshot, memory) -> JEDPlan:
    bandit = load_regime_bandit(memory)

    suggested_regime = select_regime_ucb(bandit)

    # Optionally clamp by safety:
    safe_regime = enforce_safety_on_regime(
        suggested_regime,
        snapshot,
        memory
    )

    plan = JEDPlan(
        gs_regime=safe_regime,
        drift_budget=compute_drift_budget(intent, snapshot, memory),
        curvature_profile=compute_curvature_profile(intent, snapshot, memory),
        node_policy=compute_node_policy(intent, snapshot, memory),
        safety_profile=compute_safety_profile(intent, snapshot, memory),
        horizon_steps=compute_horizon(intent, snapshot, memory),
    )
    return plan

# jed_anomaly_response.py (conceptual)

from jed_bandit import update_regime_bandit
from jed_persistent_state import load_regime_bandit, save_regime_bandit

def compute_scores(plan, before, after):
    stability = compute_stability_score(before, after)
    safety = compute_safety_score(before, after)
    performance = compute_performance_score(before, after)
    return stability, safety, performance

def compute_reward(stability, safety, performance,
                   alpha=0.4, beta=0.4, gamma=0.2):
    return alpha * stability + beta * safety + gamma * performance

def evaluate_transition(plan, before, after, memory):
    stability, safety, performance = compute_scores(plan, before, after)
    reward = compute_reward(stability, safety, performance)

    bandit = load_regime_bandit(memory)
    update_regime_bandit(bandit, plan.gs_regime, reward)
    save_regime_bandit(memory, bandit)

    # existing anomaly logic + result struct
    result = CriticResult(
        score=reward,
        stability_score=stability,
        safety_score=safety,
        performance_score=performance,
        anomalies=detect_anomalies(before, after),
        policy_adjustments={},  # can be filled later
    )
    return result

def compute_safety_score(before, after):
    # Example:
    if after.safety_state["hard_trip"]:
        return 0.0
    if after.safety_state["near_trip"]:
        return 0.2
    return 1.0
{
  "regime_bandit": {
    "SUBCRITICAL": {"count": 42, "total_reward": 30.5},
    "EDGE_GS":     {"count": 37, "total_reward": 35.2},
    "DEEP_GS":     {"count": 10, "total_reward": 4.1},
    "total_pulls": 89
  },
  ...
}


