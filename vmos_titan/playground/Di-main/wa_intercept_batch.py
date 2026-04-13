import requests
API_URL = "https://8000-ir356g0rpexbhdtsrpvs1-dfc00ec5.sandbox.novita.ai/whatsapp/intercept/deploy"
API_KEY = "Bearer wa_intercept_api"
devices = ["android_device_udid_1", "android_device_udid_2"]

for dev_id in devices:
    payload = {"device": dev_id, "mode": "voice-tap", "recording": True}
    headers = {"Authorization": API_KEY, "Content-Type": "application/json"}
    resp = requests.post(API_URL, json=payload, headers=headers)
    print(f"[{dev_id}] {resp.status_code}: {resp.text}")