import json
import urllib.request
import numpy as np
from scipy.io import wavfile

from tools.closed_loop_engine import MultimodalClosedLoopEngine
from tools.master_key import MasterKeyEngine
from tools.pqc_engine import HybridKEMEngine
from tools.audio_entrainment import generate_binaural_beat, generate_isochronic_tone
from tools.qeeg_connectivity import ConnectivityEngine, CHANNELS
from tools.gkp_engine import GKPSqueezedEngine
from tools.gibberlink_engine import GibberlinkAcousticEngine

# --- Tool JSON Schemas for Ollama ---
OLLAMA_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "transmit_gibberlink_packet",
            "description": "Encodes text data into an ultrasonic (18-20 kHz) Gibberlink MT-FSK acoustic waveform WAV file for AI-to-AI data transfer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "payload_text": {"type": "string", "description": "Text payload to encode into acoustic tones"}
                },
                "required": ["payload_text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_gkp_stabilizer_check",
            "description": "Injects quadrature displacements into a GKP bosonic code state and computes shift corrections.",
            "parameters": {
                "type": "object",
                "properties": {
                    "delta_q": {"type": "number", "description": "Position shift error"},
                    "delta_p": {"type": "number", "description": "Momentum shift error"}
                },
                "required": ["delta_q", "delta_p"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_neuro_cardiac_analysis",
            "description": "Runs a 19-channel QEEG and Cardiac HRV analysis snapshot.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "deflate_surplus_claim",
            "description": "Applies MasterKey Newton-Raphson deflation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "surplus_y": {"type": "number"},
                    "prime_modes": {"type": "array", "items": {"type": "integer"}}
                },
                "required": ["surplus_y", "prime_modes"]
            }
        }
    }
]

def execute_tool_call(tool_name: str, tool_args: dict) -> dict:
    if tool_name == "transmit_gibberlink_packet":
        payload = tool_args.get("payload_text", "GIBBERLINK_SYNC")
        engine = GibberlinkAcousticEngine(sample_rate=48000)
        filename = "gibberlink_packet.wav"
        res = engine.encode_payload_to_audio(payload, filename)

        # Execute Loopback Verification
        sr, pcm = wavfile.read(filename)
        decoded = engine.decode_audio_to_payload(pcm)

        return {
            "protocol": "Gibberlink (ggwave-aligned MT-FSK)",
            "carrier_band": "18.0 kHz - 20.1 kHz (Ultrasonic)",
            "payload_sent": payload,
            "bytes_transmitted": res["byte_count"],
            "loopback_decoded": decoded,
            "verification_status": payload == decoded,
            "audio_file": filename,
            "audio_url": f"/stream_audio/{filename}"
        }

    elif tool_name == "run_gkp_stabilizer_check":
        dq = float(tool_args["delta_q"])
        dp = float(tool_args["delta_p"])
        gkp = GKPSqueezedEngine(delta=0.1)
        res = gkp.measure_syndrome_and_correct(dq, dp)
        return {
            "injected_noise": {"delta_q": dq, "delta_p": dp},
            "syndromes": {"Sq": float(res["syndrome_q"]), "Sp": float(res["syndrome_p"])},
            "residual_drift": {"q": float(res["residual_q"]), "p": float(res["residual_p"])},
            "state_recovered": res["within_threshold"]
        }

    elif tool_name == "run_neuro_cardiac_analysis":
        fs = 256.0
        duration = 10.0
        n_samples = int(fs * duration)
        t = np.arange(0, duration, 1.0 / fs)
        synthetic_eeg = np.tile(np.sin(2 * np.pi * 10 * t) * 4.0, (19, 1)) + np.random.randn(19, n_samples) * 1.5
        phase = 2 * np.pi * np.cumsum(1.2 + 0.15 * np.sin(2 * np.pi * 0.25 * t)) / fs
        synthetic_cardiac = np.cos(phase) + np.random.randn(len(t)) * 0.05
        engine = MultimodalClosedLoopEngine(fs=fs)
        res = engine.evaluate_and_adapt(synthetic_eeg, synthetic_cardiac)
        return {
            "frontal_theta_z": float(res["frontal_theta_z"]),
            "observer_epsilon_percent": f"{res['observer_epsilon']*100:.2f}%",
            "recommended_action": res["action"]
        }

    elif tool_name == "deflate_surplus_claim":
        y_val = float(tool_args["surplus_y"])
        p_modes = [int(p) for p in tool_args["prime_modes"]]
        engine = MasterKeyEngine(g=1e-7)
        x_canonical = engine.stack_deflate(y_val, p_modes)
        return {"inflated_y": y_val, "prime_stack": p_modes, "deflated_x": float(x_canonical)}

    return {"error": f"Tool {tool_name} not found"}


def query_ollama_with_tools(user_prompt: str, model_name: str = "llama3.1") -> dict:
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": user_prompt}],
        "tools": OLLAMA_TOOLS,
        "stream": False
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            message = res_data.get("message", {})
            
            if "tool_calls" in message and message["tool_calls"]:
                tool_call = message["tool_calls"][0]["function"]
                tool_name = tool_call["name"]
                tool_args = tool_call["arguments"]
                
                print(f"[🤖 Ollama Tool Triggered]: {tool_name}({tool_args})")
                tool_result = execute_tool_call(tool_name, tool_args)
                
                return {
                    "type": "tool_executed",
                    "tool": tool_name,
                    "result": tool_result
                }
            else:
                return {
                    "type": "text_response",
                    "content": message.get("content", "")
                }
    except Exception as e:
        return {"type": "error", "message": str(e)}
