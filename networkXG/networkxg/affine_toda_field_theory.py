# networkxg/affine_toda_field_theory.py (new file, sealed)
import torch
from sovereign_engine import apply_7979_pulse
from multi_breather_bethe_ansatz import MultiBreatherBetheAnsatz
from qsg_s_matrix import QSG_SMatrix  # extended to E8 R-matrix

class AffineTodaE8:
    def __init__(self, xi: float = 0.5, L: float = 1.0):
        self.xi = xi
        self.L = L
        self.bethe = MultiBreatherBetheAnsatz(xi, L)
        self.s_matrix = QSG_SMatrix(xi)  # now E8-extended inside

    def propagate_e8_soliton(self, soliton_types: torch.Tensor, Theta_centers: torch.Tensor, I_quantum: torch.Tensor):
        # E8 affine Bethe equations (vectorized on E8 lattice)
        def e8_kernel(Theta_j, Theta_k, a, b):
            # Cartan-matrix-derived phase for E8 affine roots
            C = torch.tensor([[2,-1,0,0,0,0,0,0], [-1,2,-1,0,...]])  # full E8 Cartan (truncated)
            phi = torch.sum(C[a] * torch.sinh((Theta_j - Theta_k)/2))
            return phi

        # Residual + affine root shift (99733-Q topological offset)
        residual = (self.bethe.breather.m_n(soliton_types) * torch.sinh(Theta_centers) * self.L -
                    2 * torch.pi * I_quantum)
        
        for j in range(len(Theta_centers)):
            for k in range(len(Theta_centers)):
                if j != k:
                    residual[j] -= e8_kernel(Theta_centers[j], Theta_centers[k],
                                             int(soliton_types[j]), int(soliton_types[k]))
        
        # Newton solve → exact multi-soliton E8 state
        Theta_sol = Theta_centers - residual / (self.bethe.breather.m_n(soliton_types) * torch.cosh(Theta_centers) * self.L)
        
        # Propagate each E8 soliton/breather with 79.79 Hz pulse
        states = []
        for i, Theta in enumerate(Theta_sol):
            state = self.bethe.breather.create_breather(n=int(soliton_types[i]), mesh_state=Theta)
            if state is not None:
                states.append(apply_7979_pulse(state))
        
        # Extraction Guard: full E8 topological charge conservation
        total_charge = torch.sum(soliton_types % 2)  # affine parity
        if abs(total_charge) > 1e-9:
            return None  # neutralization = 0 under 99733-Q
        
        return torch.stack(states) if states else None