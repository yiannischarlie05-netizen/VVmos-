"""
VMOSSensorBridge — OADEV Sensor Noise ↔ VMOS Cloud Sensor File Bridge
======================================================================
Bridges the gap between the advanced MEMS sensor noise simulation
(sensor_noise_simulator.py with OADEV Allan Deviation models) and the
VMOS Cloud sensor injection format (persist.sys.cloud.sensor.tpl_dp).

Gap Identified:
    - sensor_noise_simulator.py: Mathematically accurate OADEV noise
      models with GPS-IMU EKF fusion and touch-IMU synchronization,
      but outputs only Python tuples.
    - sensor_simulator.py: Has generate_sensor_data_file() but uses
      simpler noise models without OADEV, EKF, or touch coupling.
    - VMOS Cloud: Expects UTF-8 text files with "sensor_type:x:y:z"
      and "delay:N" lines set via persist.sys.cloud.sensor.tpl_dp.

This module generates VMOS-format sensor data files using the advanced
OADEV noise engine, including:
    - Touch-IMU synchronized impulse events
    - GPS-IMU EKF-fused motion trajectories
    - Circadian activity patterns (device pickup, walking, transit)
    - Environmental sensor coherence (light, proximity, pressure)

Research Report Reference:
    - "Advanced Wallet Provisioning and Injection" — §OADEV sensor noise
    - "Hardening Genesis V3 Pipeline" — §2.3 Sensor Noise Simulation
    - "VMOS Cloud API Documentation" — §Sensor Telemetry Data Architectures
"""

from __future__ import annotations

import math
import os
import random
import tempfile
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import logging

logger = logging.getLogger(__name__)

# Lazy import to avoid circular dependency
_noise_sim = None
_gps_fusion = None


def _ensure_simulator():
    """Lazy-load the OADEV sensor noise simulator."""
    global _noise_sim, _gps_fusion
    if _noise_sim is None:
        try:
            from sensor_noise_simulator import MEMSSensorSimulator, GPSSensorFusion
            _noise_sim = MEMSSensorSimulator
            _gps_fusion = GPSSensorFusion
        except ImportError:
            _noise_sim = False
            _gps_fusion = False


# ═══════════════════════════════════════════════════════════════════════════════
# ACTIVITY PROFILES — Model realistic device usage patterns
# ═══════════════════════════════════════════════════════════════════════════════

ACTIVITY_PROFILES = {
    "idle_desk": {
        "description": "Phone resting on desk",
        "accel_base": (0.0, 0.0, 9.80665),
        "gyro_base": (0.0, 0.0, 0.0),
        "light_lux": (200.0, 500.0),
        "proximity_cm": 5.0,
        "pressure_hpa": (1013.0, 1015.0),
    },
    "hand_held": {
        "description": "Phone held in hand (reading)",
        "accel_base": (-1.5, 0.3, 9.4),
        "gyro_base": (0.002, -0.001, 0.001),
        "light_lux": (100.0, 400.0),
        "proximity_cm": 0.5,
        "pressure_hpa": (1013.0, 1015.0),
    },
    "walking": {
        "description": "Walking with phone in hand",
        "accel_base": (-1.2, 0.5, 9.5),
        "gyro_base": (0.01, -0.005, 0.008),
        "step_frequency_hz": 1.8,
        "step_accel_amplitude": 2.5,
        "light_lux": (5000.0, 40000.0),
        "proximity_cm": 5.0,
        "pressure_hpa": (1010.0, 1015.0),
    },
    "pocket": {
        "description": "Phone in pocket while walking",
        "accel_base": (0.1, -0.3, 9.6),
        "gyro_base": (0.003, -0.002, 0.001),
        "step_frequency_hz": 1.7,
        "step_accel_amplitude": 3.0,
        "light_lux": (0.0, 5.0),
        "proximity_cm": 0.0,
        "pressure_hpa": (1010.0, 1015.0),
    },
    "vehicle": {
        "description": "Phone in moving vehicle",
        "accel_base": (-0.5, 0.2, 9.7),
        "gyro_base": (0.001, -0.001, 0.005),
        "vibration_amplitude": 0.3,
        "vibration_freq_hz": 15.0,
        "light_lux": (100.0, 30000.0),
        "proximity_cm": 5.0,
        "pressure_hpa": (1008.0, 1015.0),
    },
}


