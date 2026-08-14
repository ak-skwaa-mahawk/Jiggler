#!/usr/bin/env python3
import numpy as np
from scipy.signal import butter, iirnotch, filtfilt

def apply_notch_filter(data: np.ndarray, fs: float = 256.0, notch_freq: float = 60.0, quality_factor: float = 30.0) -> np.ndarray:
    b, a = iirnotch(w0=notch_freq, Q=quality_factor, fs=fs)
    return filtfilt(b, a, data, axis=-1)

def apply_bandpass_filter(data: np.ndarray, lowcut: float = 0.5, highcut: float = 50.0, fs: float = 256.0, order: int = 4) -> np.ndarray:
    nyquist = 0.5 * fs
    low = lowcut / nyquist
    high = highcut / nyquist if (highcut / nyquist) < 1.0 else 0.99
    b, a = butter(order, [low, high], btype='band')
    return filtfilt(b, a, data, axis=-1)

def preprocess_eeg_stream(raw_data: np.ndarray, fs: float = 256.0) -> np.ndarray:
    notched = apply_notch_filter(raw_data, fs=fs, notch_freq=60.0)
    filtered = apply_bandpass_filter(notched, lowcut=0.5, highcut=45.0, fs=fs)
    return filtered

if __name__ == "__main__":
    np.random.seed(42)
    fs = 256.0
    t = np.linspace(0, 2.0, int(fs * 2), endpoint=False)
    
    clean_signal = np.sin(2 * np.pi * 10 * t) * 15.0
    line_noise = np.sin(2 * np.pi * 60 * t) * 30.0
    raw_eeg = np.tile(clean_signal + line_noise, (8, 1)) + np.random.randn(8, int(fs * 2)) * 2.0
    
    cleaned_eeg = preprocess_eeg_stream(raw_eeg, fs=fs)
    
    print("--- DSP Preprocessing Check ---")
    print(f"Raw Signal Max Amplitude (with noise):     {np.max(np.abs(raw_eeg)):.2f} uV")
    print(f"Cleaned Signal Max Amplitude (filtered):   {np.max(np.abs(cleaned_eeg)):.2f} uV")
