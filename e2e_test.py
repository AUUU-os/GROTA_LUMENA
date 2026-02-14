import requests
import json
import time

nodes = {
    "Omega Central (8000)": "http://127.0.0.1:8000",
    "Grota Node (8002)": "http://127.0.0.1:8002"
}

for name, url in nodes.items():
    print(f"\n--- Testing {name} ---")
    
    health_url = f"{url}/health" if "8000" in url else f"{url}/api/v1/health"
    try:
        r = requests.get(health_url, timeout=2)
        print(f"Health ({health_url}): {r.status_code} - {r.json() if r.status_code==200 else r.text}")
    except Exception as e:
        print(f"Health Error: {e}")

    time.sleep(0.1) # Respect the wolf

    if "8002" in url:
        for endpoint in ["/api/v1/swarm/health", "/api/v1/swarm/routes"]:
            try:
                r = requests.get(f"{url}{endpoint}", timeout=2)
                print(f"Swarm ({endpoint}): {r.status_code}")
                if r.status_code == 200:
                    print(f"  Data: {json.dumps(r.json())[:100]}...")
                time.sleep(0.1)
            except Exception as e:
                print(f"Swarm Error ({endpoint}): {e}")
