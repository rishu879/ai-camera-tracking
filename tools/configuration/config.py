"""Pydantic configuration models for the complete FSOC Tracking System."""
from typing import Optional, Tuple
from pydantic import BaseModel, Field


class ScreenConfig(BaseModel):
    width: int = Field(default=2048, ge=1000, description="Virtual canvas width (min 2000 per ISRO specs)")
    height: int = Field(default=2048, ge=1000, description="Virtual canvas height (min 2000 per ISRO specs)")


class TargetConfig(BaseModel):
    num_targets: int = Field(default=1, ge=1, description="Number of targets (1 mandatory, multiple optional)")
    shape: str = Field(default="square", description="Target shape: 'square' or 'circle'")
    size: Tuple[int, int] = Field(default=(10, 10), description="Target width and height in pixels (5-20 px)")
    initial_position: Optional[Tuple[float, float]] = Field(default=None, description="Initial (x,y) or None for random")
    motion_type: str = Field(
        default="figure_8",
        description="Motion type: 'straight', 'circular', 'figure_8', 'random', 'spiral', 'sinusoidal'",
    )
    speed: float = Field(default=25.0, ge=1.0, le=200.0, description="Kinematic speed in pixels/second")
    intensity: float = Field(default=255.0, ge=50.0, le=255.0, description="Target radiant intensity (0-255)")


class CameraConfig(BaseModel):
    camera_type: str = Field(default="monochrome", description="'monochrome' or 'color'")
    resolution: Tuple[int, int] = Field(default=(640, 480), description="(width, height) in pixels")
    fov: Tuple[float, float] = Field(default=(4.0, 3.0), description="Horizontal and Vertical FOV in degrees")
    fps: float = Field(default=30.0, ge=20.0, description="Camera sensor update rate (min 30 Hz)")
    max_pan_speed: float = Field(default=5.0, ge=1.0, le=15.0, description="Max pan speed in deg/s (5-10 deg/s)")
    max_tilt_speed: float = Field(default=5.0, ge=1.0, le=15.0, description="Max tilt speed in deg/s (5-10 deg/s)")
    jitter_max_px: float = Field(default=5.0, ge=0.0, le=20.0, description="Max high-frequency jitter in pixels")
    platform_motion_type: str = Field(
        default="linear",
        description="Platform motion: 'none', 'linear', 'circular', 'random', 'spiral'",
    )
    platform_motion_max_px: float = Field(default=5.0, ge=0.0, le=20.0, description="Max platform motion drift in pixels")


class WeatherConfig(BaseModel):
    fog_density: float = Field(default=0.0, ge=0.0, le=1.0, description="Fog attenuation density (0-1)")
    rain_intensity: float = Field(default=0.0, ge=0.0, le=1.0, description="Rain intensity (0-1)")
    snow_intensity: float = Field(default=0.0, ge=0.0, le=1.0, description="Snow particle intensity (0-1)")
    haze_density: float = Field(default=0.0, ge=0.0, le=1.0, description="Atmospheric haze density (0-1)")
    low_light: bool = Field(default=False, description="Simulate night / low-light illumination")
    brightness: float = Field(default=1.0, ge=0.1, le=2.0, description="Brightness scaling factor")
    contrast: float = Field(default=1.0, ge=0.1, le=2.0, description="Contrast scaling factor")


class NoiseConfig(BaseModel):
    gaussian_std: float = Field(default=0.0, ge=0.0, le=20.0, description="Gaussian noise standard deviation (0-20 px)")
    salt_pepper_ratio: float = Field(default=0.0, ge=0.0, le=0.10, description="Salt & Pepper noise ratio (up to 10%)")
    poisson_enabled: bool = Field(default=False, description="Enable Poisson photon shot noise")
    motion_blur_kernel: int = Field(default=0, ge=0, le=15, description="Motion blur kernel size (0 = disabled)")
    camera_blur_sigma: float = Field(default=0.0, ge=0.0, le=10.0, description="Defocus optical blur sigma")


class DetectorConfig(BaseModel):
    model_type: str = Field(default="adaptive", description="'adaptive', 'yolov11', or 'hybrid'")
    confidence_threshold: float = Field(default=0.35, ge=0.05, le=1.0, description="Detection confidence threshold")
    model_path: str = Field(default="models/yolov11_beacon.onnx", description="Path to deep learning weights")


class TrackerConfig(BaseModel):
    tracker_type: str = Field(default="bytetrack", description="'bytetrack' or 'deepsort'")
    track_thresh: float = Field(default=0.4, ge=0.1, le=0.9, description="High detection association threshold")
    match_thresh: float = Field(default=0.7, ge=0.1, le=0.95, description="IoU / spatial matching threshold")
    max_lost_frames: int = Field(default=30, ge=5, le=120, description="Frames before deleting a lost track")


class KalmanConfig(BaseModel):
    model_type: str = Field(default="constant_acceleration", description="'constant_velocity' or 'constant_acceleration'")
    process_noise_std: float = Field(default=0.5, ge=0.01, le=10.0, description="Process noise covariance factor")
    measurement_noise_std: float = Field(default=1.0, ge=0.01, le=10.0, description="Measurement noise covariance factor")
    prediction_steps: int = Field(default=2, ge=0, le=10, description="Future frames to forecast for latency compensation")


class PIDConfig(BaseModel):
    kp_pan: float = Field(default=0.035, ge=0.0, le=1.0, description="Proportional gain for Pan axis")
    ki_pan: float = Field(default=0.002, ge=0.0, le=0.1, description="Integral gain for Pan axis")
    kd_pan: float = Field(default=0.012, ge=0.0, le=0.5, description="Derivative gain for Pan axis")
    kp_tilt: float = Field(default=0.035, ge=0.0, le=1.0, description="Proportional gain for Tilt axis")
    ki_tilt: float = Field(default=0.002, ge=0.0, le=0.1, description="Integral gain for Tilt axis")
    kd_tilt: float = Field(default=0.012, ge=0.0, le=0.5, description="Derivative gain for Tilt axis")
    max_pan_speed_deg: float = Field(default=5.0, ge=1.0, le=10.0, description="Slew rate clamp: max pan speed in deg/s")
    max_tilt_speed_deg: float = Field(default=5.0, ge=1.0, le=10.0, description="Slew rate clamp: max tilt speed in deg/s")
    anti_windup_limit: float = Field(default=2.0, ge=0.1, le=10.0, description="Integral anti-windup clamp limit")
    deadband_px: float = Field(default=0.5, ge=0.0, le=5.0, description="Error deadband in pixels to prevent jitter")


class SystemConfig(BaseModel):
    profile_name: str = Field(default="default", description="Configuration profile name")
    screen: ScreenConfig = Field(default_factory=ScreenConfig)
    target: TargetConfig = Field(default_factory=TargetConfig)
    camera: CameraConfig = Field(default_factory=CameraConfig)
    weather: WeatherConfig = Field(default_factory=WeatherConfig)
    noise: NoiseConfig = Field(default_factory=NoiseConfig)
    detector: DetectorConfig = Field(default_factory=DetectorConfig)
    tracker: TrackerConfig = Field(default_factory=TrackerConfig)
    kalman: KalmanConfig = Field(default_factory=KalmanConfig)
    pid: PIDConfig = Field(default_factory=PIDConfig)
