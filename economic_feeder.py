import time
import random
import requests

API_GATEWAY_URL = "http://127.0.0.1:8000/manifold/synchronize"


def scrape_and_pipe_loop():
    print("🚀 Starting Live Topological Economic Ingestion Feed...")
    print("📡 Monitoring target platform parameters... Press CTRL+C to halt.")

    while True:
        try:
            # 💡 REAL-TIME SCRAPING PIVOT:
            # Replace these mock variables with your live scraped metrics
            # from platform APIs, smart contracts, or public financial ledgers.
            scraped_velocity = round(random.uniform(2.5, 4.2), 3)   # Capital Velocity
            scraped_drag = round(random.uniform(0.01, 0.05), 4)     # Tax/Regulatory Drag
            scraped_yield = round(random.uniform(0.12, 0.35), 3)    # Yield Generation

            payload = {
                "vector_id": f"VEC-{int(time.time())}",
                "economic_vector": {
                    "capital_velocity": scraped_velocity,
                    "regulatory_drag": scraped_drag,
                    "yield_generation": scraped_yield,
                },
                "vault_depth": 21.8566,
                "liquidity_coupling": 1.48,
            }

            response = requests.post(API_GATEWAY_URL, json=payload)

            if response.status_code == 200:
                print(
                    f"📥 [INGESTION] Synced vector {payload['vector_id']} | "
                    f"V_c: {scraped_velocity} | D_r: {scraped_drag} | "
                    f"Y_g: {scraped_yield} -> Response: 200 OK"
                )
            else:
                print(
                    f"⚠️ [WARNING] Substrate returned alternative status: "
                    f"{response.status_code}"
                )

        except Exception as e:
            print(f"❌ Ingestion loop friction detected: {e}")

        time.sleep(2)


if __name__ == "__main__":
    scrape_and_pipe_loop()