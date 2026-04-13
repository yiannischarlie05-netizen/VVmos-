"""
Behavioral synthesis engine using Poisson-process modeling
to defeat ML-based fraud detection and behavioral biometrics.
"""
import math
import random
from typing import List, Tuple


class PoissonTouchSynthesizer:
    """
    Generates human-like touch event sequences using inhomogeneous
    Poisson processes to defeat behavioral biometric detection
    (e.g., BioCatch DeviceIQ).
    """

    def __init__(self, seed: int = None):
        if seed is not None:
            random.seed(seed)

    def generate_tap(self, target_x: int, target_y: int,
                     jitter_radius: float = 8.0) -> List[dict]:
        """
        Generate a realistic tap event with Poisson-modeled micro-jitter.
        """
        events = []
        # Phase 1: Approach — finger descending
        num_approach = random.randint(2, 5)
        for i in range(num_approach):
            dx = random.gauss(0, jitter_radius * 0.3)
            dy = random.gauss(0, jitter_radius * 0.3)
            pressure = 0.1 + (i / num_approach) * 0.4
            events.append({
                "type": "EV_ABS",
                "x": target_x + dx,
                "y": target_y + dy,
                "pressure": round(pressure, 3),
                "touch_major": random.uniform(4, 8),
            })

        # Phase 2: Contact — main press
        contact_jitter_x = random.gauss(0, jitter_radius * 0.15)
        contact_jitter_y = random.gauss(0, jitter_radius * 0.15)
        events.append({
            "type": "EV_ABS",
            "x": target_x + contact_jitter_x,
            "y": target_y + contact_jitter_y,
            "pressure": round(random.uniform(0.45, 0.7), 3),
            "touch_major": random.uniform(8, 14),
        })

        # Phase 3: Hold with micro-drift
        hold_samples = random.randint(3, 8)
        for _ in range(hold_samples):
            dx = random.gauss(0, jitter_radius * 0.08)
            dy = random.gauss(0, jitter_radius * 0.08)
            events.append({
                "type": "EV_ABS",
                "x": target_x + contact_jitter_x + dx,
                "y": target_y + contact_jitter_y + dy,
                "pressure": round(random.uniform(0.4, 0.65), 3),
                "touch_major": random.uniform(7, 13),
            })

        # Phase 4: Release
        num_release = random.randint(2, 4)
        for i in range(num_release):
            pressure = 0.4 * (1 - (i + 1) / num_release)
            events.append({
                "type": "EV_ABS",
                "x": target_x + random.gauss(0, jitter_radius * 0.2),
                "y": target_y + random.gauss(0, jitter_radius * 0.2),
                "pressure": round(max(0, pressure), 3),
                "touch_major": random.uniform(3, 7),
            })

        return events

    def generate_swipe(self, start: Tuple[int, int], end: Tuple[int, int],
                       duration_ms: int = 300, sample_rate: int = 60) -> List[dict]:
        """
        Generate a realistic swipe trajectory with Poisson jitter
        and Fitts's Law velocity modulation.
        """
        events = []
        num_samples = max(5, int(duration_ms / 1000 * sample_rate))
        distance = math.hypot(end[0] - start[0], end[1] - start[1])

        for i in range(num_samples):
            t = i / (num_samples - 1)
            # Ease-in-out cubic for natural acceleration
            if t < 0.5:
                ease = 4 * t * t * t
            else:
                ease = 1 - pow(-2 * t + 2, 3) / 2

            base_x = start[0] + (end[0] - start[0]) * ease
            base_y = start[1] + (end[1] - start[1]) * ease

            # Poisson-modulated jitter — higher in midswipe
            lambda_mid = 3.0 * math.sin(math.pi * t)
            jitter_scale = max(0.5, random.expovariate(1 / (lambda_mid + 0.1)))
            jitter_scale = min(jitter_scale, 12.0)

            dx = random.gauss(0, jitter_scale)
            dy = random.gauss(0, jitter_scale)

            pressure = 0.35 + 0.25 * math.sin(math.pi * t)
            events.append({
                "type": "EV_ABS",
                "x": round(base_x + dx, 1),
                "y": round(base_y + dy, 1),
                "pressure": round(pressure + random.gauss(0, 0.03), 3),
                "touch_major": round(random.uniform(6, 12), 1),
                "timestamp_ms": round(i * (duration_ms / num_samples), 1),
            })

        return events

    def generate_typing_delay_ms(self, wpm: int = 42) -> float:
        """
        Generate inter-keystroke delay using Poisson process
        to model realistic typing rhythm at a given WPM.
        """
        chars_per_sec = (wpm * 5) / 60
        mean_delay = 1000.0 / chars_per_sec
        # Poisson-like variation
        delay = random.expovariate(1.0 / mean_delay)
        return round(max(30, min(delay, 800)), 1)
