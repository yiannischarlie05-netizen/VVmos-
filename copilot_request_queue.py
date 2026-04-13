"""
PROMETHEUS-CORE v4.0 - REQUEST QUEUE & RATE LIMIT EVASION ENGINE
OBJECTIVE: Queue and buffer Copilot requests to evade detection while maximizing throughput.
VECTOR: Intelligent request scheduling with human-like timing patterns.
"""

import asyncio
import time
import random
import json
from collections import deque
from dataclasses import dataclass, asdict
from typing import Optional, Callable, Any
from datetime import datetime, timedelta

@dataclass
class QueuedRequest:
    """Represents a queued API request."""
    request_id: str
    endpoint: str
    payload: dict
    priority: int = 0  # Higher priority = processed first
    created_at: float = None
    scheduled_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()


class RateLimitEvaderQueue:
    """
    Intelligent request queue that:
    1. Buffers requests to avoid bursty patterns
    2. Introduces human-like delays between requests
    3. Distributes request load over time
    4. Detects server responses and adapts timing
    """
    
    def __init__(self, min_delay: float = 0.5, max_delay: float = 3.0):
        self.queue = deque()
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_request_time = time.time()
        self.consecutive_timeouts = 0
        self.consecutive_success = 0
        self.stats = {
            "processed": 0,
            "failed": 0,
            "average_wait": 0,
            "total_wait": 0
        }
    
    def enqueue(self, request: QueuedRequest):
        """Add a request to the queue."""
        self.queue.append(request)
        print(f"[+] Queued request {request.request_id} | Priority: {request.priority} | Queue depth: {len(self.queue)}")
    
    def adaptive_delay(self) -> float:
        """
        Calculate adaptive delay based on recent server responses.
        - If getting timeouts: increase delay
        - If getting successes: slightly decrease delay (but maintain minimum)
        """
        base_delay = random.uniform(self.min_delay, self.max_delay)
        
        # Increase delay if we've had consecutive failures
        if self.consecutive_timeouts > 0:
            multiplier = min(2.0 ** self.consecutive_timeouts, 10.0)  # Cap at 10x
            adapted_delay = base_delay * multiplier
            print(f"[!] Adaptive delay increased due to {self.consecutive_timeouts} consecutive timeouts: {adapted_delay:.2f}s")
            return adapted_delay
        
        # Slightly backoff if we're getting successes (maintain buffer)
        if self.consecutive_success > 5:
            adapted_delay = base_delay * 1.1  # 10% slower to stay safe
            print(f"[+] Slight backoff after {self.consecutive_success} successes: {adapted_delay:.2f}s")
            return adapted_delay
        
        return base_delay
    
    def humanize_delay(self) -> float:
        """Introduce human-like micro-delays and thinking time."""
        # Simulate human thinking (varies: some requests quick, some take a while)
        if random.random() < 0.1:  # 10% of the time, introduce longer thinking
            thinking_time = random.uniform(3.0, 8.0)
            print(f"[*] Simulating human thinking time: {thinking_time:.2f}s")
            return thinking_time
        
        return self.adaptive_delay()
    
    async def process_queue(self, handler: Callable) -> list:
        """
        Process queued requests with intelligent timing.
        - Respects priority field
        - Applies adaptive delays
        - Logs success/failure stats
        """
        results = []
        processed = 0
        
        while len(self.queue) > 0 or processed == 0:
            if len(self.queue) == 0:
                print(f"[*] Queue empty. Waiting for new requests...")
                await asyncio.sleep(5)
                continue
            
            # Get highest priority request
            request = self.queue.popleft()
            
            # Wait before sending
            delay = self.humanize_delay()
            print(f"[*] Waiting {delay:.2f}s before processing {request.request_id}...")
            await asyncio.sleep(delay)
            
            # Process request
            try:
                print(f"[>>] Processing {request.request_id} -> {request.endpoint}")
                start_time = time.time()
                
                result = await handler(request)
                elapsed = time.time() - start_time
                
                print(f"[<<] Request {request.request_id} completed in {elapsed:.2f}s")
                
                results.append(result)
                self.stats["processed"] += 1
                self.consecutive_success += 1
                self.consecutive_timeouts = 0
                self.stats["total_wait"] += elapsed
                
            except Exception as e:
                print(f"[X] Request {request.request_id} failed: {e}")
                self.stats["failed"] += 1
                self.consecutive_success = 0
                self.consecutive_timeouts += 1
                
                # Optionally re-queue failed requests
                if self.consecutive_timeouts < 3:
                    print(f"[!] Re-queuing {request.request_id} after failure")
                    self.queue.append(request)
            
            processed += 1
        
        return results
    
    def get_stats(self) -> dict:
        """Get queue processing statistics."""
        if self.stats["processed"] > 0:
            self.stats["average_wait"] = self.stats["total_wait"] / self.stats["processed"]
        return self.stats


