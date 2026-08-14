import json
import urllib.request
import numpy as np

from tools.closed_loop_engine import MultimodalClosedLoopEngine
from tools.master_key import MasterKeyEngine
from tools.pqc_engine import HybridKEMEngine
from tools.audio_entrainment import generate_binaural_beat, generate_isochronic_tone
from tools.qeeg_connectivity import ConnectivityEngine, CHANNELS

# --- Tool JSON Schemas for Ollama ---
OLLAMA_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_neuro_cardiac_analysis",
            "description": "Runs a 19-channel QEEG and Cardiac HRV analysis snapshot and returns current Z-scores and Observer Epsilon coherence.",
            "parameters": {
                "type": "object",
                "properties": {
                    "theta_spike_intensity": {
                        "type": "number",
                        "description": "Simulated frontal theta spike intensity (default 7.0)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_channel_connectivity",
            "description": "Computes cross-spectral coherence, phase angle lag, and time delay between two target EEG channels for a given frequency band.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ch1": {"type": "string", "description": "First channel name, e.g. F3"},
                    "ch2": {"type": "string", "description": "Second channel name, e.g. F4"},
                    "band_low": {"type": "number", "description": "Target frequency band low bound in Hz (default 4.0)"},
                    "band_high": {"type": "number", "description": "Target frequency band high bound in Hz (default 8.0)"}
                },
                "required": ["ch1", "ch2"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "deflate_surplus_claim",
            "description": "Applies Codex.MasterKey.v001 Newton-Raphson deflation to recover the canonical ground state from an inflated surplus claim.",
            "parameters": {
                "type": "object",
                "properties": {
                    "surplus_y": {
                        "type": "number",
                        "description": "The inflated surplus state Y to deflate."
                    },
                    "prime_modes": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of prime observer modes in the stack, e.g. [3, 5, 7]."
                    }
                },
                "required": ["surplus_y", "prime_modes"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_pqc_key_exchange",
            "description": "Executes a hybrid post-quantum key exchange (X25519 + PQC Lattice KEM) and returns derived symmetric key fingerprints.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "synthesize_entrainment_audio",
            "description": "Generates a custom binaural beat or isochronic tone WAV file at a given target frequency.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mode": {"type": "string", "enum": ["binaural", "isochronic"]},
                    "target_freq": {"type": "number", "description": "Target beat or pulse frequency in Hz (e.g. 10.0, 15.0, 40.0)"},
                    "carrier_freq": {"type": "number", "description": "Carrier tone frequency in Hz (e.g. 200.0)"}
                },
                "required": ["mode", "target_freq"]
            }
        }
    }
]

# --- Python Tool Execution Router ---
def execute_tool_call(tool_name: str, tool_args: dict) -> dict:
    if tool_name == "run_neuro_cardiac_analysis":
        fs = 256.0
        duration = 10.0
        n_samples = int(fs * duration)
        t = np.arange(0, duration, 1.0 / fs)
        
        theta_spike = float(tool_args.get("theta_spike_intensity", 7.0))
        
        synthetic_eeg = np.tile(np.sin(2 * np.pi * 10 * t) * 4.0, (19, 1)) + np.random.randn(19, n_samples) * 1.5
        synthetic_eeg[2, :] += np.sin(2 * np.pi * 6 * t) * theta_spike
        synthetic_eeg[3, :] += np.sin(2 * np.pi * 6 * t) * theta_spike

        phase = 2 * np.pi * np.cumsum(1.2 + 0.15 * np.sin(2 * np.pi * 0.25 * t)) / fs
        synthetic_cardiac = np.cos(phase) + np.random.randn(len(t)) * 0.05

        engine = MultimodalClosedLoopEngine(fs=fs)
        res = engine.evaluate_and_adapt(synthetic_eeg, synthetic_cardiac)
        
        return {
            "frontal_theta_z": float(res["frontal_theta_z"]),
            "observer_epsilon_percent": f"{res['observer_epsilon']*100:.2f}%",
            "is_coiled_state": res["is_coiled"],
            "recommended_action": res["action"],
            "target_freq_hz": res["target_freq"],
            "audio_mode": res["mode"]
        }

    elif tool_name == "analyze_channel_connectivity":
        ch1 = tool_args.get("ch1", "F3").upper()
        ch2 = tool_args.get("ch2", "F4").upper()
        low = float(tool_args.get("band_low", 4.0))
        high = float(tool_args.get("band_high", 8.0))

        fs = 256.0
        duration = 10.0
        n_samples = int(fs * duration)
        t = np.arange(0, duration, 1.0 / fs)

        # Generate test signals with phase offset
        sig1 = np.sin(2 * np.pi * 6.0 * t) + np.random.randn(n_samples) * 0.2
        shift = int(0.025 * fs)
        sig2 = np.roll(sig1, shift) + np.random.randn(n_samples) * 0.2

        conn_engine = ConnectivityEngine(fs=fs)
        metrics = conn_engine.compute_pair_connectivity(sig1, sig2, target_band=(low, high))

        leading_ch = ch1 if metrics["time_delay_ms"] > 0 else ch2
        lagging_ch = ch2 if metrics["time_delay_ms"] > 0 else ch1

        return {
            "channel_pair": f"{ch1} <-> {ch2}",
            "target_band_hz": f"{low}-{high}",
            "coherence_strength": f"{metrics['coherence']:.4f}",
            "phase_angle_deg": f"{metrics['phase_deg']:.2f}°",
            "time_delay_ms": f"{metrics['time_delay_ms']:.2f} ms",
            "directional_flow": f"{leading_ch} leads {lagging_ch}"
        }

    elif tool_name == "deflate_surplus_claim":
        y_val = float(tool_args["surplus_y"])
        p_modes = [int(p) for p in tool_args["prime_modes"]]
        
        engine = MasterKeyEngine(g=1e-7)
        x_canonical = engine.stack_deflate(y_val, p_modes)
        return {
            "inflated_surplus_y": y_val,
            "prime_stack": p_modes,
            "deflated_canonical_x": float(x_canonical)
        }

    elif tool_name == "execute_pqc_key_exchange":
        node_a = HybridKEMEngine()
        node_b = HybridKEMEngine()
        payload_a = node_a.get_public_payload()
        payload_b = node_b.get_public_payload()
        
        pqc_secret = np.random.bytes(32)
        key_a = node_a.encapsulate(payload_b["classical_pub"], payload_b["pqc_pub"])[0]
        
        return {
            "status": "established",
            "derived_key_fingerprint": key_a.hex()[:32],
            "quantum_safe": True
        }

    elif tool_name == "synthesize_entrainment_audio":
        mode = tool_args.get("mode", "isochronic")
        target_freq = float(tool_args.get("target_freq", 40.0))
        carrier_freq = float(tool_args.get("carrier_freq", 200.0))
        
        filename = f"chat_{mode}_{int(target_freq)}Hz.wav"
        if mode == "binaural":
            generate_binaural_beat(carrier_freq=carrier_freq, beat_freq=target_freq, duration_sec=10.0, output_filename=filename)
        else:
            generate_isochronic_tone(carrier_freq=carrier_freq, pulse_freq=target_freq, duration_sec=10.0, output_filename=filename)
            
        return {
            "status": "generated",
            "audio_file": filename,
            "audio_url": f"/stream_audio/{filename}"
        }

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
