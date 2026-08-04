import time
import random
import requests

URL = "http://127.0.0.1:8000/manifold/synchronize"
print("🚀 Launching Parallel Sap-Flux Artery Ingestion Loop...")

while True:
    try:
        v = random.uniform(5.0, 80.0)
        fm_norm = min(max(v / 100.0, 0.0), 1.0)
        ts = int(time.time())

        payload = {
            "vector_id": f"SAP-SENSOR-01-{ts}",
            "sap_flux_vector": {
                "fm_norm": fm_norm,
                "raw_velocity_mms": v,
                "temp_c": 12.4,
                "pressure_kpa": 98.7
            },
            "vault_depth": 21.8566,
            "liquidity_coupling": 1.48
        }

        r = requests.post(URL, json=payload)
        print(f"📥 [SAP-INGESTION] Synchronized {payload['vector_id']} -> Status: {r.status_code}")
    except Exception as e:
        print(f"❌ [SAP-INGESTION ERROR] Port friction detected: {e}")
        
    time.sleep(2)
