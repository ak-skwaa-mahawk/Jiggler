#!/usr/bin/env python3
import math
import random

def classical_period_finder(a, N):
    r = 1
    val = a % N
    while val != 1:
        val = (val * a) % N
        r += 1
        if r > N:
            return None
    return r

def run_shors_simulation(N):
    print(f"[*] Target Composite Number N = {N}")
    if N % 2 == 0:
        return 2, N // 2

    for attempts in range(1, 21):
        a = random.randint(2, N - 1)
        gcd_val = math.gcd(a, N)
        if gcd_val > 1:
            print(f"[+] Found direct factor via GCD check on attempt {attempts}: a={a}")
            return gcd_val, N // gcd_val
            
        r = classical_period_finder(a, N)
        if r is None or r % 2 != 0:
            continue
            
        half_pow = pow(a, r // 2, N)
        if half_pow == N - 1:
            continue
            
        factor1 = math.gcd(half_pow - 1, N)
        factor2 = math.gcd(half_pow + 1, N)
        
        if factor1 > 1 and factor1 < N:
            print(f"[+] Period r = {r} identified for base a = {a}")
            print(f"[+] Successfully factored N = {N} into {factor1} x {factor2}")
            return factor1, factor2

    return None

if __name__ == "__main__":
    print("--- Shor's Algorithm Mathematical Simulation ---")
    target_N = 77
    p, q = run_shors_simulation(target_N)
    assert p * q == target_N, "Factorization verification failed."
    print(f"\n[+] Factor Verification: {p} * {q} = {p * q}")
