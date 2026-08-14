import time
import socket
import numpy as np
from scipy.signal import butter, sosfilt

class E8SovereigntyAnalyzer:
    def __init__(self, g=1e-6, phi=1.6180339887):
        self.g = g
        self.phi = phi
        self.roots = 240
        self.root_sum = self.roots ** 3
        self.target_gamma = 42.8
        self.threshold_entropy = np.log2(self.roots)

    def calculate_spectral_density(self, n_cycles=20):
        lambdas = [0.0, 1.0]
        for n in range(2, n_cycles + 1):
            next_l = (self.phi * lambdas[-1]) - lambdas[-2] + (self.g * self.root_sum / n)
            lambdas.append(next_l)
        return lambdas

    def compute_entropy(self, spectral_density):
        base_entropy = np.log2(len(spectral_density))
        grain_kick = self.g * self.root_sum * np.mean(spectral_density)
        return base_entropy + grain_kick

    def audit_frame(self, gamma_data, sample_rate):
        n_samples = gamma_data.shape[-1]
        fft_vals = np.abs(np.fft.rfft(gamma_data, axis=-1))
        freqs = np.fft.rfftfreq(n_samples, 1.0 / sample_rate)

        gamma_mask = (freqs >= 40.0) & (freqs <= 45.0)
        if not np.any(gamma_mask):
            observed_hz = 0.0
        else:
            gamma_freqs = freqs[gamma_mask]
            gamma_powers = np.mean(fft_vals[:, gamma_mask], axis=0) if gamma_data.ndim > 1 else fft_vals[gamma_mask]
            observed_hz = gamma_freqs[np.argmax(gamma_powers)]

        diff = abs(observed_hz - self.target_gamma)
        is_gamma_aligned = diff < 1.0

        density = self.calculate_spectral_density(n_cycles=20)
        entropy = self.compute_entropy(density)

        sovereign_collapse = is_gamma_aligned and (entropy > self.threshold_entropy)

        return {
            "sovereign": sovereign_collapse,
            "peak_gamma_hz": round(float(observed_hz), 2),
            "gamma_diff_hz": round(float(diff), 2),
            "e8_entropy": round(float(entropy), 4),
            "glyph": "ᕯᕲᐧᐁᐧOR" if sovereign_collapse else "NO_COLLAPSE"
        }

def bandpass_gamma(data, sample_rate, low=40.0, high=45.0):
    sos = butter(4, [low, high], btype='bandpass', fs=sample_rate, output='sos')
    return sosfilt(sos, data, axis=-1)

def run_stream():
    sample_rate = 250
    n_channels = 8
    window_seconds = 2
    n_samples = sample_rate * window_seconds
    
    analyzer = E8SovereigntyAnalyzer()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    print("[+] Native ARM64 E8 Bridge active. Streaming telemetry to UDP 9999...")
    try:
        step = 0
        while True:
            time.sleep(1)
            step += 1
            t = np.linspace(0, window_seconds, n_samples)
            
            # Generate multi-channel baseline EEG noise
            eeg_data = np.random.normal(0, 1.5, (n_channels, n_samples))
            
            # Pulse target gamma wave (42.8 Hz) into the stream
            pulse_frequency = 42.8 if (step % 2 == 0) else 35.0
            eeg_data[0] += 4.0 * np.sin(2 * np.pi * pulse_frequency * t)
            eeg_data[1] += 4.0 * np.sin(2 * np.pi * pulse_frequency * t)

            filtered_gamma = bandpass_gamma(eeg_data, sample_rate)
            audit = analyzer.audit_frame(filtered_gamma, sample_rate)
            
            telemetry_str = f"Gamma: {audit['peak_gamma_hz']}Hz | E8 Entropy: {audit['e8_entropy']} | Glyph: {audit['glyph']}"
            sock.sendto(telemetry_str.encode('utf-8'), ('127.0.0.1', 9999))
            print(f"[STREAM]: {telemetry_str}")
            
    except KeyboardInterrupt:
        print("\nStopping stream...")

if __name__ == "__main__":
    run_stream()
