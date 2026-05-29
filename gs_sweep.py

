# gs_sweep.py
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Tuple, List, Dict

class GSSweep:
    def __init__(self):
        self.PI_3D = 3.20442315
        self.PHI_OP = 1.65036
        self.GEAR_SHIFT = 1.04

    def compute_gs(self, d: int, r: int) -> Dict:
        """Return full Tordial-GS metrics for a (d,r) pair."""
        denom = 4 * self.PHI_OP * self.GEAR_SHIFT
        sigma_T = r - (d ** 2) / denom
        if sigma_T <= 0:
            return {"d": d, "r": r, "sigma_T": 0, "kappa_GS_T": 0,
                    "rho_GS_T": 0, "band": "SUBCRITICAL"}
        
        kappa = sigma_T / d
        rho = math.sqrt(sigma_T) / d
        
        band = self.classify_band(kappa, sigma_T)
        
        return {
            "d": d,
            "r": r,
            "sigma_T": round(sigma_T, 4),
            "kappa_GS_T": round(kappa, 4),
            "rho_GS_T": round(rho, 4),
            "band": band
        }

    def classify_band(self, kappa: float, sigma: float) -> str:
        if kappa < 3.2 or sigma < 40:
            return "SUBCRITICAL"
        elif 3.2 <= kappa < 5.0:
            return "MARGINAL"
        elif 5.0 <= kappa <= 8.5 and sigma > 90:
            return "GOLDILOCKS"
        else:
            return "DEEP_GS"

    def run_sweep(self, 
                  d_range: Tuple[int, int, int] = (22, 68, 4),
                  r_range: Tuple[int, int, int] = (180, 560, 35)) -> pd.DataFrame:
        """Full grid sweep."""
        results = []
        d_vals = range(*d_range)
        r_vals = range(*r_range)

        print(f"[+] Sweeping {len(d_vals)} × {len(r_vals)} = {len(d_vals)*len(r_vals)} configurations...\n")
        
        for d in d_vals:
            for r in r_vals:
                res = self.compute_gs(d, r)
                results.append(res)
                if res["band"] == "GOLDILOCKS":
                    print(f"  ✓ GOLDILOCKS → d={d:2d} r={r:3d}  κ={res['kappa_GS_T']:.3f}  σ={res['sigma_T']:.1f}")

        df = pd.DataFrame(results)
        df.to_csv("gs_sweep_results.csv", index=False)
        print(f"\n[+] Sweep complete. Results saved to gs_sweep_results.csv")
        return df

    def plot_heatmap(self, df: pd.DataFrame):
        pivot = df.pivot(index="d", columns="r", values="kappa_GS_T")
        plt.figure(figsize=(11, 7))
        sns.heatmap(pivot, cmap="viridis", annot=False, linewidths=0.5)
        plt.title("Tordial-GS κ Field — Parameter Sweep")
        plt.xlabel("r (relations)")
        plt.ylabel("d (generators)")
        plt.tight_layout()
        plt.savefig("gs_kappa_heatmap.png", dpi=240)
        plt.show()

        # Band distribution
        plt.figure(figsize=(8, 5))
        df["band"].value_counts().plot(kind='bar', color=['red','orange','lime','purple'])
        plt.title("GS Regime Distribution")
        plt.ylabel("Count")
        plt.savefig("gs_band_distribution.png", dpi=200)
        plt.show()


# ========================== CLI ==========================
if __name__ == "__main__":
    sweep = GSSweep()
    df = sweep.run_sweep(d_range=(22, 68, 4), r_range=(180, 560, 35))
    sweep.plot_heatmap(df)