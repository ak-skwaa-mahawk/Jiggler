# jed_pid_bandit.py

from dataclasses import dataclass, field
import math
from pid_gain_space import PID_GAIN_CANDIDATES, PIDGains

@dataclass
class GainStats:
    count: int = 0
    total_reward: float = 0.0

    @property
    def mean_reward(self) -> float:
        if self.count == 0:
            return 0.0
        return self.total_reward / self.count

@dataclass
class PIDBandit:
    gains_stats: dict = field(default_factory=lambda: {
        i: GainStats() for i in range(len(PID_GAIN_CANDIDATES))
    })
    total_pulls: int = 0

def select_gain_index_ucb(bandit: PIDBandit) -> int:
    bandit.total_pulls += 1
    t = bandit.total_pulls

    best_idx = None
    best_score = float("-inf")

    for idx, stats in bandit.gains_stats.items():
        if stats.count == 0:
            return idx  # force exploration

        ucb = stats.mean_reward + math.sqrt(2.0 * math.log(t) / stats.count)
        if ucb > best_score:
            best_score = ucb
            best_idx = idx

    return best_idx

def update_pid_bandit(bandit: PIDBandit, idx: int, reward: float):
    stats = bandit.gains_stats[idx]
    stats.count += 1
    stats.total_reward += reward

def get_gains_for_index(idx: int) -> PIDGains:
    return PID_GAIN_CANDIDATES[idx]