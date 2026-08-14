import eventlet
eventlet.monkey_patch()

import os
import json
import socket
import time
import numpy as np
from flask import Flask, render_template, jsonify, request, send_file
from flask_socketio import SocketIO, emit

from tools.eeg_filter import preprocess_eeg_stream
from tools.eeg_processor import extract_band_powers
from tools.audio_entrainment import generate_binaural_beat, generate_isochronic_tone
from tools.closed_loop_engine import MultimodalClosedLoopEngine

app = Flask(__name__)
app.config['SECRET_KEY'] = 'manifold_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/trigger_adaptive_loop', methods=['POST'])
def trigger_adaptive_loop():
    np.random.seed(int(time.time()))
    fs = 256.0
    duration = 10.0
    n_samples = int(fs * duration)
    t = np.arange(0, duration, 1.0 / fs)

    # 19-Channel Synthetic EEG
    synthetic_eeg = np.tile(np.sin(2 * np.pi * 10 * t) * 4.0, (19, 1)) + np.random.randn(19, n_samples) * 1.5
    synthetic_eeg[2, :] += np.sin(2 * np.pi * 6 * t) * np.random.uniform(5.0, 9.0) # F3
    synthetic_eeg[3, :] += np.sin(2 * np.pi * 6 * t) * np.random.uniform(5.0, 9.0) # F4

    # Synthetic Cardiac Trace with RSA
    phase = 2 * np.pi * np.cumsum(1.2 + 0.15 * np.sin(2 * np.pi * 0.25 * t)) / fs
    synthetic_cardiac = np.cos(phase) + np.random.randn(len(t)) * 0.05

    engine = MultimodalClosedLoopEngine(fs=fs)
    protocol = engine.evaluate_and_adapt(synthetic_eeg, synthetic_cardiac)

    return jsonify({
        "status": "success",
        "action": protocol["action"],
        "target_freq": protocol["target_freq"],
        "mode": protocol["mode"],
        "observer_epsilon": f"{protocol['observer_epsilon']*100:.2f}%",
        "is_coiled": protocol["is_coiled"],
        "url": "/stream_audio/adaptive_protocol.wav"
    })

@app.route('/stream_audio/<filename>', methods=['GET'])
def stream_audio_file(filename):
    filepath = os.path.join(os.getcwd(), filename)
    if os.path.exists(filepath):
        return send_file(filepath, mimetype="audio/wav")
    return jsonify({"error": "File not found"}), 404

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
