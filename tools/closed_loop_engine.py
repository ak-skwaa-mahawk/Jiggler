#!/usr/bin/env python3
import os
import numpy as np
from tools.qeeg_baseline import QEEGProcessor, CHANNELS
from tools.hrv_processor import HRVProcessor
from tools.audio_entrainment import generate_isochronic_tone, generate_binaural_beat

class MultimodalClosedLoopEngine:
    """
    Fused Multimodal Neuro-Cardiac Engine:
    Combines 19-channel QEEG Z-scores with Cardiac HRV Observer Epsilon (ε)
    to select entrainment parameters dynamically.
    """
    def __init__(self, fs: float = 256.0):
        self.fs = fs
        self.qeeg = QEEGProcessor(fs=fs)
        self.hrv = HRVProcessor(fs=fs)

    def evaluate_and_adapt(self, raw_eeg: np.ndarray, raw_cardiac: np.ndarray) -> dict:
        # 1. Process Brain QEEG Z-Scores
        filtered_eeg = self.qeeg.bandpass_filter(raw_eeg)
        freqs, psd = self.qeeg.compute_psd(filtered_eeg)
        band_powers = self.qeeg.extract_band_powers(freqs, psd)
        z_scores = self.qeeg.compute_z_scores(band_powers)

        f3_idx, f4_idx = CHANNELS.index("F3"), CHANNELS.index("F4")
        frontal_theta_z = (z_scores["theta"][f3_idx] + z_scores["theta"][f4_idx]) / 2.0
        frontal_beta_z  = (z_scores["beta"][f3_idx] + z_scores["beta"][f4_idx]) / 2.0

        # 2. Process Cardiac HRV Observer Epsilon Metrics
        rr_intervals = self.hrv.extract_rr_intervals(raw_cardiac)
        t_metrics = self.hrv.compute_time_domain(rr_intervals)
        coherence = self.hrv.compute_fpt_coherence(t_metrics["sdnn_ms"], t_metrics["rmssd_ms"])

        obs_epsilon = coherence["observer_epsilon"]
        is_coiled = coherence["is_coiled_state"]

        print(f"[*] Telemetry: Frontal Theta Z={frontal_theta_z:.2f} | Cardiac ε={obs_epsilon*100:.2f}% | Coiled={is_coiled}")

        output_file = os.path.join(os.getcwd(), "adaptive_protocol.wav")
        protocol = {}

        # 3. Decision Matrix (Brain + Heart Fusion)
        if frontal_theta_z > 1.96 and not is_coiled:
            # Brain Inattention + Low Cardiac Coherence -> Strong SMR/Beta Drive (15 Hz)
            target_freq = 15.0
            carrier_freq = 240.0
            mode = "isochronic"
            action = "Dual-Drive Frontal Theta & Cardiac Coherence Recovery (15 Hz Isochronic)"
            generate_isochronic_tone(carrier_freq=carrier_freq, pulse_freq=target_freq, duration_sec=10.0, output_filename=output_file)
        elif frontal_beta_z > 1.96 or obs_epsilon < 0.035:
            # Brain Stress or Reduced Cardiac Epsilon -> Alpha Stabilization (10 Hz Binaural)
            target_freq = 10.0
            carrier_freq = 200.0
            mode = "binaural"
            action = "Autonomic Stress Reduction & Vagal Tuning (10 Hz Alpha Binaural)"
            generate_binaural_beat(carrier_freq=carrier_freq, beat_freq=target_freq, duration_sec=10.0, output_filename=output_file)
        else:
            # High Coherence & Nominal Brain State -> High Focus Gamma Entrainment (40 Hz)
            target_freq = 40.0
            carrier_freq = 200.0
            mode = "isochronic"
            action = "Peak Performance State Maintenance (40 Hz Gamma)"
            generate_isochronic_tone(carrier_freq=carrier_freq, pulse_freq=target_freq, duration_sec=10.0, output_filename=output_file)

        protocol.update({
            "frontal_theta_z": frontal_theta_z,
            "observer_epsilon": obs_epsilon,
            "is_coiled": is_coiled,
            "action": action,
            "mode": mode,
            "target_freq": target_freq,
            "output_file": output_file
        })
        return protocol

if __name__ == "__main__":
    print("--- Running Multimodal Neuro-Cardiac Engine Test ---")
    np.random.seed(42)
    fs = 256.0
    duration = 10.0
    n_samples = int(fs * duration)
    t = np.arange(0, duration, 1.0 / fs)

    # Synthetic 19-Channel EEG with Frontal Theta Spike
    synthetic_eeg = np.tile(np.sin(2 * np.pi * 10 * t) * 4.0, (19, 1)) + np.random.randn(19, n_samples) * 1.5
    f3_idx, f4_idx = CHANNELS.index("F3"), CHANNELS.index("F4")
    synthetic_eeg[f3_idx, :] += np.sin(2 * np.pi * 6 * t) * 8.0
    synthetic_eeg[f4_idx, :] += np.sin(2 * np.pi * 6 * t) * 7.5

    # Synthetic Cardiac Signal
    phase = 2 * np.pi * np.cumsum(1.2 + 0.15 * np.sin(2 * np.pi * 0.25 * t)) / fs
    synthetic_cardiac = np.cos(phase) + np.random.randn(len(t)) * 0.05

    engine = MultimodalClosedLoopEngine(fs=fs)
    res = engine.evaluate_and_adapt(synthetic_eeg, synthetic_cardiac)

    print("\n--- Multimodal Adaptive Protocol Triggered ---")
    print(f"Action Taken: {res['action']}")
    print(f"Target Beat:  {res['target_freq']} Hz ({res['mode']})")
    print(f"Audio File:   {res['output_file']}")
