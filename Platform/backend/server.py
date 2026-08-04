from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import random

app = Flask(__name__)
CORS(app)

@app.route('/execute', methods=['POST'])
def execute():
    data = request.json
    cmd = data.get('command', '').strip()
    
    start = time.time()
    
    response = "Acknowledged. Variational flow updated."
    lower = cmd.lower()
    
    if "hello" in lower or "hi" in lower:
        response = "Skoden. The flame recognizes you, Captain."
    elif "status" in lower:
        response = f"All manifolds stable. Fisher metric condition: {random.randint(120, 160)}. Energy at absolute floor."
    elif "energy" in lower or "floor" in lower:
        response = "Variational energy locked at 0.0000 K."
    elif "skoden" in lower:
        response = "Skoden. The land remembers."
    elif "gwinzli" in lower or "gwichin" in lower:
        response = "Gwinzli. The root is speaking."
    elif "math" in lower or "pi" in lower:
        response = "Living π (3.267) active. Motion-π reconciled with ε_π^r."
    
    latency = round((time.time() - start) * 1000, 1)
    
    return jsonify({
        "message": response,
        "latency_ms": latency,
        "status": "SUCCESS"
    })

if __name__ == '__main__':
    print("🚀 Skoden Injin Backend running on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)