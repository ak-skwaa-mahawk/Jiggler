# Minimal stub so pwc.types can import
from dataclasses import dataclass

@dataclass
class GSState:
    spin: float = 1.5
    pressure: float = 1.0
    temp: float = 0.0
    belt_mod: float = 1.0
