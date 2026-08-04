#!/usr/bin/env python3
"""
GS Heterogeneity Engine for Tordial–GS Manifold

Purpose:
    - Generate heterogeneous (d, r) configurations for TordialNode populations.
    - Respect Tordial-patched GS inequality:
          sigma_T = r - d^2 / (4 * PHI_OP * GEAR_SHIFT_CORRECTION)
    - Classify nodes into GS regimes (bands).
    - Support mutation and adaptation of (d, r) under macro stress signals.

Intended integration:
    - Used by DualRingTordialMatrix at node construction time.
    - Optionally called during runtime to mutate GS parameters.
"""

from __future__ import annotations
import math
import random
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional, Callable

# Keep these aligned with your core constants
PHI_OP = 1.65036
GEAR_SHIFT_CORRECTION = 1.04
DENOM_GS_TORDIAL = 4 * PHI_OP * GEAR_SHIFT_CORRECTION


# =========================
# DATA STRUCTURES
# =========================

@dataclass
class GSProfile:
    d: int
    r: int
    sigma_T: float
    kappa_GS_T: float
    lambda_GS_T: float
    rho_GS_T: float
    band: str


@dataclass
class GSHeterogeneityConfig:
    d_range: Tuple[int, int]          # (min_d, max_d)
    r_range: Tuple[int, int]          # (min_r, max_r)
    sigma_soft: float = 12.0
    sigma_hard: float = 48.0
    target_band_mix: Dict[str, float] = None  # e.g. {"MARGINAL": 0.4, "DEEP_GS": 0.4, "EXTREME_GS": 0.2}

    def __post_init__(self):
        if self.target_band_mix is None:
            self.target_band_mix = {
                "MARGINAL": 0.4,
                "DEEP_GS": 0.4,
                "EXTREME_GS": 0.2,
            }


# =========================
# CORE GS HELPERS
# =========================

def compute_gs_profile(d: int, r: int,
                       sigma_soft: float,
                       sigma_hard: float) -> Optional[GSProfile]:
    sigma_T = r - (d ** 2) / DENOM_GS_TORDIAL
    if sigma_T <= 0:
        return None

    kappa = sigma_T / d
    lam = math.sqrt(sigma_T)
    rho = lam / d

    if sigma_T <= sigma_soft:
        band = "MARGINAL"
    elif sigma_T <= sigma_hard:
        band = "DEEP_GS"
    else:
        band = "EXTREME_GS"

    return GSProfile(
        d=d,
        r=r,
        sigma_T=sigma_T,
        kappa_GS_T=kappa,
        lambda_GS_T=lam,
        rho_GS_T=rho,
        band=band,
    )


# =========================
# HETEROGENEITY GENERATOR
# =========================

def generate_heterogeneous_profiles(
    node_count: int,
    cfg: GSHeterogeneityConfig,
    rng: Optional[random.Random] = None,
) -> List[GSProfile]:
    """
    Generate a list of GSProfile objects for node_count nodes,
    approximately matching the desired band mix.
    """
    if rng is None:
        rng = random.Random()

    min_d, max_d = cfg.d_range
    min_r, max_r = cfg.r_range

    # Target counts per band
    band_targets: Dict[str, int] = {}
    remaining = node_count
    bands = list(cfg.target_band_mix.keys())

    for i, band in enumerate(bands):
        if i == len(bands) - 1:
            band_targets[band] = remaining
        else:
            count = int(node_count * cfg.target_band_mix[band])
            band_targets[band] = count
            remaining -= count

    profiles: List[GSProfile] = []

    def sample_profile_for_band(target_band: str, max_attempts: int = 500) -> Optional[GSProfile]:
        for _ in range(max_attempts):
            d = rng.randint(min_d, max_d)
            r = rng.randint(min_r, max_r)
            prof = compute_gs_profile(d, r, cfg.sigma_soft, cfg.sigma_hard)
            if prof and prof.band == target_band:
                return prof
        return None

    # Fill per band
    for band, target_count in band_targets.items():
        for _ in range(target_count):
            prof = sample_profile_for_band(band)
            if prof is None:
                # Fallback: accept any valid GS profile
                for _ in range(300):
                    d = rng.randint(min_d, max_d)
                    r = rng.randint(min_r, max_r)
                    prof_any = compute_gs_profile(d, r, cfg.sigma_soft, cfg.sigma_hard)
                    if prof_any:
                        profiles.append(prof_any)
                        break
            else:
                profiles.append(prof)

    # If we somehow undershoot, fill remaining with any valid profiles
    while len(profiles) < node_count:
        d = rng.randint(min_d, max_d)
        r = rng.randint(min_r, max_r)
        prof_any = compute_gs_profile(d, r, cfg.sigma_soft, cfg.sigma_hard)
        if prof_any:
            profiles.append(prof_any)

    # Trim if overshoot
    return profiles[:node_count]


