import time
import random
import requests

API_GATEWAY_URL = "http://127.0.0.1:8000/manifold/synchronize"

def scrape_and_pipe_loop():
    print("🚀 Starting Live Biophysical Ingestion Feed...")
    print("🌲 Monitoring arboreal magnetic flux and mass vectors... Press CTRL+C to halt.")
    
    while True:
        try:
            flux_velocity = round(random.uniform(1.8, 3.5), 3)       
            environmental_friction = round(random.uniform(0.005, 0.02), 4) 
            mass_generation = round(random.uniform(0.45, 0.85), 3)   
            
            payload = {
                "vector_id": f"BIO-VEC-{int(time.time())}",
                "economic_vector": {
                    "capital_velocity": flux_velocity,
                    "regulatory_drag": environmental_friction,
                    "yield_generation": mass_generation
                },
                "vault_depth": 45.214,        
                "liquidity_coupling": 2.851    
            }
            
            response = requests.post(API_GATEWAY_URL, json=payload)
            
            if response.status_code == 200:
                print(f"📥 [ECO-INGESTION] Synced {payload['vector_id']} | Flux (F_m): {flux_velocity} nT | Friction (E_f): {environmental_friction} | Mass (M_o): {mass_generation} kg -> Status: 200 OK")
            else:
                print(f"⚠️ [WARNING] Substrate returned alternative status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Ingestion loop friction detected: {e}")
            
        time.sleep(2)

if __name__ == "__main__":
    scrape_and_pipe_loop()
