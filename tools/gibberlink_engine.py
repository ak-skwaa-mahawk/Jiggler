#!/usr/bin/env python3
import numpy as np
from scipy.io import wavfile

class GibberlinkAcousticEngine:
    """
    Gibberlink MT-FSK Acoustic Engine with Zero-Padded Frame Reconstruction.
    """
    def __init__(self, sample_rate: int = 48000):
        self.sample_rate = sample_rate
        self.beacon_freq = 18000.0
        self.base_freq = 18500.0
        self.bin_spacing = 60.0
        self.symbol_duration = 0.10  # 100 ms per symbol

    def encode_payload_to_audio(self, payload_text: str, output_filename: str = "gibberlink_payload.wav") -> dict:
        payload_bytes = payload_text.encode('utf-8')
        t_sym = np.linspace(0, self.symbol_duration, int(self.sample_rate * self.symbol_duration), endpoint=False)
        
        # 1. Sync Beacon (18 kHz tone for 0.20 sec)
        t_beacon = np.linspace(0, 0.20, int(self.sample_rate * 0.20), endpoint=False)
        beacon_wave = 0.5 * np.sin(2 * np.pi * self.beacon_freq * t_beacon)
        
        audio_frames = [beacon_wave]

        # 2. Encode Bytes (High/Low Nibbles)
        for b in payload_bytes:
            high_nibble = (b >> 4) & 0x0F
            low_nibble = b & 0x0F

            f1 = self.base_freq + (high_nibble * self.bin_spacing)
            f2 = self.base_freq + 1000.0 + (low_nibble * self.bin_spacing)

            frame_wave = 0.25 * (np.sin(2 * np.pi * f1 * t_sym) + np.sin(2 * np.pi * f2 * t_sym))
            envelope = np.hanning(len(t_sym))
            audio_frames.append(frame_wave * envelope)

        full_audio = np.concatenate(audio_frames)
        pcm_data = np.int16(full_audio / np.max(np.abs(full_audio)) * 32767)
        wavfile.write(output_filename, self.sample_rate, pcm_data)

        return {
            "payload_encoded": payload_text,
            "byte_count": len(payload_bytes),
            "duration_sec": len(full_audio) / self.sample_rate,
            "output_file": output_filename
        }

    def decode_audio_to_payload(self, pcm_data: np.ndarray) -> str:
        norm_data = pcm_data.astype(np.float32) / 32767.0
        frame_samples = int(self.sample_rate * self.symbol_duration)

        # Dynamic Sync Search: Locate end of 18 kHz sync beacon
        win_size = int(self.sample_rate * 0.05)
        beacon_end_idx = 0
        for i in range(0, len(norm_data) - win_size, win_size // 2):
            chunk = norm_data[i : i + win_size]
            fft_vals = np.abs(np.fft.rfft(chunk))
            freqs = np.fft.rfftfreq(len(chunk), 1.0 / self.sample_rate)
            beacon_idx = np.argmin(np.abs(freqs - self.beacon_freq))
            if fft_vals[beacon_idx] > 50.0:
                beacon_end_idx = i + win_size

        data_signal = norm_data[beacon_end_idx:]

        # Pad with zeros to ensure the final frame is complete
        remainder = len(data_signal) % frame_samples
        if remainder > 0:
            pad_length = frame_samples - remainder
            data_signal = np.pad(data_signal, (0, pad_length), mode='constant')

        num_frames = len(data_signal) // frame_samples
        decoded_bytes = bytearray()

        for i in range(num_frames):
            frame = data_signal[i * frame_samples : (i + 1) * frame_samples]
            fft_vals = np.abs(np.fft.rfft(frame))
            freqs = np.fft.rfftfreq(len(frame), 1.0 / self.sample_rate)

            # High Nibble Band
            idx_high = np.logical_and(freqs >= self.base_freq - 30, freqs <= self.base_freq + 960)
            sub_f_h, sub_fft_h = freqs[idx_high], fft_vals[idx_high]
            peak_f1 = sub_f_h[np.argmax(sub_fft_h)]
            high_nibble = max(0, min(15, int(round((peak_f1 - self.base_freq) / self.bin_spacing))))

            # Low Nibble Band
            base_low = self.base_freq + 1000.0
            idx_low = np.logical_and(freqs >= base_low - 30, freqs <= base_low + 960)
            sub_f_l, sub_fft_l = freqs[idx_low], fft_vals[idx_low]
            peak_f2 = sub_f_l[np.argmax(sub_fft_l)]
            low_nibble = max(0, min(15, int(round((peak_f2 - base_low) / self.bin_spacing))))

            decoded_bytes.append((high_nibble << 4) | low_nibble)

        return decoded_bytes.decode('utf-8', errors='ignore')

if __name__ == "__main__":
    print("--- Padded Gibberlink Engine Test ---")
    engine = GibberlinkAcousticEngine(sample_rate=48000)
    test_msg = "FPT::Sovereign"
    res = engine.encode_payload_to_audio(test_msg, "gibberlink_test.wav")
    
    sr, pcm = wavfile.read("gibberlink_test.wav")
    decoded = engine.decode_audio_to_payload(pcm)

    print(f"Original: {test_msg}")
    print(f"Decoded:  {decoded}")
    print(f"Match:    {test_msg == decoded}")
