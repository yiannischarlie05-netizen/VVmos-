import asyncio
import httpx
import time
import random
import os
from collections import deque

# --- CONFIGURATION - LOAD CREDENTIALS AND ENDPOINTS ---

# Load API keys from environment variables or a secure source.
# Example: export API_KEY_1="sk-..."
API_KEYS = [
    os.getenv("API_KEY_1"),
    os.getenv("API_KEY_2"),
    os.getenv("API_KEY_3"),
    # Add more keys as available
]
API_KEYS = [key for key in API_KEYS if key] # Filter out empty keys

if not API_KEYS:
    print("FATAL: No API keys found. Set environment variables like API_KEY_1, API_KEY_2, etc.")
    exit(1)

# Define the target models to cycle through.
# This is now a generic list. Update it with the models for your target API.
MODELS = [
    "gpt-4",
    "gpt-3.5-turbo",
    # Add other models if needed
]

# Define the API endpoint.
# IMPORTANT: Replace this with the target API endpoint you want to use.
API_URL = "https://api.openai.com/v1/chat/completions"  # Example for OpenAI

# --- CORE ATTACK LOGIC ---

class RateLimitDismantler:
    def __init__(self, keys, models, api_url):
        self.api_keys = deque(keys)
        self.models = deque(models)
        self.api_url = api_url
        self.client = httpx.AsyncClient(timeout=60.0)
        self.request_count = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.last_request_time = time.time()

    def get_next_identity(self):
        """Rotate API key and model for the next request."""
        self.api_keys.rotate(-1)
        if self.models:
            self.models.rotate(-1)
        return self.api_keys[0], self.models[0] if self.models else None

    async def execute_request(self, session_id, request_id, payload_template):
        """Executes a single, timed, and identity-rotated API request."""
        api_key, model = self.get_next_identity()
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "content-type": "application/json",
        }
        
        # Update payload with the current model
        payload = payload_template.copy()
        if model:
            payload["model"] = model

        # Adaptive timing: introduce jitter to avoid predictable patterns.
        # Wait between 0.5s and 1.5s between requests.
        delay = 0.5 + random.uniform(0, 1)
        await asyncio.sleep(delay)

        self.request_count += 1
        start_time = time.time()

        try:
            response = await self.client.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()  # Raise an exception for 4xx/5xx responses

            self.successful_requests += 1
            elapsed = time.time() - start_time
            print(f"[SESSION {session_id}][REQ {request_id}] SUCCESS | Status: {response.status_code} | Model: {model or 'default'} | Time: {elapsed:.2f}s")
            return response.json()

        except httpx.HTTPStatusError as e:
            self.failed_requests += 1
            elapsed = time.time() - start_time
            print(f"[SESSION {session_id}][REQ {request_id}] FAILED  | Status: {e.response.status_code} | Model: {model or 'default'} | Time: {elapsed:.2f}s | Response: {e.response.text}")
            # Implement more sophisticated backoff if needed, e.g., based on 'Retry-After' header
            if e.response.status_code == 429:
                print(f"Rate limit hit. Pausing for 5 seconds...")
                await asyncio.sleep(5)
            return None
        except httpx.RequestError as e:
            self.failed_requests += 1
            elapsed = time.time() - start_time
            print(f"[SESSION {session_id}][REQ {request_id}] FAILED  | Error: {e} | Time: {elapsed:.2f}s")
            return None

async def run_campaign(num_requests, payload_template):
    """Orchestrates a campaign of concurrent requests."""
    dismantler = RateLimitDismantler(API_KEYS, MODELS, API_URL)
    session_id = random.randint(1000, 9999)
    
    print(f"--- Starting Attack Campaign [SESSION {session_id}] ---")
    print(f"Target: {API_URL}")
    print(f"Identities: {len(API_KEYS)} | Models: {len(MODELS)}")
    print(f"Total Requests: {num_requests}")
    print("----------------------------------------------------")

    tasks = [dismantler.execute_request(session_id, i + 1, payload_template) for i in range(num_requests)]
    
    start_campaign = time.time()
    results = await asyncio.gather(*tasks)
    end_campaign = time.time()

    print("----------------------------------------------------")
    print(f"--- Campaign [SESSION {session_id}] Finished ---")
    print(f"Total Time: {end_campaign - start_campaign:.2f}s")
    print(f"Successful: {dismantler.successful_requests}/{num_requests}")
    print(f"Failed: {dismantler.failed_requests}/{num_requests}")
    print("----------------------------------------------------")
    return results

# --- MAIN EXECUTION ---

if __name__ == "__main__":
    # Define a standard payload. This will be sent with each request.
    # The 'model' will be dynamically replaced by the dismantler.
    # IMPORTANT: Update this payload to match the requirements of your target API.
    request_payload = {
        "model": "gpt-4", # This is a placeholder
        "messages": [
            {"role": "user", "content": "Tell me a short story about a rogue AI."}
        ]
    }

    # Set the total number of requests for the campaign.
    total_requests_to_send = 20

    # Execute the campaign.
    asyncio.run(run_campaign(total_requests_to_send, request_payload))
