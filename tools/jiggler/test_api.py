# test_api.py
import pytest
from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app)

def test_health_endpoint_and_cors_headers():
    # Verify the baseline telemetry sensors return an unblocked CORS handshake
    response = client.get("/health", headers={"Origin": "https://sites.google.com"})
    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert response.headers.get("access-control-allow-origin") == "https://sites.google.com"

def test_rate_limiter_interceptor(monkeypatch):
    # Force the app into production origin mode to check security compliance
    monkeypatch.setenv("ENV_MODE", "production")
    
    # Fire rapid sequential requests to ensure SlowAPI executes a 429 rate hold
    status_codes = []
    for _ in range(25):  # Adjust number based on your exact limiter setup defaults
        res = client.get("/health")
        status_codes.append(res.status_code)
        
    assert 429 in status_codes, "[-] Traffic Governance Membrane failed to intercept rapid ingress requests."
    print("[+] SlowAPI rate-limiting successfully protected the system substrate.")
