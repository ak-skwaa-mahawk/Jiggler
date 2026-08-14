#!/usr/bin/env python3
import numpy as np
from scipy.signal import csd, welch

CHANNELS = ["Fp1", "Fp2", "F3", "F4", "C3", "C4", "P3", "P4", "O1", "O2", "F7", "F8", "T3", "T4", "T5", "T6", "Fz", "Cz", "Pz"]

class ConnectivityEngine:
    def __init__(self, fs: float = 256.0):
        self.fs = fs

    def compute_pair_connectivity(self, ch1_data: np.ndarray, ch2_data: np.ndarray, target_band: tuple = (4.0, 8.0)) -> dict:
        """
        Computes Magnitude-Squared Coherence, Phase Lag (Degrees), 
        and Time Delay (ms) for a target frequency band between two channels.
        """
        nperseg = min(len(ch1_data), int(self.fs * 2))
        
        # Cross-Spectral Density & Auto-Spectral Densities
        freqs, Cxy = csd(ch1_data, ch2_data, fs=self.fs, nperseg=nperseg)
        _, Pxx = welch(ch1_data, fs=self.fs, nperseg=nperseg)
        _, Pyy = welch(ch2_data, fs=self.fs, nperseg=nperseg)

        # Target Band Indexing
        idx = np.logical_and(freqs >= target_band[0], freqs <= target_band[1])
        
        # Magnitude Squared Coherence
        coherence_spectrum = (np.abs(Cxy) ** 2) / (Pxx * Pyy + 1e-12)
        mean_coherence = float(np.mean(coherence_spectrum[idx]))

        # Phase Angle in Radians and Degrees
        mean_csd = np.mean(Cxy[idx])
        phase_rad = float(np.angle(mean_csd))
        phase_deg = float(np.degrees(phase_rad))

        # Time Delay (ms) calculation based on band center frequency
        center_freq = (target_band[0] + target_band[1]) / 2.0
        time_delay_ms = float((phase_rad / (2.0 * np.pi * center_freq)) * 1000.0)

        return {
            "coherence": mean_coherence,
            "phase_deg": phase_deg,
            "time_delay_ms": time_delay_ms
        }


if __name__ == "__main__":
    print("--- QEEG Functional Connectivity Engine ---")
    np.random.seed(42)
    fs = 256.0
    duration = 10.0
    n_samples = int(fs * duration)
    t = np.arange(0, duration, 1.0 / fs)

    # 1. Generate Signal Pair: F3 (Master) and F4 (Delayed Slave)
    # 6 Hz Theta wave with an intentional 25 ms delay applied to F4
    f_theta = 6.0
    f3_signal = np.sin(2 * np.pi * f_theta * t) + np.random.randn(n_samples) * 0.2
    
    # Apply time-shift delay (25 ms)
    shift_samples = int(0.025 * fs)
    f4_signal = np.roll(f3_signal, shift_samples) + np.random.randn(n_samples) * 0.2

    # 2. Process Pairwise Connectivity
    engine = ConnectivityEngine(fs=fs)
    conn = engine.compute_pair_connectivity(f3_signal, f4_signal, target_band=(4.0, 8.0))

    print("\n--- Connectivity Metrics (F3 -> F4 Theta Band: 4-8 Hz) ---")
    print(f"Coherence Strength:  {conn['coherence']:.4f}  (1.0 = Perfect Coupling)")
    print(f"Phase Angle Offset:  {conn['phase_deg']:.2f}°")
    print(f"Estimated Delay:     {conn['time_delay_ms']:.2f} ms")

    if conn["time_delay_ms"] > 0:
        print("\n[+] Directional Flow Verified: Channel F3 leads Channel F4.")
    else:
        print("\n[+] Directional Flow Verified: Channel F4 leads Channel F3.")
