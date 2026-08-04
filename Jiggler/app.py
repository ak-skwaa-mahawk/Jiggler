#!/usr/bin/env python3
import time
from threading import Thread, Lock
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

class DownsampledTelemetryBuffer:
    def __init__(self):
        self.lock = Lock()
        self.latest_data = None

    def push(self, data: dict):
        with self.lock:
            self.latest_data = data

    def pop(self) -> dict:
        with self.lock:
            data = self.latest_data
            self.latest_data = None
            return data

telemetry_buffer = DownsampledTelemetryBuffer()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tordial_manifold_secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

@app.route('/')
def index():
    return render_template('index.html')

def telemetry_emitter_loop():
    print("⚡ [SOCKETIO ENGINE] Starting 60Hz Downsampled Telemetry Emitter Loop...")
    while True:
        data = telemetry_buffer.pop()
        if data is not None:
            socketio.emit('telemetry_update', data)
        time.sleep(1 / 60.0)

emitter_thread = Thread(target=telemetry_emitter_loop, daemon=True)
emitter_thread.start()

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
