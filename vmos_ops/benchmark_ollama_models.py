import requests
import time

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODELS = [
    "deepseek-coder:6.7b",
    "qwen2.5-coder:7b",
    "codellama:7b",
    "cybersec-coder:latest"
]
PROMPT = "Write a Python function to compute the nth Fibonacci number recursively."

results = []

for model in MODELS:
    data = {"model": model, "prompt": PROMPT, "stream": False}
    print(f"Testing model: {model}")
    start = time.time()
    try:
        resp = requests.post(OLLAMA_URL, json=data, timeout=120)
        duration = time.time() - start
        if resp.ok:
            out = resp.json()
            print(f"Model: {model}\nTime: {duration:.2f}s\nResponse: {out.get('response','')[:120]}...\n")
            results.append((model, duration, out.get('response','')[:120]))
        else:
            print(f"Model: {model} failed with status {resp.status_code}")
    except Exception as e:
        print(f"Model: {model} error: {e}")

print("\nSummary:")
for model, duration, preview in results:
    print(f"{model}: {duration:.2f}s | {preview}...")