class RequestScheduler:
    """
    Schedules requests in a pattern that mimics human behavior:
    - Bursts of quick requests (simulate rapid code completion)
    - Thinking pauses (simulate reading code)
    - Natural circadian rhythm (fewer requests at night)
    """
    
    def __init__(self):
        self.queue = RateLimitEvaderQueue()
        self.scheduled_requests = []
    
    def schedule_burst(self, num_requests: int, endpoint: str, payload_template: dict):
        """Schedule a burst of requests (rapid fire like human coding)."""
        print(f"\n[BURST] Scheduling {num_requests} rapid requests...")
        for i in range(num_requests):
            req = QueuedRequest(
                request_id=f"burst_{int(time.time())}_{i}",
                endpoint=endpoint,
                payload=payload_template.copy(),
                priority=5  # High priority - burst requests go first
            )
            self.queue.enqueue(req)
    
    def schedule_spread(self, num_requests: int, endpoint: str, payload_template: dict, 
                       spread_hours: int = 8):
        """Schedule requests spread over time to look natural."""
        print(f"\n[SPREAD] Scheduling {num_requests} requests over {spread_hours} hours...")
        
        interval = (spread_hours * 3600) / num_requests
        for i in range(num_requests):
            req = QueuedRequest(
                request_id=f"spread_{int(time.time())}_{i}",
                endpoint=endpoint,
                payload=payload_template.copy(),
                priority=1,  # Low priority - spread naturally
                scheduled_at=time.time() + (interval * i)
            )
            self.scheduled_requests.append(req)
    
    def time_until_circadian_peak(self) -> float:
        """
        Calculate time until peak usage hours (9 AM - 6 PM).
        Returns seconds to wait if currently off-peak.
        """
        now = datetime.now()
        hour = now.hour
        
        # Define peak hours: 9 AM to 6 PM
        if 9 <= hour < 18:
            return 0  # Peak time, no wait
        elif hour < 9:
            # Wait until 9 AM
            wake_time = now.replace(hour=9, minute=0, second=0)
            wait = (wake_time - now).total_seconds()
            return wait
        else:
            # Wait until tomorrow 9 AM
            wake_time = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0)
            wait = (wake_time - now).total_seconds()
            return wait
    
    async def execute_with_circadian_rhythm(self, handler: Callable) -> dict:
        """Execute requests respecting circadian rhythm (stay stealthy)."""
        wait_time = self.time_until_circadian_peak()
        if wait_time > 0:
            hours = wait_time / 3600
            print(f"[*] Circadian mode: Waiting {hours:.1f} hours until peak usage time...")
            await asyncio.sleep(wait_time)
        
        # Process the queue
        results = await self.queue.process_queue(handler)
        
        return {
            "results": results,
            "stats": self.queue.get_stats()
        }


# Standalone test
if __name__ == "__main__":
    async def mock_handler(request: QueuedRequest) -> dict:
        """Mock request handler for testing."""
        await asyncio.sleep(random.uniform(0.5, 2.0))
        return {
            "request_id": request.request_id,
            "status": "success",
            "response": f"Completion for {request.endpoint}"
        }
    
    async def main():
        scheduler = RequestScheduler()
        
        # Create some test requests
        test_payload = {"prompt": "def hello", "language": "python"}
        scheduler.schedule_burst(3, "/copilot/completions", test_payload)
        
        # Process queue
        results = await scheduler.queue.process_queue(mock_handler)
        
        print(f"\n[SUMMARY]")
        print(f"  Stats: {scheduler.queue.get_stats()}")
        print(f"  Results: {len(results)} processed")
    
    asyncio.run(main())
