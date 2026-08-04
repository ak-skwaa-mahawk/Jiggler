#!/usr/bin/env python3
"""
GS Field Sweep Engine for Tordial–GS Manifold

Sweeps (d, r) space under the Tordial-patched Golod–Shafarevich inequality:

    sigma_T = r - d^2 / (4 * PHI_OP * GEAR_SHIFT_CORRECTION)

and classifies each pair into stability bands:

    - SUBCRITICAL   : sigma_T <= 0
    - MARGINAL      : 0 < sigma_T <= sigma_soft
    - DEEP_GS       : sigma_soft < sigma_T <= sigma_hard
    - EXTREME_GS    : sigma_T > sigma_hard

Outputs a CSV suitable for heatmaps / offline analysis.
"""

import csv
import math
from dataclasses import dataclass
from typing import List, Dict, Tuple


# =========================
# TORDIAL–GS BASE CONSTANTS
# =========================

PI_3D = 3.20442315
TAU_3D = 2 * PI_3D
PHI_OP = 1.65036
GEAR_SHIFT_CORRECTION = 1.04

DENOM_GS_TORDIAL = 4 * PHI_OP * GEAR_SHIFT_CORRECTION


@dataclass
class GSSweepPoint:
    d: int
    r: int
    sigma_T: float
    kappa_GS_T: float
    lambda_GS_T: float
    rho_GS_T: float
    band: str


# =========================
# CORE GS COMPUTATION
# =========================

def compute_gs_tordial_constants(d: int, r: int) -> Dict[str, float] | None:
    """
    Compute Tordial-patched GS constants for a given (d, r).

    Returns None if sigma_T <= 0 (not in GS-infinite regime).
    """
    sigma_T = r - (d ** 2) / DENOM_GS_TORDIAL
    if sigma_T <= 0:
        return None

    kappa = sigma_T / d
    lam = math.sqrt(sigma_T)
    rho = lam / d

    return {
        "sigma_T": sigma_T,
        "kappa_GS_T": kappa,
        "lambda_GS_T": lam,
        "rho_GS_T": rho,
    }


def classify_sigma_band(
    sigma_T: float,
    sigma_soft: float,
    sigma_hard: float
) -> str:
    """
    Classify sigma_T into qualitative bands.
    """
    if sigma_T <= 0:
        return "SUBCRITICAL"
    if sigma_T <= sigma_soft:
        return "MARGINAL"
    if sigma_T <= sigma_hard:
        return "DEEP_GS"
    return "EXTREME_GS"


# =========================
# SWEEP ENGINE
# =========================

def sweep_gs_field(
    d_range: Tuple[int, int, int],
    r_range: Tuple[int, int, int],
    sigma_soft: float = 10.0,
    sigma_hard: float = 40.0,
) -> List[GSSweepPoint]:
    """
    Sweep over (d, r) grid and compute GS constants + band classification.

    d_range: (d_min, d_max, d_step)
    r_range: (r_min, r_max, r_step)

    sigma_soft, sigma_hard: thresholds for banding sigma_T.
    """
    d_min, d_max, d_step = d_range
    r_min, r_max, r_step = r_range

    results: List[GSSweepPoint] = []

    for d in range(d_min, d_max + 1, d_step):
        for r in range(r_min, r_max + 1, r_step):
            consts = compute_gs_tordial_constants(d, r)
            if consts is None:
                # Still record subcritical region with zeros
                results.append(
                    GSSweepPoint(
                        d=d,
                        r=r,
                        sigma_T=0.0,
                        kappa_GS_T=0.0,
                        lambda_GS_T=0.0,
                        rho_GS_T=0.0,
                        band="SUBCRITICAL",
                    )
                )
                continue

            sigma_T = consts["sigma_T"]
            kappa = consts["kappa_GS_T"]
            lam = consts["lambda_GS_T"]
            rho = consts["rho_GS_T"]
            band = classify_sigma_band(sigma_T, sigma_soft, sigma_hard)

            results.append(
                GSSweepPoint(
                    d=d,
                    r=r,
                    sigma_T=sigma_T,
                    kappa_GS_T=kappa,
                    lambda_GS_T=lam,
                    rho_GS_T=rho,
                    band=band,
                )
            )

    return results


def export_gs_sweep_csv(
    points: List[GSSweepPoint],
    filename: str = "gs_field_sweep.csv"
) -> None:
    """
    Export sweep results to CSV for heatmaps / analysis.
    """
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "d_generators",
            "r_relations",
            "sigma_T",
            "kappa_GS_T",
            "lambda_GS_T",
            "rho_GS_T",
            "band",
        ])
        for p in points:
            writer.writerow([
                p.d,
                p.r,
                f"{p.sigma_T:.6f}",
                f"{p.kappa_GS_T:.6f}",
                f"{p.lambda_GS_T:.6f}",
                f"{p.rho_GS_T:.6f}",
                p.band,
            ])


# =========================
# CLI ENTRYPOINT
# =========================

def main():
    # Default sweep region tuned around your current manifold baseline (d≈42, r≈380)
    d_range = (24, 72, 2)    # d from 24 to 72, step 2
    r_range = (120, 520, 10) # r from 120 to 520, step 10

    # Band thresholds — you can tune these after first plots
    sigma_soft = 12.0
    sigma_hard = 48.0

    print("[+] Running GS field sweep...")
    print(f"    d in [{d_range[0]}, {d_range[1]}] step {d_range[2]}")
    print(f"    r in [{r_range[0]}, {r_range[1]}] step {r_range[2]}")
    print(f"    sigma_soft={sigma_soft}, sigma_hard={sigma_hard}")

    points = sweep_gs_field(d_range, r_range, sigma_soft, sigma_hard)
    export_gs_sweep_csv(points, "gs_field_sweep.csv")

    print(f"[+] Sweep complete. {len(points)} points written to gs_field_sweep.csv")


if __name__ == "__main__":
    main()