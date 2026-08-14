import numpy as np
from scipy.io import wavfile

SAMPLE_RATE = 44100

def generate_binaural_beat(carrier_freq=200.0, beat_freq=40.0, duration_sec=10.0, output_filename="binaural_gamma.wav"):
    t = np.linspace(0, duration_sec, int(SAMPLE_RATE * duration_sec), endpoint=False)
    left_channel = np.sin(2 * np.pi * carrier_freq * t)
    right_channel = np.sin(2 * np.pi * (carrier_freq + beat_freq) * t)
    stereo_audio = np.vstack((left_channel, right_channel)).T
    wavfile.write(output_filename, SAMPLE_RATE, np.int16(stereo_audio * 32767 * 0.5))
    print(f"[+] Binaural Beat ({beat_freq}Hz) saved to {output_filename}")

def generate_isochronic_tone(carrier_freq=200.0, pulse_freq=40.0, duration_sec=10.0, output_filename="isochronic_gamma.wav"):
    t = np.linspace(0, duration_sec, int(SAMPLE_RATE * duration_sec), endpoint=False)
    carrier = np.sin(2 * np.pi * carrier_freq * t)
    pulse_mask = (np.sin(2 * np.pi * pulse_freq * t) > 0).astype(np.float32)
    wavfile.write(output_filename, SAMPLE_RATE, np.int16(carrier * pulse_mask * 32767 * 0.5))
    print(f"[+] Isochronic Tone ({pulse_freq}Hz) saved to {output_filename}")

if __name__ == "__main__":
    generate_binaural_beat()
    generate_isochronic_tone()
