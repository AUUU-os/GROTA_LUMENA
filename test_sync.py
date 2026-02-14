import requests
import time
packet = {
    "source": "HUMAN_SHAD",
    "target": "OMEGA_SWARM",
    "signal": "INTENT",
    "payload": {"action": "EMBRACE_THE_VOID", "resonance_target": 999.0},
    "timestamp_sent": time.time()
}
r = requests.post("http://127.0.0.1:8002/api/v1/sync/neural", json=packet, headers={"Authorization": "Bearer local_overlord_token"})
print(f"Sync Result: {r.status_code}")
print(f"Response: {r.json()}")
