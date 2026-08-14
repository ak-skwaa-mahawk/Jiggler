#!/usr/bin/env python3
import numpy as np
from scipy.signal import find_peaks, welch
from scipy.interpolate import interp1d

class HRVProcessor:
    def __init__(self, fs: float = 256.0):
        self.fs = fs

    def extract_rr_intervals(self, signal: np.ndarray) -> np.ndarray:
        # Distance filter for 220 BPM max (256 Hz * (60/220) = ~70 samples min distance)
        min_distance = int(self.fs * (60.0 / 220.0))
        # Standardize signal to zero mean, unit variance before peak detection
        norm_sig = (signal - np.mean(signal)) / (np.std(signal) + 1e-8)
        peaks, _ = find_peaks(norm_sig, height=1.0, distance=min_distance)
        
        rr_intervals = np.diff(peaks) / self.fs * 1000.0
        return rr_intervals

    def compute_time_domain(self, rr: np.ndarray) -> dict:
        if len(rr) < 2:
            return {"sdnn_ms": 0.0, "rmssd_ms": 0.0, "mean_hr_bpm": 0.0}
            
        sdnn = float(np.std(rr, ddof=1))
        successive_diffs = np.diff(rr)
        rmssd = float(np.sqrt(np.mean(successive_diffs ** 2)))
        mean_hr = float(60000.0 / np.mean(rr))

        return {
            "sdnn_ms": sdnn,
            "rmssd_ms": rmssd,
            "mean_hr_bpm": mean_hr
        }

    def compute_frequency_domain(self, rr: np.ndarray) -> dict:
        if len(rr) < 4:
            return {"lf_power": 0.0, "hf_power": 0.0, "lf_hf_ratio": 0.0}

        time_rr = np.cumsum(rr) / 1000.0
        time_rr -= time_rr[0]

        fs_resample = 4.0
        interp_fn = interp1d(time_rr, rr, kind='cubic', fill_value='extrapolate')
        time_uniform = np.arange(0, time_rr[-1], 1.0 / fs_resample)
        rr_uniform = interp_fn(time_uniform)

        freqs, psd = welch(rr_uniform, fs=fs_resample, nperseg=min(len(rr_uniform), 256))
        trapz_fn = getattr(np, 'trapezoid', getattr(np, 'trapz', None))
        
        lf_idx = np.logical_and(freqs >= 0.04, freqs < 0.15)
        hf_idx = np.logical_and(freqs >= 0.15, freqs <= 0.40)

        lf_power = float(trapz_fn(psd[lf_idx], freqs[lf_idx])) if np.any(lf_idx) else 0.0
        hf_power = float(trapz_fn(psd[hf_idx], freqs[hf_idx])) if np.any(hf_idx) else 0.0
        lf_hf_ratio = lf_power / (hf_power + 1e-8)

        return {
            "lf_power": lf_power,
            "hf_power": hf_power,
            "lf_hf_ratio": lf_hf_ratio
        }

    def compute_fpt_coherence(self, sdnn: float, rmssd: float) -> dict:
        vagal_ratio = rmssd / (sdnn + 1e-5)
        epsilon_surplus = float(np.clip(vagal_ratio * 0.0417, 0.0, 0.10))
        zeta_damping = float(np.clip(vagal_ratio, 0.1, 1.0))

        return {
            "observer_epsilon": epsilon_surplus,
            "zeta_damping": zeta_damping,
            "is_coiled_state": bool(rmssd >= 50.0 and vagal_ratio >= 0.8)
        }

if __name__ == "__main__":
    print("--- Corrected HRV Signal Engine Test ---")
    np.random.seed(42)
    fs = 256.0
    duration = 60.0
    t = np.arange(0, duration, 1.0 / fs)

    # Clean 72 BPM cardiac generator with RSA modulation (0.25 Hz)
    base_hr_hz = 1.2
    rsa_mod = 0.15 * np.sin(2 * np.pi * 0.25 * t)
    instant_freq = base_hr_hz + rsa_mod
    phase = 2 * np.pi * np.cumsum(instant_freq) / fs
    synthetic_cardiac = np.cos(phase) + np.random.randn(len(t)) * 0.05

    processor = HRVProcessor(fs=fs)
    rr_intervals = processor.extract_rr_intervals(synthetic_cardiac)
    time_metrics = processor.compute_time_domain(rr_intervals)
    freq_metrics = processor.compute_frequency_domain(rr_intervals)
    fpt_metrics = processor.compute_fpt_coherence(time_metrics["sdnn_ms"], time_metrics["rmssd_ms"])

    print(f"Mean Heart Rate:    {time_metrics['mean_hr_bpm']:.2f} BPM")
    print(f"SDNN:               {time_metrics['sdnn_ms']:.2f} ms")
    print(f"RMSSD:              {time_metrics['rmssd_ms']:.2f} ms")
    print(f"Observer Epsilon:   {fpt_metrics['observer_epsilon'] * 100:.2f}%")
    print(f"Coiled State:       {fpt_metrics['is_coiled_state']}")
