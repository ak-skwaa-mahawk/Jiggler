import os
import sys
import json

# Dynamic lookback: Append parent directory to sys.path before loading native binaries
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tordial_gs_manifold

class ExternalNeuralGateway:
    def __init__(self, mesh_bus):
        self.mesh_bus = mesh_bus
        print("🧠 External Neural Gateway initialized. Listening for telemetry streams...")

    def parse_system_telemetry_json(self, raw_json_packet: str, current_timestamp: int):
        """
        Ingests real-world host metrics and pipes them into native substrate configurations
        """
        try:
            data = json.loads(raw_json_packet)
            cpu_temp = data.get("cpu_temperature_c", 45.0)
            net_latency = data.get("network_latency_ms", 30.0)
            market_volatility = data.get("market_volatility_index", 1.0)
            
            print(f"\n📥 Ingested External Telemetry Packet:")
            print(f"   ├─ Host CPU Temp : {cpu_temp}°C")
            print(f"   ├─ Network Ping  : {net_latency}ms")
            print(f"   └─ Volatility    : {market_volatility}")

            # 1. Map High CPU/Network Latency into Macro Chųų Floods (Viscous Drag)
            if cpu_temp > 65.0 or net_latency > 100.0:
                print("🌧️  [Neural Overload Triggered] Sweeping macro Chųų moisture field broadcasted!")
                self.mesh_bus.broadcast_macro_chuu_flood(2.8, 0.95, current_timestamp)
            else:
                print("🌲 System thermals nominal. Maintaining stable baseline SoilLiquidity fields.")
                self.mesh_bus.broadcast_macro_chuu_flood(1.0, 0.10, current_timestamp)

            return True
        except Exception as e:
            print(f"❌ Error decoding neural gateway packet: {e}")
            return False

# --- LIVE GATEWAY DEMONSTRATION PASS ---
if __name__ == "__main__":
    print("================================================================================")
    print("     🧠 NATIVE NEURAL GATEWAY — EXTERNAL DATA STREAM PIPELINE")
    print("================================================================================")
    
    # Spawn global mesh substrate
    shared_bus = tordial_gs_manifold.PySubstrateMeshBus(0.5)
    gateway = ExternalNeuralGateway(shared_bus)

    # Spawn Actor Alpha (99733) to measure real-time adaptation profiles
    alpha = tordial_gs_manifold.PyCombiner(99733, 1.0)
    alpha.register_to_bus(shared_bus)
    alpha.set_internal_target([0.5, 0.5])
    state_alpha = [0.10, 0.10, 500.0, 1.0]

    # Scenario A: Simulate nominal operating thermals
    normal_packet = json.dumps({
        "cpu_temperature_c": 42.5,
        "network_latency_ms": 15.2,
        "market_volatility_index": 1.0
    })
    gateway.parse_system_telemetry_json(normal_packet, 95000)
    state_alpha, _ = alpha.run_autonomous_session(state_alpha, 1, 0.02, 95001)
    print(f"   └─ Alpha Shih Level Post-Step (Nominal): {state_alpha[3]:.4f}")

    # Scenario B: Simulate high system stress (CPU spike triggers global marsh flooding)
    stress_packet = json.dumps({
        "cpu_temperature_c": 78.9,  
        "network_latency_ms": 145.0,
        "market_volatility_index": 2.4
    })
    gateway.parse_system_telemetry_json(stress_packet, 96000)
    state_alpha, _ = alpha.run_autonomous_session(state_alpha, 1, 0.02, 96001)
    print(f"   └─ Alpha Shih Level Post-Step (Stressed): {state_alpha[3]:.4f}")
    
    print("================================================================================")
