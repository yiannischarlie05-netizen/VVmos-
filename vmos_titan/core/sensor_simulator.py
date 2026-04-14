"""
Titan V11.3 — Sensor Simulator
OADEV-based noise model for accelerometer, gyroscope, and magnetometer.
Generates realistic IMU readings with bias instability and random walk.

Couples sensor bursts with touch gestures so accelerometer/gyroscope
readings correlate with user interactions (tap → micro-shake,
swipe → wrist rotation).

Usage:
    sim = SensorSimulator(adb_target="127.0.0.1:5555")
    frame = sim.generate_accelerometer_frame()
    sim.couple_with_gesture("tap", magnitude=0.3)
    sim.inject_sensor_burst("accelerometer", duration_ms=200)
"""

import logging
import math
import os
import random
import subprocess
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("titan.sensor-simulator")

# ═══════════════════════════════════════════════════════════════════════
# OADEV NOISE PROFILES (real MEMS sensor specifications)
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class SensorNoiseProfile:
    """Allan deviation-based noise parameters for a MEMS sensor axis."""
    bias_instability: float   # Long-term drift (mg for accel, °/s for gyro)
    random_walk: float        # White noise integration (mg/√Hz or °/s/√Hz)
    quantization: float       # ADC quantization noise floor


# Real device profiles — values from datasheets (Bosch, InvenSense, STMicro)
SENSOR_PROFILES = {
    "samsung": {
        "accelerometer": SensorNoiseProfile(
            bias_instability=0.04,   # LSM6DSO: 40 µg
            random_walk=0.12,        # 120 µg/√Hz
            quantization=0.061,      # 16-bit @ ±4g
        ),
        "gyroscope": SensorNoiseProfile(
            bias_instability=0.8,    # 0.8 °/s
            random_walk=0.004,       # 4 m°/s/√Hz
            quantization=0.0038,     # 16-bit @ ±125°/s
        ),
        "magnetometer": SensorNoiseProfile(
            bias_instability=0.3,    # 300 nT → 0.3 µT
            random_walk=0.15,
            quantization=0.1,
        ),
    },
    "google": {
        "accelerometer": SensorNoiseProfile(
            bias_instability=0.05,
            random_walk=0.15,
            quantization=0.061,
        ),
        "gyroscope": SensorNoiseProfile(
            bias_instability=1.0,
            random_walk=0.005,
            quantization=0.004,
        ),
        "magnetometer": SensorNoiseProfile(
            bias_instability=0.25,
            random_walk=0.12,
            quantization=0.1,
        ),
    },
    "default": {
        "accelerometer": SensorNoiseProfile(
            bias_instability=0.06,
            random_walk=0.18,
            quantization=0.07,
        ),
        "gyroscope": SensorNoiseProfile(
            bias_instability=1.2,
            random_walk=0.006,
            quantization=0.005,
        ),
        "magnetometer": SensorNoiseProfile(
            bias_instability=0.35,
            random_walk=0.18,
            quantization=0.12,
        ),
    },
}

# Earth gravity constant
EARTH_G = 9.80665

# Gesture coupling profiles: (accel_magnitude_g, gyro_magnitude_dps, duration_ms)
GESTURE_COUPLING = {
    "tap":       {"accel_peak": 0.08, "gyro_peak": 0.5,  "duration_ms": 120, "decay": 0.85},
    "double_tap": {"accel_peak": 0.12, "gyro_peak": 0.8,  "duration_ms": 200, "decay": 0.80},
    "swipe":     {"accel_peak": 0.15, "gyro_peak": 2.0,  "duration_ms": 350, "decay": 0.75},
    "scroll":    {"accel_peak": 0.05, "gyro_peak": 0.3,  "duration_ms": 500, "decay": 0.90},
    "long_press": {"accel_peak": 0.02, "gyro_peak": 0.1,  "duration_ms": 800, "decay": 0.95},
    "type":      {"accel_peak": 0.03, "gyro_peak": 0.2,  "duration_ms": 80,  "decay": 0.88},
}


