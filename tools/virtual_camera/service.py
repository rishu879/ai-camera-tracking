"""Virtual PTZ Camera Service implementing software gimbal dynamics and frame capture."""
import time
from typing import Any, Dict, Optional, Tuple
import numpy as np
from .config import VirtualCameraConfig
from .utils import compute_jitter, compute_platform_motion, extract_camera_frame


class VirtualCameraService:
    """Simulates a motorized Pan-Tilt-Zoom (PTZ) optical sensor platform with disturbances."""

    def __init__(
        self,
        config: Optional[VirtualCameraConfig] = None,
        canvas_center: Tuple[float, float] = (1024.0, 1024.0),
    ):
        self.config = config or VirtualCameraConfig()
        self.canvas_center = canvas_center

        # Physical gimbal state
        self.pan_deg: float = 0.0
        self.tilt_deg: float = 0.0
        self.pan_speed_cmd: float = 0.0
        self.tilt_speed_cmd: float = 0.0
        self.zoom: float = self.config.zoom

        # Disturbance state
        self.current_jitter: Tuple[float, float] = (0.0, 0.0)
        self.current_platform_motion: Tuple[float, float] = (0.0, 0.0)
        self.sim_time: float = 0.0
        self.frame_count: int = 0
        self.last_frame: Optional[np.ndarray] = None

    def reset(self) -> None:
        """Reset PTZ orientation and speeds to optical center."""
        self.pan_deg = 0.0
        self.tilt_deg = 0.0
        self.pan_speed_cmd = 0.0
        self.tilt_speed_cmd = 0.0
        self.zoom = self.config.zoom
        self.current_jitter = (0.0, 0.0)
        self.current_platform_motion = (0.0, 0.0)
        self.sim_time = 0.0
        self.frame_count = 0

    def set_ptz_speed(self, pan_speed: float, tilt_speed: float) -> None:
        """Command Pan and Tilt speeds in deg/s, clamped to physical max constraints (5-10 deg/s)."""
        max_p = self.config.max_pan_speed_deg
        max_t = self.config.max_tilt_speed_deg
        self.pan_speed_cmd = max(-max_p, min(max_p, float(pan_speed)))
        self.tilt_speed_cmd = max(-max_t, min(max_t, float(tilt_speed)))

    def set_ptz(
        self,
        pan_deg: Optional[float] = None,
        tilt_deg: Optional[float] = None,
        zoom: Optional[float] = None,
    ) -> None:
        """Directly set PTZ angles and zoom (useful for manual steering or initialization)."""
        if pan_deg is not None:
            self.pan_deg = float(pan_deg)
        if tilt_deg is not None:
            self.tilt_deg = float(tilt_deg)
        if zoom is not None:
            self.zoom = max(0.2, min(10.0, float(zoom)))

    def step(self, dt: float, canvas: np.ndarray) -> np.ndarray:
        """
        Advance camera dynamics by dt seconds, integrate gimbal angular motion,
        apply sensor jitter and platform vibration, and crop the sensor FOV frame.
        """
        self.sim_time += dt
        self.frame_count += 1

        # Integrate commanded gimbal angular velocity
        self.pan_deg += self.pan_speed_cmd * dt
        self.tilt_deg += self.tilt_speed_cmd * dt

        # Generate stochastic disturbances
        self.current_jitter = compute_jitter(self.config.max_jitter_px)
        self.current_platform_motion = compute_platform_motion(
            self.sim_time,
            self.config.platform_motion_type,
            self.config.max_platform_motion_px,
        )

        # Extract sensor crop
        frame = extract_camera_frame(
            canvas=canvas,
            camera_center=self.canvas_center,
            pan_deg=self.pan_deg,
            tilt_deg=self.tilt_deg,
            fov_deg=self.config.fov,
            resolution=self.config.resolution,
            zoom=self.zoom,
            jitter=self.current_jitter,
            platform_motion=self.current_platform_motion,
            camera_type=self.config.camera_type,
        )
        self.last_frame = frame
        return frame

    def get_state(self) -> Dict[str, Any]:
        """Return full telemetric state of the virtual camera."""
        return {
            "frame_count": self.frame_count,
            "sim_time": round(self.sim_time, 4),
            "pan_deg": round(self.pan_deg, 4),
            "tilt_deg": round(self.tilt_deg, 4),
            "pan_speed_cmd": round(self.pan_speed_cmd, 4),
            "tilt_speed_cmd": round(self.tilt_speed_cmd, 4),
            "zoom": round(self.zoom, 2),
            "fov": list(self.config.fov),
            "resolution": list(self.config.resolution),
            "jitter_px": [round(j, 2) for j in self.current_jitter],
            "platform_motion_px": [round(p, 2) for p in self.current_platform_motion],
        }