# =========================
# RUNTIME MUTATION RULES
# =========================

def mutate_profile_under_stress(
    profile: GSProfile,
    stress_level: float,
    rng: Optional[random.Random] = None,
) -> GSProfile:
    """
    Mutate (d, r) in response to macro stress.

    stress_level in [0, 1]:
        - 0.0 → no change
        - 1.0 → maximum mutation

    Heuristic:
        - Under stress, increase r slightly more than d to push sigma_T upward,
          but keep changes bounded.
    """
    if rng is None:
        rng = random.Random()

    if stress_level <= 0.0:
        return profile

    # Scale mutation magnitude
    max_delta_d = 4
    max_delta_r = 24

    delta_d = rng.randint(-max_delta_d, max_delta_d)
    delta_r = rng.randint(0, max_delta_r)

    # Weight by stress level
    delta_d = int(delta_d * stress_level)
    delta_r = int(delta_r * stress_level)

    new_d = max(4, profile.d + delta_d)
    new_r = max(20, profile.r + delta_r)

    new_prof = compute_gs_profile(new_d, new_r, sigma_soft=12.0, sigma_hard=48.0)
    if new_prof is None:
        # If mutation drops us out of GS regime, keep original
        return profile
    return new_prof


def relax_profile_under_stability(
    profile: GSProfile,
    stability_level: float,
    rng: Optional[random.Random] = None,
) -> GSProfile:
    """
    Mutate (d, r) under prolonged stability.

    stability_level in [0, 1]:
        - 0.0 → no change
        - 1.0 → maximum relaxation

    Heuristic:
        - Under stability, allow slight reduction in r to lower sigma_T,
          drifting toward MARGINAL / DEEP_GS from EXTREME_GS.
    """
    if rng is None:
        rng = random.Random()

    if stability_level <= 0.0:
        return profile

    max_delta_r = 20
    delta_r = -rng.randint(0, max_delta_r)
    delta_r = int(delta_r * stability_level)

    new_d = profile.d
    new_r = max(20, profile.r + delta_r)

    new_prof = compute_gs_profile(new_d, new_r, sigma_soft=12.0, sigma_hard=48.0)
    if new_prof is None:
        return profile
    return new_prof


# =========================
# INTEGRATION HELPERS
# =========================

def attach_profiles_to_nodes(
    nodes: List[object],
    profiles: List[GSProfile],
    set_dr: Callable[[object, int, int], None] | None = None,
) -> None:
    """
    Attach GS profiles to an existing list of TordialNode-like objects.

    If set_dr is None, assumes nodes have attributes .d and .r.
    Otherwise, set_dr(node, d, r) is called.
    """
    n = min(len(nodes), len(profiles))
    for i in range(n):
        p = profiles[i]
        node = nodes[i]
        if set_dr is None:
            node.d = p.d
            node.r = p.r
        else:
            set_dr(node, p.d, p.r)


# =========================
# DEMO / CLI
# =========================

def demo():
    cfg = GSHeterogeneityConfig(
        d_range=(24, 72),
        r_range=(160, 520),
        sigma_soft=12.0,
        sigma_hard=48.0,
        target_band_mix={
            "MARGINAL": 0.35,
            "DEEP_GS": 0.45,
            "EXTREME_GS": 0.20,
        },
    )

    profiles = generate_heterogeneous_profiles(10, cfg)
    print("[+] Generated GS profiles:")
    for i, p in enumerate(profiles):
        print(f"Node {i:2d} | d={p.d:3d} r={p.r:4d} | "
              f"sigma_T={p.sigma_T:7.2f} κ={p.kappa_GS_T:6.2f} ρ={p.rho_GS_T:5.3f} | {p.band}")


if __name__ == "__main__":
    demo()