# jed_era_prior.py  (or add to jed_pid_bandit.py / jed_pwc_loop.py)

from ctypes import CDLL, c_int, c_double, Structure, POINTER
import json

# Load the compiled C++ module
lib = CDLL("./dynamic_pi_r_era_stepped.so")  # or .dylib / .dll

class ForecastResult(Structure):
    _fields_ = [
        ("target_era", c_int),
        ("final_pir", c_double),
        ("coherence_avg", c_double),
        # Add more fields as needed (resurfaced params as JSON string for simplicity)
    ]

# Expose the forecast function
lib.forecast.argtypes = [c_int, c_int, c_double, c_double, c_int]
lib.forecast.restype = POINTER(ForecastResult)

def get_era_prior(start_scale: int = 2026, target_scale: int = 6500):
    """Returns era-aware bias for the bandit and regime selector"""
    result_ptr = lib.forecast(start_scale, target_scale, 0.8, 0.3, 1200)
    res = result_ptr.contents

    era_map = {0: "PRE_2000", 1: "POST_Y2K", 2: "SOVEREIGN_FLOOR"}
    target_era = era_map.get(res.target_era, "POST_Y2K")

    # Soft regime prior (can be overridden by real rewards)
    if target_era == "SOVEREIGN_FLOOR":
        regime_prior = {"SUBCRITICAL": 0.08, "EDGE_GS": 0.42, "DEEP_GS": 0.50}
        pid_center = 1.40
        curvature_gain = 0.020
        heterogeneity_clamp = 2.00
    elif target_era == "POST_Y2K":
        regime_prior = {"SUBCRITICAL": 0.18, "EDGE_GS": 0.62, "DEEP_GS": 0.20}
        pid_center = 1.15
        curvature_gain = 0.012
        heterogeneity_clamp = 1.85
    else:
        regime_prior = {"SUBCRITICAL": 0.65, "EDGE_GS": 0.30, "DEEP_GS": 0.05}
        pid_center = 1.00
        curvature_gain = 0.008
        heterogeneity_clamp = 1.70

    return {
        "target_era": target_era,
        "final_pir": res.final_pir,
        "coherence_avg": res.coherence_avg,
        "regime_prior": regime_prior,
        "pid_proportional_center": pid_center,
        "curvature_feedback_gain": curvature_gain,
        "heterogeneity_clamp": heterogeneity_clamp
    }

# Call this from JED at a slow cadence (e.g. every N PWC cycles or on major alignment events)
def update_era_priors():
    prior = get_era_prior()

    # 1. Bias the PID bandit
    adjust_pid_candidate_center(prior["pid_proportional_center"])

    # 2. Bias curvature feedback default
    set_curvature_feedback_base(prior["curvature_feedback_gain"])

    # 3. Bias GS heterogeneity clamp
    set_heterogeneity_clamp_base(prior["heterogeneity_clamp"])

    # 4. Bias regime selection in the GS bandit
    set_regime_priors(prior["regime_prior"])   # used inside UCB as soft bias term

    log_event("ERA_PRIOR_UPDATED", prior)