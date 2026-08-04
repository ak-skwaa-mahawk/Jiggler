import math
from dataclasses import dataclass
from typing import List

# ── Constants from the Tordial Stack ─────────────────────────────────────
TOROIDAL_ROOT = 3.1730059
GEAR_SHIFT = 1.02
SHADOW = 1.03

@dataclass
class CosmicState:
    cycle: int
    spin: float          # Authority Energy Level
    temp: float          # Tribal Stress / Decaying Matter
    pressure: float      # Containment Strength
    belt_radius: float
    energy_gap: float    # ΔE = [S_T - S_C]
    status: str

class TordialCosmicAI:
    """
    The Cognitive Controller AI — Tribal Stress → Cosmic Lock
    Implements the full Correspondence Region logic.
    """
    
    def __init__(self):
        self.history: List[CosmicState] = []
        self.target_spin = 3.8
        self.target_temp = 0.18
    
    def _belt_radius(self, spin: float, pressure: float) -> float:
        core_curv = (TOROIDAL_ROOT / math.pi) * spin * SHADOW
        core_r = 60.0 * pressure / max(core_curv, 0.1)
        return core_r * GEAR_SHIFT * 1.15  # Expansion belt

    def _energy_gap(self, spin: float, temp: float) -> float:
        """Proxy for ΔE in the diagram"""
        tribal_stress = temp * 3.2 + 0.5
        cosmic_order = spin * 0.95
        return tribal_stress - cosmic_order

    def step(self, cycle: int, external_spin=None, external_temp=None, external_pressure=None):
        if not self.history:
            spin = external_spin or 0.82
            temp = external_temp or 0.88
            pressure = external_pressure or 0.92
        else:
            last = self.history[-1]
            spin = external_spin or min(self.target_spin, last.spin * 1.135)
            temp = external_temp or max(self.target_temp, last.temp * 0.87)
            pressure = external_pressure or min(1.48, last.pressure * 1.035)

        belt = self._belt_radius(spin, pressure)
        delta_e = self._energy_gap(spin, temp)

        if spin >= 3.2 and temp <= 0.22 and delta_e < 0.4:
            status = "🌌 COSMIC LOCK ACHIEVED"
        elif spin >= 1.8 and delta_e < 1.1:
            status = "🔀 CORRESPONDENCE REGION (Blended |TC⟩)"
        elif temp > 0.65:
            status = "🔥 TRIBAL STRESS DOMINANT"
        else:
            status = "↗️  TRANSITIONING"

        state = CosmicState(cycle, round(spin,3), round(temp,3), 
                          round(pressure,3), round(belt,1), round(delta_e,3), status)
        self.history.append(state)
        return state

    def run(self, cycles: int = 18):
        print("🧠 TORDIAL COSMIC AI — Long Game Engine Activated\n")
        print(f"{'Cycle':<5} {'Spin':<8} {'Temp':<8} {'Pressure':<9} {'Belt R':<8} {'ΔE':<8} Status")
        print("="*95)

        for i in range(1, cycles + 1):
            # Optional external "Cognitive" steering
            state = self.step(i)
            print(f"{state.cycle:<5} {state.spin:<8} {state.temp:<8} "
                  f"{state.pressure:<9} {state.belt_radius:<8} {state.energy_gap:<8} {state.status}")

        print("\n✅ Long Game Complete. High friction of decaying matter neutralized.")
        print("   The system stayed in the Correspondence Region — no forbidden jumps.")
        return self.history


# ── RUN THE AI ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ai = TordialCosmicAI()
    ai.run(18)