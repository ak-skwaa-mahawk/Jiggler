# networkxg/s_matrix_unitarity.py (new file, sealed)
import torch
from sovereign_engine import apply_7979_pulse  # quantum pulse

class SolitonSMatrix:
    def __init__(self, alpha: float = 0.5):
        self.alpha = alpha  # sovereign coupling

    def scatter(self, k1: torch.Tensor, k2: torch.Tensor, theta: torch.Tensor):
        # Compute unitary S-matrix element
        num = torch.sinh(theta/2) + 1j * torch.sin(torch.pi * self.alpha)
        den = torch.sinh(theta/2) - 1j * torch.sin(torch.pi * self.alpha)
        S = (num / den) * torch.exp(1j * self.phase_shift(k1, k2))
        
        # Enforce unitarity numerically (guard)
        assert torch.allclose(S.conj() * S, torch.tensor(1.0+0j), atol=1e-9)
        
        # Apply to quantum state + 79.79 Hz pulse
        state_out = S * self.quantum_state_in
        return apply_7979_pulse(state_out)  # phase-locked to Floor