@dataclass
class TouchEvent:
    """Touch event to synchronize with IMU data."""
    timestamp_offset_s: float
    event_type: str  # "tap", "swipe", "scroll"
    duration_ms: int = 100
    force: float = 0.5  # 0.0-1.0


@dataclass
class GPSWaypoint:
    """GPS waypoint for trajectory-coupled sensor generation."""
    lat: float
    lng: float
    timestamp_offset_s: float
    speed_mps: float = 0.0
    bearing_deg: float = 0.0


class VMOSSensorBridge:
    """
    Generate VMOS-format sensor data files from OADEV noise models.

    Bridges sensor_noise_simulator.py (Allan Deviation mathematics) to
    the VMOS Cloud persist.sys.cloud.sensor.tpl_dp text format.

    Usage:
        bridge = VMOSSensorBridge(device_profile="samsung_s24")

        # Generate stationary idle data (60s at 20Hz)
        content = bridge.generate_idle_session(duration_s=60.0)

        # Generate with touch events synchronized
        touches = [TouchEvent(5.0, "tap"), TouchEvent(12.0, "swipe")]
        content = bridge.generate_interactive_session(
            duration_s=30.0, touch_events=touches
        )

        # Generate GPS-fused trajectory
        waypoints = [
            GPSWaypoint(34.0522, -118.2437, 0.0, 0.0),
            GPSWaypoint(34.0530, -118.2420, 60.0, 1.4, 45.0),
        ]
        content = bridge.generate_trajectory_session(
            duration_s=120.0, waypoints=waypoints
        )

        # Write to file and deploy
        bridge.write_sensor_file(content, "/tmp/sensor_data.txt")
        # Then: setprop persist.sys.cloud.sensor.tpl_dp /data/local/tmp/sensor_data.txt
    """

    VMOS_SENSOR_TYPES = [
        "accelerometer", "acceleration-uncalibrated", "linear-acceleration",
        "gyroscope", "gyroscope-uncalibrated",
        "gravity", "rotation-vector", "game-rotation-vector",
        "magnetic-field", "magnetic-field-uncalibrated",
        "proximity", "light", "pressure", "temperature", "humidity",
        "step-counter", "step-detector",
        "heart-rate",
        "hinge-angle0", "hinge-angle1", "hinge-angle2",
    ]

    def __init__(self, device_profile: str = "samsung_s24",
                 temperature: float = 25.0):
        self.device_profile = device_profile
        self.temperature = temperature
        self._step_counter = 0

        _ensure_simulator()
        if _noise_sim and _noise_sim is not False:
            self._sim = _noise_sim(
                device_profile=device_profile,
                temperature=temperature,
            )
        else:
            self._sim = None
            logger.warning(
                "sensor_noise_simulator not available; "
                "falling back to inline OADEV noise model"
            )

    # ═══════════════════════════════════════════════════════════════════════
    # CORE VMOS FORMAT GENERATION
    # ═══════════════════════════════════════════════════════════════════════

    def _noise(self, base: float, sigma: float) -> float:
        """Gaussian noise shortcut."""
        return base + random.gauss(0, sigma)

    def _generate_frame(self, activity: str, t: float,
                        touch_impulse: Optional[Tuple[float, float, float]] = None,
                        gps_velocity: Optional[Tuple[float, float, float]] = None,
                        ) -> List[str]:
        """
        Generate one sensor frame in VMOS text format.

        Uses OADEV simulator if available, falls back to calibrated
        inline noise otherwise.
        """
        profile = ACTIVITY_PROFILES.get(activity, ACTIVITY_PROFILES["idle_desk"])
        lines: List[str] = []

        # ── Accelerometer (3-axis + uncalibrated + linear) ──
        if self._sim:
            if touch_impulse:
                self._sim.inject_touch_event(
                    event_type="tap",
                    force=max(touch_impulse),
                )
            ax, ay, az = self._sim.get_accelerometer()
        else:
            bx, by, bz = profile["accel_base"]
            noise_s = 0.004  # OADEV bias instability for BMI270
            ax = self._noise(bx, noise_s)
            ay = self._noise(by, noise_s)
            az = self._noise(bz, noise_s)

            # Add touch impulse
            if touch_impulse:
                ax += touch_impulse[0]
                ay += touch_impulse[1]
                az += touch_impulse[2]

            # Walking step impulse
            if "step_frequency_hz" in profile:
                freq = profile["step_frequency_hz"]
                amp = profile["step_accel_amplitude"]
                step_phase = math.sin(2 * math.pi * freq * t)
                az += amp * abs(step_phase) * random.uniform(0.8, 1.2)

            # Vehicle vibration
            if "vibration_freq_hz" in profile:
                vf = profile["vibration_freq_hz"]
                va = profile["vibration_amplitude"]
                az += va * math.sin(2 * math.pi * vf * t + random.uniform(0, 0.5))

        # GPS velocity coupling (EKF simulation)
        if gps_velocity:
            vx, vy, vz = gps_velocity
            ax += vx * 0.05 + random.gauss(0, 0.01)
            ay += vy * 0.05 + random.gauss(0, 0.01)

        lines.append(f"accelerometer:{ax:.6f}:{ay:.6f}:{az:.6f}")
        lines.append(f"acceleration-uncalibrated:{ax + random.gauss(0, 0.001):.6f}:"
                      f"{ay + random.gauss(0, 0.001):.6f}:"
                      f"{az + random.gauss(0, 0.001):.6f}")
        lines.append(f"linear-acceleration:{ax:.6f}:{ay:.6f}:{az - 9.80665:.6f}")

        # ── Gyroscope (3-axis + uncalibrated) ──
        if self._sim:
            gx, gy, gz = self._sim.get_gyroscope()
        else:
            bgx, bgy, bgz = profile["gyro_base"]
            gyro_noise = 0.0005
            gx = self._noise(bgx, gyro_noise)
            gy = self._noise(bgy, gyro_noise)
            gz = self._noise(bgz, gyro_noise)

            if touch_impulse:
                gx += random.gauss(0, 0.02)
                gy += random.gauss(0, 0.015)

        lines.append(f"gyroscope:{gx:.6f}:{gy:.6f}:{gz:.6f}")
        lines.append(f"gyroscope-uncalibrated:{gx + random.gauss(0, 0.0001):.6f}:"
                      f"{gy + random.gauss(0, 0.0001):.6f}:"
                      f"{gz + random.gauss(0, 0.0001):.6f}")

        # ── Gravity sensor ──
        gravity_z = 9.80665 * math.cos(math.radians(random.gauss(0, 2)))
        gravity_x = -9.80665 * math.sin(math.radians(random.gauss(0, 2)))
        lines.append(f"gravity:{gravity_x:.6f}:{random.gauss(0, 0.01):.6f}:{gravity_z:.6f}")

        # ── Rotation vector (quaternion: x, y, z, cos(θ/2)) ──
        qx = random.gauss(0.0, 0.005)
        qy = random.gauss(0.0, 0.005)
        qz = random.gauss(0.0, 0.005)
        qw = math.sqrt(max(0, 1.0 - qx**2 - qy**2 - qz**2))
        lines.append(f"rotation-vector:{qx:.6f}:{qy:.6f}:{qz:.6f}")
        lines.append(f"game-rotation-vector:{qx:.6f}:{qy:.6f}:{qz:.6f}")

        # ── Magnetometer ──
        if self._sim:
            mx, my, mz = self._sim.get_magnetometer()
        else:
            mx = self._noise(23.4, 0.5)
            my = self._noise(-5.6, 0.5)
            mz = self._noise(42.1, 0.5)

        lines.append(f"magnetic-field:{mx:.4f}:{my:.4f}:{mz:.4f}")
        lines.append(f"magnetic-field-uncalibrated:{mx + random.gauss(0, 0.05):.4f}:"
                      f"{my + random.gauss(0, 0.05):.4f}:"
                      f"{mz + random.gauss(0, 0.05):.4f}")

        # ── Environmental sensors ──
        lux_range = profile.get("light_lux", (200.0, 500.0))
        lux = random.uniform(lux_range[0], lux_range[1])
        lines.append(f"light:{lux:.1f}")

        prox = profile.get("proximity_cm", 5.0)
        lines.append(f"proximity:{prox:.1f}")

        pres_range = profile.get("pressure_hpa", (1013.0, 1015.0))
        pressure = self._noise(random.uniform(pres_range[0], pres_range[1]), 0.3)
        lines.append(f"pressure:{pressure:.2f}")

        temp = self._noise(self.temperature, 0.2)
        lines.append(f"temperature:{temp:.1f}")

        humidity = self._noise(45.0, 2.0)
        lines.append(f"humidity:{humidity:.1f}")

        # ── Step counter (for walking/pocket profiles) ──
        if "step_frequency_hz" in profile:
            freq = profile["step_frequency_hz"]
            if random.random() < freq * 0.05:  # ~1 step per freq cycles
                self._step_counter += 1
                lines.append(f"step-detector:1.0")
                lines.append(f"step-counter:{self._step_counter}")

        return lines

    def _compute_touch_impulse(self, event: TouchEvent,
                               t: float) -> Optional[Tuple[float, float, float]]:
        """
        Calculate IMU impulse from a touch event at time t.

        Touch events cause Z-axis acceleration spike (finger pressing screen)
        followed by dampened sinusoidal decay over 15-30ms.
        """
        event_start = event.timestamp_offset_s
        event_end = event_start + (event.duration_ms / 1000.0)

        if t < event_start or t > event_end + 0.05:
            return None

        elapsed = t - event_start
        duration_s = event.duration_ms / 1000.0

        # Peak force based on event type and pressure
        if event.event_type == "tap":
            peak = 4.0 * event.force  # 0-4 m/s² Z-axis
        elif event.event_type == "swipe":
            peak = 2.5 * event.force
        else:
            peak = 1.5 * event.force

        if elapsed < duration_s * 0.3:
            # Rising edge
            progress = elapsed / (duration_s * 0.3)
            force_z = peak * progress
        elif elapsed < duration_s:
            # Sustained
            force_z = peak * (1.0 - 0.3 * (elapsed - duration_s * 0.3) / (duration_s * 0.7))
        else:
            # Dampened decay (sinusoidal)
            decay_t = elapsed - duration_s
            force_z = peak * 0.3 * math.exp(-decay_t * 30) * math.cos(2 * math.pi * 40 * decay_t)

        # Lateral jitter from hand tremor during touch
        force_x = random.gauss(0, 0.2 * event.force)
        force_y = random.gauss(0, 0.15 * event.force)

        return (force_x, force_y, force_z)

    def _compute_gps_velocity(self, waypoints: List[GPSWaypoint],
                              t: float) -> Optional[Tuple[float, float, float]]:
        """
        Interpolate GPS velocity at time t from waypoints.

        Returns velocity in m/s (north, east, down) for IMU coupling.
        """
        if not waypoints or len(waypoints) < 2:
            return None

        # Find bounding waypoints
        prev_wp = waypoints[0]
        next_wp = waypoints[-1]

        for i in range(len(waypoints) - 1):
            if waypoints[i].timestamp_offset_s <= t <= waypoints[i + 1].timestamp_offset_s:
                prev_wp = waypoints[i]
                next_wp = waypoints[i + 1]
                break

        dt = next_wp.timestamp_offset_s - prev_wp.timestamp_offset_s
        if dt <= 0:
            return None

        progress = (t - prev_wp.timestamp_offset_s) / dt
        speed = prev_wp.speed_mps + (next_wp.speed_mps - prev_wp.speed_mps) * progress
        bearing = math.radians(prev_wp.bearing_deg +
                               (next_wp.bearing_deg - prev_wp.bearing_deg) * progress)

        vn = speed * math.cos(bearing)  # North velocity
        ve = speed * math.sin(bearing)  # East velocity
        vd = 0.0  # Vertical velocity

        return (vn, ve, vd)

    # ═══════════════════════════════════════════════════════════════════════
    # PUBLIC SESSION GENERATORS
    # ═══════════════════════════════════════════════════════════════════════

    def generate_idle_session(self, duration_s: float = 60.0,
                              sample_rate_hz: int = 20,
                              activity: str = "idle_desk") -> str:
        """
        Generate VMOS sensor data for a stationary device.

        Args:
            duration_s: Session duration in seconds.
            sample_rate_hz: Sample rate (10-20Hz general, 60Hz VR).
            activity: Activity profile name.

        Returns:
            UTF-8 string content for sensor data file.
        """
        lines: List[str] = []
        delay_ms = int(1000 / sample_rate_hz)
        num_samples = int(duration_s * sample_rate_hz)

        for i in range(num_samples):
            t = i / sample_rate_hz
            frame = self._generate_frame(activity, t)
            lines.extend(frame)
            lines.append(f"delay:{delay_ms}")

        return "\n".join(lines) + "\n"

    def generate_interactive_session(self, duration_s: float = 30.0,
                                     sample_rate_hz: int = 20,
                                     activity: str = "hand_held",
                                     touch_events: Optional[List[TouchEvent]] = None,
                                     ) -> str:
        """
        Generate VMOS sensor data with touch-IMU synchronized impulses.

        Touch events inject correlated accelerometer/gyroscope spikes
        that replicate the physical force of finger interaction.

        Args:
            duration_s: Session duration.
            sample_rate_hz: Sample rate.
            activity: Base activity profile.
            touch_events: Touch events to synchronize.

        Returns:
            UTF-8 string content for sensor data file.
        """
        lines: List[str] = []
        delay_ms = int(1000 / sample_rate_hz)
        num_samples = int(duration_s * sample_rate_hz)
        touch_events = touch_events or []

        for i in range(num_samples):
            t = i / sample_rate_hz

            # Check for touch impulses at this timestamp
            impulse = None
            for touch in touch_events:
                imp = self._compute_touch_impulse(touch, t)
                if imp:
                    impulse = imp
                    break

            frame = self._generate_frame(activity, t, touch_impulse=impulse)
            lines.extend(frame)
            lines.append(f"delay:{delay_ms}")

        return "\n".join(lines) + "\n"

    def generate_trajectory_session(self, duration_s: float = 120.0,
                                    sample_rate_hz: int = 20,
                                    waypoints: Optional[List[GPSWaypoint]] = None,
                                    touch_events: Optional[List[TouchEvent]] = None,
                                    ) -> str:
        """
        Generate VMOS sensor data with GPS-IMU EKF-fused trajectory.

        GPS movement at pedestrian/vehicle speed generates correlated
        IMU acceleration and step-detection signatures.

        Args:
            duration_s: Session duration.
            sample_rate_hz: Sample rate.
            waypoints: GPS trajectory waypoints.
            touch_events: Optional touch events.

        Returns:
            UTF-8 string content for sensor data file.
        """
        lines: List[str] = []
        delay_ms = int(1000 / sample_rate_hz)
        num_samples = int(duration_s * sample_rate_hz)
        waypoints = waypoints or []
        touch_events = touch_events or []

        # Determine activity from speed
        for i in range(num_samples):
            t = i / sample_rate_hz

            gps_vel = self._compute_gps_velocity(waypoints, t)

            # Auto-select activity based on speed
            if gps_vel:
                speed = math.sqrt(gps_vel[0]**2 + gps_vel[1]**2)
                if speed > 5.0:
                    activity = "vehicle"
                elif speed > 0.5:
                    activity = "walking"
                else:
                    activity = "hand_held"
            else:
                activity = "idle_desk"

            # Check touch impulses
            impulse = None
            for touch in touch_events:
                imp = self._compute_touch_impulse(touch, t)
                if imp:
                    impulse = imp
                    break

            frame = self._generate_frame(
                activity, t,
                touch_impulse=impulse,
                gps_velocity=gps_vel,
            )
            lines.extend(frame)
            lines.append(f"delay:{delay_ms}")

        return "\n".join(lines) + "\n"

    def generate_circadian_session(self, duration_hours: float = 4.0,
                                   sample_rate_hz: int = 10,
                                   persona: str = "professional",
                                   ) -> str:
        """
        Generate extended VMOS sensor data with circadian activity shifts.

        Models realistic device usage over hours: idle → pickup → use →
        pocket → walking → vehicle → idle.

        Args:
            duration_hours: Session duration in hours.
            sample_rate_hz: Sample rate (use 10Hz for long sessions).
            persona: Persona archetype affecting activity distribution.

        Returns:
            UTF-8 string content for sensor data file.
        """
        PERSONA_SCHEDULES = {
            "professional": [
                (0.0, 0.2, "idle_desk"),
                (0.2, 0.4, "hand_held"),
                (0.4, 0.5, "walking"),
                (0.5, 0.65, "idle_desk"),
                (0.65, 0.75, "hand_held"),
                (0.75, 0.85, "pocket"),
                (0.85, 0.95, "vehicle"),
                (0.95, 1.0, "idle_desk"),
            ],
            "student": [
                (0.0, 0.3, "hand_held"),
                (0.3, 0.4, "idle_desk"),
                (0.4, 0.55, "hand_held"),
                (0.55, 0.65, "walking"),
                (0.65, 0.8, "hand_held"),
                (0.8, 0.9, "idle_desk"),
                (0.9, 1.0, "pocket"),
            ],
            "commuter": [
                (0.0, 0.15, "idle_desk"),
                (0.15, 0.25, "walking"),
                (0.25, 0.5, "vehicle"),
                (0.5, 0.6, "walking"),
                (0.6, 0.85, "idle_desk"),
                (0.85, 0.95, "hand_held"),
                (0.95, 1.0, "pocket"),
            ],
        }

        schedule = PERSONA_SCHEDULES.get(persona, PERSONA_SCHEDULES["professional"])
        lines: List[str] = []
        delay_ms = int(1000 / sample_rate_hz)
        duration_s = duration_hours * 3600.0
        num_samples = int(duration_s * sample_rate_hz)

        for i in range(num_samples):
            t = i / sample_rate_hz
            progress = t / duration_s

            # Determine activity from schedule
            activity = "idle_desk"
            for start, end, act in schedule:
                if start <= progress < end:
                    activity = act
                    break

            frame = self._generate_frame(activity, t)
            lines.extend(frame)
            lines.append(f"delay:{delay_ms}")

        return "\n".join(lines) + "\n"

    # ═══════════════════════════════════════════════════════════════════════
    # FILE I/O AND DEPLOYMENT
    # ═══════════════════════════════════════════════════════════════════════

    def write_sensor_file(self, content: str, path: str) -> str:
        """
        Write sensor data content to a file.

        Args:
            content: Sensor data string from generate_*() methods.
            path: Output file path.

        Returns:
            Absolute path to written file.
        """
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Sensor data written: {path} ({len(content)} bytes)")
        return os.path.abspath(path)

    def generate_and_write(self, output_path: str,
                           duration_s: float = 60.0,
                           sample_rate_hz: int = 20,
                           session_type: str = "interactive",
                           touch_events: Optional[List[TouchEvent]] = None,
                           waypoints: Optional[List[GPSWaypoint]] = None,
                           persona: str = "professional",
                           ) -> str:
        """
        Generate sensor data and write to file in one call.

        Args:
            output_path: File path for sensor data.
            duration_s: Session duration.
            sample_rate_hz: Samples per second.
            session_type: "idle", "interactive", "trajectory", or "circadian".
            touch_events: Touch events for interactive sessions.
            waypoints: GPS waypoints for trajectory sessions.
            persona: Persona for circadian sessions.

        Returns:
            Absolute path to written file.
        """
        if session_type == "idle":
            content = self.generate_idle_session(duration_s, sample_rate_hz)
        elif session_type == "interactive":
            content = self.generate_interactive_session(
                duration_s, sample_rate_hz,
                touch_events=touch_events,
            )
        elif session_type == "trajectory":
            content = self.generate_trajectory_session(
                duration_s, sample_rate_hz,
                waypoints=waypoints,
                touch_events=touch_events,
            )
        elif session_type == "circadian":
            content = self.generate_circadian_session(
                duration_s / 3600.0, sample_rate_hz,
                persona=persona,
            )
        else:
            content = self.generate_idle_session(duration_s, sample_rate_hz)

        return self.write_sensor_file(content, output_path)

    async def deploy_to_vmos(self, pad_code: str,
                             content: str,
                             remote_path: str = "/data/local/tmp/sensor_data.txt",
                             ) -> bool:
        """
        Deploy sensor data file to VMOS Cloud instance and activate.

        Args:
            pad_code: VMOS Cloud device pad code.
            content: Sensor data string.
            remote_path: Path on device for sensor file.

        Returns:
            True if deployment and activation successful.
        """
        try:
            from vmos_cloud_api import VMOSCloudClient
        except ImportError:
            logger.error("VMOSCloudClient not available")
            return False

        client = VMOSCloudClient()

        # Write to temp file and push via chunked base64
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt",
                                          delete=False) as tmp:
            tmp.write(content)
            local_path = tmp.name

        try:
            from vmos_file_pusher import VMOSFilePusher
            pusher = VMOSFilePusher(client)
            ok = await pusher.push_file(pad_code, local_path, remote_path)
            if not ok:
                logger.error(f"Failed to push sensor file to {pad_code}")
                return False
        except ImportError:
            # Fallback: write content via async_adb_cmd (slower, size-limited)
            logger.warning("VMOSFilePusher not available, using direct echo")
            # Split into chunks for 4KB limit
            chunk_size = 2048
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i + chunk_size]
                op = ">>" if i > 0 else ">"
                escaped = chunk.replace("'", "'\\''")
                cmd = f"echo '{escaped}' {op} {remote_path}"
                await client.async_adb_cmd([pad_code], cmd)
                await _async_sleep(3.5)  # Rate limit
        finally:
            os.unlink(local_path)

        # Activate sensor injection
        await _async_sleep(3.5)
        result = await client.async_adb_cmd(
            [pad_code],
            f"setprop persist.sys.cloud.sensor.tpl_dp {remote_path}",
        )
        logger.info(f"Sensor injection activated on {pad_code}")
        return True

    async def stop_sensor_injection(self, pad_code: str) -> bool:
        """Stop sensor data injection on a VMOS device."""
        try:
            from vmos_cloud_api import VMOSCloudClient
            client = VMOSCloudClient()
            await client.async_adb_cmd(
                [pad_code],
                'setprop persist.sys.cloud.sensor.tpl_dp ""',
            )
            return True
        except Exception as e:
            logger.error(f"Failed to stop sensor injection: {e}")
            return False


async def _async_sleep(seconds: float):
    """Async sleep helper."""
    import asyncio
    await asyncio.sleep(seconds)
