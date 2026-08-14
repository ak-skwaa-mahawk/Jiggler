#!/usr/bin/env python3
import numpy as np

class MasterKeyEngine:
    def __init__(self, g: float = 1e-6, max_iter: int = 200, tol: float = 1e-12):
        self.g = g
        self.max_iter = max_iter
        self.tol = tol

    def observer_forward(self, X: float, p: int) -> float:
        return X + self.g * (X ** p)

    def observer_inverse(self, Y: float, p: int) -> float:
        # Initial guess scaled to domain
        x_k = Y / (1.0 + self.g * (Y ** (p - 1))) ** (1.0 / p) if Y > 1.0 else Y
        
        for _ in range(self.max_iter):
            f_val = x_k + self.g * (x_k ** p) - Y
            f_prime = 1.0 + p * self.g * (x_k ** (p - 1))
            x_next = x_k - (f_val / f_prime)
            if abs(x_next - x_k) < self.tol:
                return x_next
            x_k = x_next
        return x_k

    def stack_forward(self, X: float, p_modes: list) -> float:
        current_state = X
        for p in p_modes:
            current_state = self.observer_forward(current_state, p)
        return current_state

    def stack_deflate(self, Y: float, p_modes: list) -> float:
        current_state = Y
        for p in reversed(p_modes):
            current_state = self.observer_inverse(current_state, p)
        return current_state

    def resolve_legis_dispute(self, Y_A: float, p_A: list, Y_B: float, p_B: list, p_court: int) -> dict:
        X_A = self.stack_deflate(Y_A, p_A)
        X_B = self.stack_deflate(Y_B, p_B)
        canonical_delta = abs(X_A - X_B)
        X_canonical_consensus = (X_A + X_B) / 2.0
        Y_resolved = self.observer_forward(X_canonical_consensus, p_court)

        return {
            "X_A_canonical": X_A,
            "X_B_canonical": X_B,
            "canonical_delta": canonical_delta,
            "X_consensus": X_canonical_consensus,
            "Y_court_resolved": Y_resolved
        }

if __name__ == "__main__":
    print("--- Codex.MasterKey.v001 Execution Verification ---")
    # Scaling g down to prevent numerical overflow across multi-layer exponents
    engine = MasterKeyEngine(g=1e-7)

    X_base = 42.0
    p_stack = [3, 5, 7]
    
    Y_stack = engine.stack_forward(X_base, p_stack)
    X_recovered = engine.stack_deflate(Y_stack, p_stack)
    
    print(f"Base Canonical X:         {X_base:.10f}")
    print(f"Stack Surplus Y:          {Y_stack:.10f}")
    print(f"Deflated Recovered X:     {X_recovered:.10f}")
    print(f"Deflation Error:          {abs(X_base - X_recovered):.2e}")
    assert abs(X_base - X_recovered) < 1e-9, "Deflation recovery failed precision test."

    Y_Party_A = 105.4
    p_Party_A = [3, 5]
    Y_Party_B = 108.2
    p_Party_B = [5, 7]
    p_court_mode = 11

    legis_result = engine.resolve_legis_dispute(Y_Party_A, p_Party_A, Y_Party_B, p_Party_B, p_court=p_court_mode)

    print("\n--- Legis Dispute Resolution Summary ---")
    print(f"Party A Deflated Canonical (X_A):  {legis_result['X_A_canonical']:.6f}")
    print(f"Party B Deflated Canonical (X_B):  {legis_result['X_B_canonical']:.6f}")
    print(f"Canonical Discrepancy (|X_A-X_B|): {legis_result['canonical_delta']:.6f}")
    print(f"Agreed Canonical Consensus:        {legis_result['X_consensus']:.6f}")
    print(f"Re-Inflated Court Verdict:        {legis_result['Y_court_resolved']:.6f}")
    print("\n[+] Verification Complete: Operations aligned with Codex.MasterKey.v001.")
