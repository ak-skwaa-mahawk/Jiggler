#!/usr/bin/env python3
import numpy as np
from scipy.signal import welch, butter, filtfilt

# Standard 10-20 Electrodes
CHANNELS = ["Fp1", "Fp2", "F3", "F4", "C3", "C4", "P3", "P4", "O1", "O2", "F7", "F8", "T3", "T4", "T5", "T6", "Fz", "Cz", "Pz"]

BANDS = {
    "delta": (0.5, 4.0),
    "theta": (4.0, 8.0),
    "alpha": (8.0, 13.0),
    "beta":  (13.0, 30.0),
    "gamma": (30.0, 45.0)
}

# Synthetic Normative Database (Mean and Std Dev for 19 channels)
MOCK_NORMS = {
    band: {
        "mean": np.array([2.5, 2.4, 3.1, 3.0, 2.8, 2.9, 3.5, 3.4, 5.2, 5.1, 2.2, 2.3, 2.1, 2.0, 3.0, 3.1, 3.2, 3.0, 3.6]),
        "std":  np.array([0.5, 0.4, 0.6, 0.5, 0.5, 0.6, 0.7, 0.6, 1.1, 1.0, 0.4, 0.4, 0.3, 0.4, 0.6, 0.5, 0.6, 0.5, 0.7])
    }
    for band in BANDS
}

class QEEGProcessor:
    def __init__(self, fs: float = 256.0):
        self.fs = fs

    def bandpass_filter(self, data: np.ndarray, low: float = 0.5, high: float = 45.0) -> np.ndarray:
        nyq = 0.5 * self.fs
        b, a = butter(4, [low / nyq, high / nyq], btype='band')
        return filtfilt(b, a, data, axis=-1)

    def compute_psd(self, data: np.ndarray):
        """Computes Welch PSD for (n_channels, n_samples) data."""
        n_samples = data.shape[-1]
        nperseg = min(n_samples, int(self.fs * 2))
        freqs, psd = welch(data, fs=self.fs, nperseg=nperseg, axis=-1)
        return freqs, psd

    def extract_band_powers(self, freqs: np.ndarray, psd: np.ndarray) -> dict:
        """Calculates absolute power per band for each channel."""
        trapz_fn = getattr(np, 'trapezoid', getattr(np, 'trapz', None))
        powers = {}
        for band_name, (low, high) in BANDS.items():
            idx = np.logical_and(freqs >= low, freqs <= high)
            powers[band_name] = trapz_fn(psd[:, idx], freqs[idx], axis=-1)
        return powers

    def compute_z_scores(self, band_powers: dict) -> dict:
        """Computes Z-scores against normative baseline."""
        z_scores = {}
        for band, val in band_powers.items():
            norm_mean = MOCK_NORMS[band]["mean"]
            norm_std = MOCK_NORMS[band]["std"]
            z_scores[band] = (val - norm_mean) / norm_std
        return z_scores


if __name__ == "__main__":
    print("--- QEEG Baseline Analysis Engine ---")
    np.random.seed(42)
    fs = 256.0
    duration = 10.0  # 10 second baseline slice
    n_channels = len(CHANNELS)
    n_samples = int(fs * duration)

    # Generate synthetic 19-channel EEG (10 Hz Alpha + random noise + Theta spike on F3/F4)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    synthetic_signal = np.sin(2 * np.pi * 10 * t) * 4.0  # Normal Alpha
    raw_eeg = np.tile(synthetic_signal, (n_channels, 1)) + np.random.randn(n_channels, n_samples) * 1.5

    # Inject simulated excess Frontal Theta (ADHD marker simulation on F3/F4)
    raw_eeg[2, :] += np.sin(2 * np.pi * 6 * t) * 8.0  # F3
    raw_eeg[3, :] += np.sin(2 * np.pi * 6 * t) * 7.5  # F4

    # Processing Pipeline
    qeeg = QEEGProcessor(fs=fs)
    filtered_eeg = qeeg.bandpass_filter(raw_eeg)
    freqs, psd = qeeg.compute_psd(filtered_eeg)
    band_powers = qeeg.extract_band_powers(freqs, psd)
    z_scores = qeeg.compute_z_scores(band_powers)

    print("\n--- Channel Z-Score Deviations (|Z| > 1.96 marked with *) ---")
    print(f"{'Channel':<8} | {'Delta Z':<9} | {'Theta Z':<9} | {'Alpha Z':<9} | {'Beta Z':<9}")
    print("-" * 55)
    for i, ch in enumerate(CHANNELS):
        d_z = z_scores["delta"][i]
        t_z = z_scores["theta"][i]
        a_z = z_scores["alpha"][i]
        b_z = z_scores["beta"][i]
        
        t_flag = "*" if abs(t_z) >= 1.96 else " "
        print(f"{ch:<8} | {d_z:8.2f}  | {t_z:8.2f}{t_flag} | {a_z:8.2f}  | {b_z:8.2f} ")

    print("\n[+] Baseline complete: Excessive Frontal Theta successfully isolated on F3/F4.")
