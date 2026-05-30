# pwc/critic.py
from .types import *
import numpy as np


class Critic:
    def evaluate(self, trajectory: Trajectory) -> TrajectoryScore:
        spins = [s.snapshot.gs_state.spin for s in trajectory.samples]
        pressures = [s.snapshot.gs_state.pressure for s in trajectory.samples]
        temps = [s.snapshot.gs_state.temp for s in trajectory.samples]

        safeties = [s.snapshot.safety_flags for s in trajectory.samples]

        # Stability = inverse variance of spin/pressure/temp
        stability = 1.0 / (1.0 + np.var(spins) + np.var(pressures) + np.var(temps))

        # Safety = fraction of ticks without warnings
        safe_ticks = sum(1 for f in safeties if not (
            f.delta_violation or f.stability_warning or f.pressure_cap_active
        ))
        safety = safe_ticks / len(safeties)

        # Efficiency = low pressure + low temp + low spread
        efficiency = 1.0 / (1.0 + np.mean(pressures) + np.mean(temps))

        overall = 0.4 * stability + 0.4 * safety + 0.2 * efficiency

        return TrajectoryScore(
            stability=float(stability),
            safety=float(safety),
            efficiency=float(efficiency),
            overall=float(overall),
        )