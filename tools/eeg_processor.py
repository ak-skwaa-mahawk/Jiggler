#!/usr/bin/env python3
import numpy as np
from scipy.signal import welch
from scipy.io import wavfile

BANDS = {
    'delta': (0.5, 4.0),
    'theta': (4.0, 8.0),
    'alpha': (8.0, 13.0),
    'beta':  (13.0, 30.0),
    'gamma': (30.0, 50.0)
}

def extract_band_powers(eeg_data, fs=256.0):
    n_channels, n_samples = eeg_data.shape
    freqs, psd = welch(eeg_data, fs=fs, nperseg=min(n_samples, int(fs * 2)))
    avg_psd = np.mean(psd, axis=0)
    band_powers = {}
    
    # NumPy 2.0+ uses np.trapezoid instead of np.trapz
    trapz_fn = getattr(np, 'trapezoid', getattr(np, 'trapz', None))
    
    for band_name, (low, high) in BANDS.items():
        idx = np.logical_and(freqs >= low, freqs <= high)
        band_powers[band_name] = trapz_fn(avg_psd[idx], freqs[idx])
    return band_powers

def generate_dynamic_entrainment(alpha_beta_ratio, duration_sec=5.0, output_file="dynamic_entrainment.wav", fs_audio=44100):
    target_beat_freq = np.clip(10.0 * (1.0 / (alpha_beta_ratio + 1e-5)), 8.0, 40.0)
    carrier_freq = 200.0
    t = np.linspace(0, duration_sec, int(fs_audio * duration_sec), endpoint=False)
    left_channel = np.sin(2 * np.pi * carrier_freq * t)
    right_channel = np.sin(2 * np.pi * (carrier_freq + target_beat_freq) * t)
    stereo_audio = np.vstack((left_channel, right_channel)).T
    wavfile.write(output_file, fs_audio, np.int16(stereo_audio * 32767 * 0.5))
    print(f"[+] Dynamic Beat Generated: Target={target_beat_freq:.2f}Hz | Saved to {output_file}")

if __name__ == "__main__":
    np.random.seed(42)
    synthetic_eeg = np.random.randn(8, 1024) * 10.0
    powers = extract_band_powers(synthetic_eeg, fs=256.0)
    print("--- Spectral Band Powers ---")
    for band, power in powers.items():
        print(f"  {band.capitalize()}: {power:.4f}")
    a_b_ratio = powers['alpha'] / (powers['beta'] + 1e-5)
    print(f"\nComputed Alpha/Beta Ratio: {a_b_ratio:.4f}")
    generate_dynamic_entrainment(a_b_ratio)
