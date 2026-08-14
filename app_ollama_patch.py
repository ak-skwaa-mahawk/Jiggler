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
from tools.ollama_dispatcher import query_ollama_with_tools

app = Flask(__name__)
app.config['SECRET_KEY'] = 'manifold_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

@app.route('/')
def index():
    return render_template('index.html')

# --- Ollama Conversational Function-Calling Route ---
@app.route('/api/chat', methods=['POST'])
def handle_ollama_chat():
    data = request.json or {}
    user_prompt = data.get("prompt", "")
    model = data.get("model", "llama3.1")

    if not user_prompt:
        return jsonify({"error": "Prompt is required"}), 400

    response = query_ollama_with_tools(user_prompt=user_prompt, model_name=model)
    return jsonify(response)

@app.route('/stream_audio/<filename>', methods=['GET'])
def stream_audio_file(filename):
    filepath = os.path.join(os.getcwd(), filename)
    if os.path.exists(filepath):
        return send_file(filepath, mimetype="audio/wav")
    return jsonify({"error": "File not found"}), 404

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