class SensorNoiseModel:
    """Generates realistic sensor noise using OADEV parameters.

    Models three noise components:
    1. Bias instability — slow 1/f drift (Markov process)
    2. Velocity/angle random walk — white noise integration
    3. Quantization noise — ADC floor
    """

    def __init__(self, profile: SensorNoiseProfile):
        self.profile = profile
        self._bias_state = 0.0    # Current bias drift state
        self._rw_state = 0.0      # Random walk accumulator
        self._last_time = time.time()

    def sample(self) -> float:
        """Generate one noise sample incorporating all three components."""
        now = time.time()
        dt = max(now - self._last_time, 0.001)
        self._last_time = now

        # 1. Bias instability: first-order Gauss-Markov process
        # τ ≈ 100s correlation time for typical MEMS
        tau = 100.0
        alpha = math.exp(-dt / tau)
        self._bias_state = (alpha * self._bias_state +
                            (1 - alpha) * random.gauss(0, self.profile.bias_instability))

        # 2. Random walk: integrated white noise
        self._rw_state += random.gauss(0, self.profile.random_walk * math.sqrt(dt))
        # Clamp random walk to prevent unbounded drift
        rw_limit = self.profile.random_walk * 10
        self._rw_state = max(-rw_limit, min(rw_limit, self._rw_state))

        # 3. Quantization noise
        quant_noise = random.uniform(-0.5, 0.5) * self.profile.quantization

        return self._bias_state + self._rw_state + quant_noise

    def reset(self):
        """Reset noise state (e.g. on device reboot simulation)."""
        self._bias_state = 0.0
        self._rw_state = 0.0
        self._last_time = time.time()


