"""
VMOS-Titan Testing Playground

Complete testing and visual verification suite for VMOS Pro Cloud:
- Web Dashboard (FastAPI + React)
- Terminal TUI (Rich/Textual)
- Jupyter Notebooks
- CLI Tools

Covers all 11 Genesis phases, Google account injection, wallet provisioning,
purchase history forging, and device backdating with visual verification.
"""

from .controller import PlaygroundController
from .phase_registry import PHASES, PhaseInfo
from .screenshot_capture import ScreenshotCapture
from .visual_verifier import VisualVerifier
from .backdater import DeviceBackdater

__all__ = [
    "PlaygroundController",
    "PHASES",
    "PhaseInfo",
    "ScreenshotCapture",
    "VisualVerifier",
    "DeviceBackdater",
]

__version__ = "1.0.0"
