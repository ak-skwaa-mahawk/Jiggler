# pwc/planner.py
from .types import *
import numpy as np


class Planner:
    def propose_plan(self, snapshot: SubstrateSnapshot, horizon: int = 200) -> ManifoldPlan:
        gs = snapshot.gs_state

        drift = DriftEnvelope(
            max_drift=abs(gs.spin) * 1.5,
            preferred_drift=1.5,   # your PID default
            horizon=horizon
        )

        pressure = PressureEnvelope(
            max_pressure=min(gs.pressure * 1.5, 2.0),  # your PRESSURE_CAP
            preferred_pressure=1.0,
            horizon=horizon
        )

        temp = TemperatureEnvelope(
            max_temp=gs.temp * 1.5,
            preferred_temp=0.0,
            horizon=horizon
        )

        return ManifoldPlan(
            id=uuid4(),
            drift=drift,
            pressure=pressure,
            temp=temp,
            horizon_steps=horizon,
        )