class SensorSimulator:
    """Full sensor simulation for a Cuttlefish Android VM.

    Creates three-axis noise models for accelerometer, gyroscope,
    and magnetometer, with gesture coupling for correlated readings.
    """

    def __init__(self, adb_target: str = "127.0.0.1:5555",
                 brand: str = "samsung"):
        self.target = adb_target
        self.brand = brand.lower()
        profiles = SENSOR_PROFILES.get(self.brand, SENSOR_PROFILES["default"])

        # Three-axis noise models
        self._accel = [SensorNoiseModel(profiles["accelerometer"]) for _ in range(3)]
        self._gyro = [SensorNoiseModel(profiles["gyroscope"]) for _ in range(3)]
        self._mag = [SensorNoiseModel(profiles["magnetometer"]) for _ in range(3)]

        # Gesture coupling state
        self._gesture_impulse = [0.0, 0.0, 0.0]  # [x, y, z] impulse
        self._gesture_decay = 0.0
        self._gesture_start = 0.0

    def _sh(self, cmd: str, timeout: int = 10) -> Tuple[bool, str]:
        try:
            r = subprocess.run(
                ["adb", "-s", self.target, "shell", cmd],
                capture_output=True, text=True, timeout=timeout,
            )
            return r.returncode == 0, r.stdout.strip()
        except Exception as e:
            return False, str(e)

    # ─── FRAME GENERATORS ─────────────────────────────────────────────

    def generate_accelerometer_frame(self) -> List[float]:
        """Generate a realistic [x, y, z] accelerometer reading in m/s².

        At rest, a phone lying face-up reads approximately [0, 0, 9.81].
        Small perturbations from hand holding add ~0.02-0.1g noise.
        """
        # Base: phone held upright with slight tilt
        base_x = random.gauss(0.15, 0.05)   # Slight lateral tilt
        base_y = random.gauss(0.3, 0.1)     # Forward tilt from holding
        base_z = EARTH_G                      # Gravity axis

        # Add OADEV noise
        noise = [m.sample() * EARTH_G / 1000.0 for m in self._accel]  # mg → m/s²

        # Add gesture coupling if active
        gesture = self._get_gesture_contribution()

        return [
            base_x + noise[0] + gesture[0],
            base_y + noise[1] + gesture[1],
            base_z + noise[2] + gesture[2],
        ]

    def generate_gyroscope_frame(self) -> List[float]:
        """Generate a realistic [x, y, z] gyroscope reading in rad/s.

        At rest: near-zero with MEMS drift noise.
        During gestures: correlated rotation from wrist movement.
        """
        noise = [m.sample() * math.pi / 180.0 for m in self._gyro]  # °/s → rad/s
        gesture = self._get_gesture_contribution()
        # Gyro gesture coupling is rotational
        gyro_scale = 0.3  # Gesture → rotation coupling factor
        return [
            noise[0] + gesture[1] * gyro_scale,  # Cross-coupled
            noise[1] + gesture[0] * gyro_scale,
            noise[2] + gesture[2] * gyro_scale * 0.1,
        ]

    def generate_magnetometer_frame(self) -> List[float]:
        """Generate a realistic [x, y, z] magnetometer reading in µT.

        Earth's field: ~25-65 µT total magnitude depending on location.
        """
        # Typical indoor values (partially shielded by building)
        base_x = random.gauss(20.0, 2.0)
        base_y = random.gauss(-5.0, 1.5)
        base_z = random.gauss(-40.0, 3.0)

        noise = [m.sample() for m in self._mag]

        return [base_x + noise[0], base_y + noise[1], base_z + noise[2]]

    # ─── GESTURE COUPLING ─────────────────────────────────────────────

    def couple_with_gesture(self, gesture_type: str, magnitude: float = 1.0):
        """Inject a correlated sensor burst for a touch gesture.

        Args:
            gesture_type: One of "tap", "swipe", "scroll", "long_press", "type"
            magnitude: Scale factor (0.5 = gentle, 1.5 = aggressive)
        """
        params = GESTURE_COUPLING.get(gesture_type, GESTURE_COUPLING["tap"])
        peak = params["accel_peak"] * magnitude

        # Random impulse direction (primarily Z for taps, X/Y for swipes)
        if gesture_type in ("tap", "double_tap", "long_press", "type"):
            self._gesture_impulse = [
                random.gauss(0, peak * 0.3),
                random.gauss(0, peak * 0.3),
                random.gauss(-peak, peak * 0.2),  # Mostly -Z (push into screen)
            ]
        else:  # swipe, scroll
            self._gesture_impulse = [
                random.gauss(peak * 0.7, peak * 0.2),
                random.gauss(peak * 0.3, peak * 0.1),
                random.gauss(0, peak * 0.1),
            ]

        self._gesture_decay = params["decay"]
        self._gesture_start = time.time()
        self._gesture_duration = params["duration_ms"] / 1000.0

    def _get_gesture_contribution(self) -> List[float]:
        """Get current gesture impulse contribution (decaying over time)."""
        if self._gesture_start == 0:
            return [0.0, 0.0, 0.0]

        elapsed = time.time() - self._gesture_start
        if elapsed > self._gesture_duration:
            self._gesture_start = 0
            return [0.0, 0.0, 0.0]

        # Exponential decay
        progress = elapsed / self._gesture_duration
        decay = self._gesture_decay ** (progress * 10)
        return [imp * decay for imp in self._gesture_impulse]

    # ─── DEVICE INJECTION ─────────────────────────────────────────────

    def inject_sensor_burst(self, sensor_type: str = "accelerometer",
                            duration_ms: int = 200, sample_rate_hz: int = 50):
        """Inject a burst of sensor readings into device via setprop.

        Writes sensor frames to persist props that a companion Android
        service can read and feed to SensorManager.
        """
        num_samples = max(1, (duration_ms * sample_rate_hz) // 1000)
        interval = 1.0 / sample_rate_hz

        generators = {
            "accelerometer": self.generate_accelerometer_frame,
            "gyroscope": self.generate_gyroscope_frame,
            "magnetometer": self.generate_magnetometer_frame,
        }
        gen = generators.get(sensor_type, self.generate_accelerometer_frame)

        # Batch sensor data into a single prop write for efficiency
        frames = []
        for _ in range(num_samples):
            frame = gen()
            frames.append(f"{frame[0]:.6f},{frame[1]:.6f},{frame[2]:.6f}")
            time.sleep(interval)

        # Write latest frame to prop (Android service polls this)
        if frames:
            latest = frames[-1]
            self._sh(
                f"setprop persist.titan.sensor.{sensor_type}.data '{latest}'; "
                f"setprop persist.titan.sensor.{sensor_type}.ts '{int(time.time() * 1000)}'"
            )
            logger.debug(f"Sensor burst: {sensor_type} {num_samples} samples, last={latest}")

    # ─── GPS-IMU SENSOR FUSION SYNCHRONIZATION ───────────────────────

    def synchronize_gps_imu(self, lat: float, lon: float,
                             prev_lat: float = 0.0, prev_lon: float = 0.0,
                             dt_seconds: float = 1.0):
        """Synchronize IMU sensor data with GPS position changes.

        Modern RASP and anti-spoofing systems use Extended Kalman Filters (EKF)
        to cross-validate GNSS data against IMU readings. If the GPS coordinates
        change while the accelerometer/gyroscope report zero movement, the
        sensor fusion algorithm instantly detects the anomaly.

        This method calculates the required velocity and directional vectors
        from GPS displacement and translates them into corresponding
        acceleration and angular velocity data, satisfying EKF consistency.

        Args:
            lat, lon: Current GPS coordinates
            prev_lat, prev_lon: Previous GPS coordinates (0 = stationary)
            dt_seconds: Time delta between position updates
        """
        if prev_lat == 0.0 and prev_lon == 0.0:
            # Stationary — just inject idle noise (hand micro-tremor)
            self._inject_stationary_imu()
            return

        # Calculate displacement in meters (Haversine approximation for short distances)
        dlat = (lat - prev_lat) * 111320.0  # ~111.32 km per degree latitude
        dlon = (lon - prev_lon) * 111320.0 * math.cos(math.radians(lat))
        distance_m = math.sqrt(dlat**2 + dlon**2)

        if distance_m < 0.5:
            # Sub-meter movement — treat as stationary with micro-drift
            self._inject_stationary_imu()
            return

        # Calculate velocity and bearing
        velocity_ms = distance_m / max(dt_seconds, 0.1)
        bearing_rad = math.atan2(dlon, dlat)

        # Decompose acceleration into device-frame axes
        # Assume phone held upright: X=lateral, Y=forward, Z=gravity
        accel_forward = velocity_ms / max(dt_seconds, 0.1)  # dv/dt
        # Clamp to realistic range (walking ~1.5 m/s², driving ~3 m/s²)
        accel_forward = max(-5.0, min(5.0, accel_forward))

        # Add realistic noise on top of the kinematic signal
        accel_x = accel_forward * math.sin(bearing_rad) + random.gauss(0, 0.05)
        accel_y = accel_forward * math.cos(bearing_rad) + random.gauss(0, 0.05)
        accel_z = EARTH_G + random.gauss(0, 0.02)  # Gravity + noise

        # Gyroscope: angular velocity from bearing change
        # If bearing changes, there's a corresponding yaw rotation
        gyro_yaw = random.gauss(0, 0.01)  # Base noise
        if velocity_ms > 0.5:
            # Walking/driving induces periodic body sway
            sway_freq = 1.8 if velocity_ms < 2.0 else 0.5  # Walking vs driving
            t = time.time()
            gyro_x = 0.02 * math.sin(2 * math.pi * sway_freq * t) + random.gauss(0, 0.005)
            gyro_y = 0.01 * math.sin(2 * math.pi * sway_freq * t + 1.2) + random.gauss(0, 0.005)
        else:
            gyro_x = random.gauss(0, 0.005)
            gyro_y = random.gauss(0, 0.005)

        # Inject synchronized IMU data
        accel_str = f"{accel_x:.6f},{accel_y:.6f},{accel_z:.6f}"
        gyro_str = f"{gyro_x:.6f},{gyro_y:.6f},{gyro_yaw:.6f}"

        self._sh(
            f"setprop persist.titan.sensor.accelerometer.data '{accel_str}'; "
            f"setprop persist.titan.sensor.accelerometer.ts '{int(time.time() * 1000)}'; "
            f"setprop persist.titan.sensor.gyroscope.data '{gyro_str}'; "
            f"setprop persist.titan.sensor.gyroscope.ts '{int(time.time() * 1000)}'"
        )

        logger.debug(f"GPS-IMU sync: dist={distance_m:.1f}m, v={velocity_ms:.2f}m/s, "
                      f"accel=[{accel_x:.3f},{accel_y:.3f},{accel_z:.3f}]")

    def _inject_stationary_imu(self):
        """Inject realistic stationary IMU data (hand micro-tremor + OADEV noise)."""
        accel = self.generate_accelerometer_frame()
        gyro = self.generate_gyroscope_frame()
        accel_str = f"{accel[0]:.6f},{accel[1]:.6f},{accel[2]:.6f}"
        gyro_str = f"{gyro[0]:.6f},{gyro[1]:.6f},{gyro[2]:.6f}"
        self._sh(
            f"setprop persist.titan.sensor.accelerometer.data '{accel_str}'; "
            f"setprop persist.titan.sensor.accelerometer.ts '{int(time.time() * 1000)}'; "
            f"setprop persist.titan.sensor.gyroscope.data '{gyro_str}'; "
            f"setprop persist.titan.sensor.gyroscope.ts '{int(time.time() * 1000)}'"
        )

    # ─── BACKGROUND NOISE ─────────────────────────────────────────────

    def start_background_noise(self, duration_s: float = 0.0):
        """Set initial background sensor readings on the device.

        If duration_s=0, just sets one batch of current readings.
        """
        for sensor, gen in [
            ("accelerometer", self.generate_accelerometer_frame),
            ("gyroscope", self.generate_gyroscope_frame),
            ("magnetometer", self.generate_magnetometer_frame),
        ]:
            frame = gen()
            data_str = f"{frame[0]:.6f},{frame[1]:.6f},{frame[2]:.6f}"
            self._sh(
                f"setprop persist.titan.sensor.{sensor}.data '{data_str}'; "
                f"setprop persist.titan.sensor.{sensor}.ts '{int(time.time() * 1000)}'"
            )
        logger.info("Background sensor noise initialized")

    # ─── CONTINUOUS SENSOR DAEMON ──────────────────────────────────────

    _daemon_threads: Dict[str, 'threading.Thread'] = {}

    def start_continuous_injection(self, interval_s: float = 2.0):
        """Start a background daemon that continuously injects sensor noise.

        Real phones ALWAYS have sensor data flowing — accelerometer reads
        gravity + micro-tremor, gyroscope reads hand/body movement, etc.
        A device with stale or missing sensor readings is instantly
        flagged by RASP SDKs (ThreatMetrix, SHIELD, Iovation).

        This daemon updates sensor props every `interval_s` seconds,
        simulating the idle-state readings of a phone being held.

        Args:
            interval_s: Update interval (2.0s = 0.5 Hz, enough to pass
                        most sensor-freshness checks without ADB spam)
        """
        import threading

        key = self.target
        # Stop existing daemon for this device if any
        if key in SensorSimulator._daemon_threads:
            SensorSimulator._daemon_threads[key] = None  # Signal stop

        stop_flag = {"running": True}

        def _daemon():
            logger.info(f"Sensor daemon started for {self.target} @ {interval_s}s interval")
            while stop_flag["running"]:
                try:
                    # Batch all three sensors into a single ADB shell call
                    accel = self.generate_accelerometer_frame()
                    gyro = self.generate_gyroscope_frame()
                    mag = self.generate_magnetometer_frame()
                    ts = str(int(time.time() * 1000))
                    cmd = (
                        f"setprop persist.titan.sensor.accelerometer.data "
                        f"'{accel[0]:.6f},{accel[1]:.6f},{accel[2]:.6f}';"
                        f"setprop persist.titan.sensor.accelerometer.ts '{ts}';"
                        f"setprop persist.titan.sensor.gyroscope.data "
                        f"'{gyro[0]:.6f},{gyro[1]:.6f},{gyro[2]:.6f}';"
                        f"setprop persist.titan.sensor.gyroscope.ts '{ts}';"
                        f"setprop persist.titan.sensor.magnetometer.data "
                        f"'{mag[0]:.6f},{mag[1]:.6f},{mag[2]:.6f}';"
                        f"setprop persist.titan.sensor.magnetometer.ts '{ts}'"
                    )
                    self._sh(cmd, timeout=5)
                except Exception as e:
                    logger.debug(f"Sensor daemon error: {e}")
                time.sleep(interval_s)
            logger.info(f"Sensor daemon stopped for {self.target}")

        t = threading.Thread(target=_daemon, daemon=True,
                             name=f"sensor-daemon-{key}")
        t.start()
        SensorSimulator._daemon_threads[key] = stop_flag

    def stop_continuous_injection(self):
        """Stop the background sensor daemon for this device."""
        key = self.target
        flag = SensorSimulator._daemon_threads.pop(key, None)
        if flag and isinstance(flag, dict):
            flag["running"] = False

    # ═══════════════════════════════════════════════════════════════════════
    # VMOS CLOUD SENSOR FILE INJECTION (persist.sys.cloud.sensor.tpl_dp)
    # ═══════════════════════════════════════════════════════════════════════

    def generate_sensor_data_file(self, duration_s: float = 60.0,
                                  sample_rate_hz: int = 20,
                                  include_sensors: list | None = None) -> str:
        """Generate VMOS Cloud sensor data file content.
        
        Creates UTF-8 text file content for persist.sys.cloud.sensor.tpl_dp
        with sequential sensor readings and delay commands.
        
        Format per line:
            sensor_type:x:y:z
            delay:ms
        
        Supported sensors:
            - accelerometer, acceleration-uncalibrated, linear-acceleration
            - gyroscope, gyroscope-uncalibrated
            - gravity, rotation-vector, game-rotation-vector
            - magnetic-field, magnetic-field-uncalibrated
            - proximity, light, pressure, temperature, humidity
            - step-counter, step-detector, heart-rate
            - hinge-angle0, hinge-angle1 (foldables)
        
        Args:
            duration_s: Total duration of sensor data.
            sample_rate_hz: Samples per second (60Hz for VR, 10-20Hz for general).
            include_sensors: List of sensors to include (default: all motion).
            
        Returns:
            UTF-8 string content for sensor data file.
        """
        if include_sensors is None:
            include_sensors = [
                "accelerometer", "gyroscope", "magnetic-field",
                "gravity", "rotation-vector", "proximity", "light",
            ]
        
        lines = []
        num_samples = int(duration_s * sample_rate_hz)
        delay_ms = int(1000 / sample_rate_hz)
        
        for i in range(num_samples):
            # Generate readings for each sensor
            for sensor in include_sensors:
                if sensor in ("accelerometer", "acceleration-uncalibrated", "linear-acceleration"):
                    frame = self.generate_accelerometer_frame()
                    if sensor == "linear-acceleration":
                        # Remove gravity component
                        frame[2] -= EARTH_G
                    lines.append(f"{sensor}:{frame[0]:.6f}:{frame[1]:.6f}:{frame[2]:.6f}")
                    
                elif sensor in ("gyroscope", "gyroscope-uncalibrated"):
                    frame = self.generate_gyroscope_frame()
                    lines.append(f"{sensor}:{frame[0]:.6f}:{frame[1]:.6f}:{frame[2]:.6f}")
                    
                elif sensor in ("magnetic-field", "magnetic-field-uncalibrated"):
                    frame = self.generate_magnetometer_frame()
                    lines.append(f"{sensor}:{frame[0]:.6f}:{frame[1]:.6f}:{frame[2]:.6f}")
                    
                elif sensor == "gravity":
                    # Gravity vector (device orientation dependent)
                    gx = random.gauss(0.1, 0.02)
                    gy = random.gauss(0.2, 0.03)
                    gz = random.gauss(EARTH_G - 0.1, 0.02)
                    lines.append(f"gravity:{gx:.6f}:{gy:.6f}:{gz:.6f}")
                    
                elif sensor in ("rotation-vector", "game-rotation-vector", "geomagnetic_rotation"):
                    # Quaternion: [x, y, z, w] or [x, y, z, cos(θ/2)]
                    # Slight phone tilt from upright
                    qx = random.gauss(0.02, 0.005)
                    qy = random.gauss(0.05, 0.01)
                    qz = random.gauss(0.01, 0.003)
                    qw = math.sqrt(max(0, 1 - qx**2 - qy**2 - qz**2))
                    lines.append(f"{sensor}:{qx:.6f}:{qy:.6f}:{qz:.6f}:{qw:.6f}")
                    
                elif sensor == "proximity":
                    # 0 = near (phone to ear), 5+ = far
                    dist = random.choice([5.0, 5.0, 5.0, 0.0])  # Usually far
                    lines.append(f"proximity:{dist:.1f}")
                    
                elif sensor == "light":
                    # Ambient light in lux (indoor ~100-500, outdoor ~10000+)
                    lux = random.gauss(350, 50)
                    lines.append(f"light:{lux:.1f}")
                    
                elif sensor == "pressure":
                    # Atmospheric pressure in hPa (sea level ~1013)
                    hpa = random.gauss(1013.25, 2.0)
                    lines.append(f"pressure:{hpa:.2f}")
                    
                elif sensor == "temperature":
                    # Ambient temperature in °C
                    temp = random.gauss(23.0, 1.0)
                    lines.append(f"temperature:{temp:.1f}")
                    
                elif sensor == "humidity":
                    # Relative humidity in %
                    rh = random.gauss(45.0, 5.0)
                    lines.append(f"humidity:{rh:.1f}")
                    
                elif sensor == "step-counter":
                    # Cumulative step count
                    base_steps = 5000 + int(i * 0.02)  # Slow walking
                    lines.append(f"step-counter:{base_steps}")
                    
                elif sensor == "step-detector":
                    # 1.0 when step detected (sparse)
                    if random.random() < 0.02:  # ~2% chance per sample
                        lines.append("step-detector:1.0")
                        
                elif sensor == "heart-rate":
                    # BPM
                    bpm = random.gauss(72, 5)
                    lines.append(f"heart-rate:{bpm:.0f}")
                    
                elif sensor.startswith("hinge-angle"):
                    # Foldable hinge angle (0-180°)
                    angle = random.gauss(180, 1)  # Fully open
                    lines.append(f"{sensor}:{angle:.1f}")
            
            # Add delay between samples
            lines.append(f"delay:{delay_ms}")
        
        return "\n".join(lines)

    def inject_sensor_file(self, duration_s: float = 60.0,
                           sample_rate_hz: int = 20,
                           include_sensors: list | None = None) -> bool:
        """Generate and inject sensor data file to VMOS Cloud instance.
        
        Creates sensor data file and sets persist.sys.cloud.sensor.tpl_dp
        to enable sensor simulation.
        
        Args:
            duration_s: Duration of sensor data.
            sample_rate_hz: Samples per second.
            include_sensors: Sensors to include.
            
        Returns:
            True if injection successful.
        """
        # Generate sensor data content
        content = self.generate_sensor_data_file(
            duration_s=duration_s,
            sample_rate_hz=sample_rate_hz,
            include_sensors=include_sensors,
        )
        
        # Write to temporary file on device
        remote_path = "/data/local/tmp/titan_sensor_data.txt"
        
        # Create file via echo (for small files) or push (for large)
        if len(content) < 50000:  # ~50KB threshold
            # Use base64 to avoid shell escaping issues
            import base64
            b64 = base64.b64encode(content.encode()).decode()
            ok, _ = self._sh(f"echo '{b64}' | base64 -d > {remote_path}")
        else:
            # Write locally and push
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(content)
                local_path = f.name
            
            try:
                result = subprocess.run(
                    ["adb", "-s", self.target, "push", local_path, remote_path],
                    capture_output=True, timeout=30,
                )
                ok = result.returncode == 0
            finally:
                os.unlink(local_path)
        
        if not ok:
            logger.error(f"Failed to write sensor data file to {remote_path}")
            return False
        
        # Enable sensor simulation via setprop
        ok, _ = self._sh(f"setprop persist.sys.cloud.sensor.tpl_dp {remote_path}")
        if ok:
            logger.info(f"Sensor simulation enabled: {remote_path} ({len(content)} bytes)")
        return ok

    def stop_sensor_file_injection(self) -> bool:
        """Stop VMOS Cloud sensor file injection.
        
        Clears persist.sys.cloud.sensor.tpl_dp to disable sensor simulation.
        """
        ok, _ = self._sh("setprop persist.sys.cloud.sensor.tpl_dp ''")
        if ok:
            logger.info("Sensor file injection stopped")
        return ok

    def generate_walking_pattern(self, duration_s: float = 300.0,
                                  steps_per_min: int = 100) -> str:
        """Generate realistic walking sensor pattern.
        
        Creates sensor data simulating a person walking with their phone:
        - Periodic accelerometer peaks from foot strikes
        - Correlated gyroscope rotation from body sway
        - Step counter increments
        
        Args:
            duration_s: Duration in seconds.
            steps_per_min: Walking cadence (60-80 slow, 100-120 normal, 130+ running).
            
        Returns:
            Sensor data file content.
        """
        lines = []
        step_period = 60.0 / steps_per_min
        sample_rate = 50  # 50 Hz for motion
        num_samples = int(duration_s * sample_rate)
        delay_ms = int(1000 / sample_rate)
        
        step_count = random.randint(3000, 8000)  # Starting step count
        
        for i in range(num_samples):
            t = i / sample_rate
            
            # Walking gait cycle: 0-1 per step
            phase = (t % step_period) / step_period
            
            # Accelerometer: Z-axis impact at heel strike (~0.15 and ~0.65 in gait cycle)
            heel_strike = (
                0.8 * math.exp(-((phase - 0.15) ** 2) / 0.002) +
                0.6 * math.exp(-((phase - 0.65) ** 2) / 0.002)
            )
            
            # X-axis: lateral sway
            lateral_sway = 0.3 * math.sin(2 * math.pi * phase)
            
            # Y-axis: forward/back motion
            forward_motion = 0.2 * math.sin(4 * math.pi * phase)
            
            ax = lateral_sway + random.gauss(0, 0.05)
            ay = forward_motion + random.gauss(0, 0.05)
            az = EARTH_G + heel_strike + random.gauss(0, 0.03)
            
            lines.append(f"accelerometer:{ax:.6f}:{ay:.6f}:{az:.6f}")
            
            # Gyroscope: body rotation correlates with sway
            gx = 0.05 * math.sin(2 * math.pi * phase + 0.5) + random.gauss(0, 0.01)
            gy = 0.03 * math.sin(4 * math.pi * phase) + random.gauss(0, 0.01)
            gz = 0.02 * math.sin(2 * math.pi * phase) + random.gauss(0, 0.005)
            
            lines.append(f"gyroscope:{gx:.6f}:{gy:.6f}:{gz:.6f}")
            
            # Step counter: increment on heel strike
            if 0.14 < phase < 0.16:
                step_count += 1
                lines.append(f"step-counter:{step_count}")
                lines.append("step-detector:1.0")
            
            lines.append(f"delay:{delay_ms}")
        
        return "\n".join(lines)

    def generate_driving_pattern(self, duration_s: float = 600.0,
                                  speed_kmh: float = 50.0) -> str:
        """Generate realistic driving sensor pattern.
        
        Creates sensor data simulating phone in a moving vehicle:
        - Low-frequency vibration from road
        - Occasional acceleration/braking
        - Turns cause gyroscope rotation
        
        Args:
            duration_s: Duration in seconds.
            speed_kmh: Average speed in km/h.
            
        Returns:
            Sensor data file content.
        """
        lines = []
        sample_rate = 20  # 20 Hz sufficient for driving
        num_samples = int(duration_s * sample_rate)
        delay_ms = int(1000 / sample_rate)
        
        # Simulate random events
        acceleration_events = [random.uniform(0, duration_s) for _ in range(int(duration_s / 30))]
        turn_events = [random.uniform(0, duration_s) for _ in range(int(duration_s / 60))]
        
        for i in range(num_samples):
            t = i / sample_rate
            
            # Base vibration from road (low amplitude, high frequency)
            road_vib = 0.05 * math.sin(2 * math.pi * 15 * t + random.random())
            
            # Check for acceleration event (braking/accelerating)
            accel_boost = 0
            for event_t in acceleration_events:
                if abs(t - event_t) < 3:  # 3-second acceleration
                    progress = (t - event_t + 3) / 6
                    if 0 < progress < 1:
                        accel_boost = 2.0 * math.sin(math.pi * progress) * random.choice([-1, 1])
            
            # Check for turn event
            turn_rate = 0
            for event_t in turn_events:
                if abs(t - event_t) < 5:  # 5-second turn
                    progress = (t - event_t + 5) / 10
                    if 0 < progress < 1:
                        turn_rate = 0.3 * math.sin(math.pi * progress) * random.choice([-1, 1])
            
            ax = road_vib + random.gauss(0, 0.02)
            ay = accel_boost + road_vib * 0.5 + random.gauss(0, 0.02)
            az = EARTH_G + abs(road_vib) * 0.5 + random.gauss(0, 0.01)
            
            lines.append(f"accelerometer:{ax:.6f}:{ay:.6f}:{az:.6f}")
            
            gx = road_vib * 0.1 + random.gauss(0, 0.005)
            gy = road_vib * 0.05 + random.gauss(0, 0.005)
            gz = turn_rate + random.gauss(0, 0.01)
            
            lines.append(f"gyroscope:{gx:.6f}:{gy:.6f}:{gz:.6f}")
            lines.append(f"delay:{delay_ms}")
        
        return "\n".join(lines)

