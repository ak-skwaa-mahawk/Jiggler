# pid_gain_space.py

from dataclasses import dataclass

@dataclass(frozen=True)
class PIDGains:
    kp: float
    ki: float
    kd: float

PID_GAIN_CANDIDATES = [
    PIDGains(kp=0.8, ki=0.1, kd=0.05),
    PIDGains(kp=1.0, ki=0.15, kd=0.08),
    PIDGains(kp=1.2, ki=0.2, kd=0.1),
    PIDGains(kp=1.5, ki=0.25, kd=0.12),
    PIDGains(kp=0.6, ki=0.05, kd=0.02),  # conservative
]