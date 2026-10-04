"""PID Camera Controller Service implementing closed-loop PTZ visual servoing."""
import math
from typing import Any, Dict, Optional, Tuple
from .config import PIDConfig, PIDControlOutput
from .utils import apply_deadband, clamp, filter_derivative


class SingleAxisPID:
    """Proportional-Integral-Derivative controller for a single gimbal axis."""

    def __init__(
        self,
        kp: float,
        ki: float,
        kd: float,
        max_speed: float,
        anti_windup: float,
        deadband: float,
        alpha: float = 0.75,
    ):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.max_speed = max_speed
        self.anti_windup = anti_windup
        self.deadband = deadband
        self.alpha = alpha

        self.integral = 0.0
        self.prev_error = 0.0
        self.filtered_derivative = 0.0
        self.initialized = False

    def reset(self) -> None:
        """Reset internal accumulator and derivative states."""
        self.integral = 0.0
        self.prev_error = 0.0
        self.filtered_derivative = 0.0
        self.initialized = False

    def compute(self, error: float, dt: float) -> Tuple[float, float, float]:
        """
        Compute commanded gimbal speed for this axis.
        Returns: (output_speed, integral, derivative)
        """
        effective_error = apply_deadband(error, self.deadband)
        if abs(effective_error) < 1e-6:
            # Within deadband: hold speed to 0, decay integral slowly
            self.integral *= 0.95
            return 0.0, self.integral, 0.0

        # 1. Proportional term
        p_term = self.kp * effective_error

        # 2. Integral term with anti-windup clamping
        if dt > 0.0:
            self.integral += effective_error * dt
            self.integral = clamp(self.integral, -self.anti_windup, self.anti_windup)
        i_term = self.ki * self.integral

        # 3. Derivative term with low-pass filtering
        if not self.initialized:
            d_raw = 0.0
            self.initialized = True
        else:
            d_raw = (effective_error - self.prev_error) / max(dt, 1e-4)

        self.filtered_derivative = filter_derivative(d_raw, self.filtered_derivative, self.alpha)
        d_term = self.kd * self.filtered_derivative

        self.prev_error = effective_error

        # Total control output clamped to physical gimbal speed limits (5-10 deg/s)
        total_cmd = p_term + i_term + d_term
        clamped_cmd = clamp(total_cmd, -self.max_speed, self.max_speed)

        return clamped_cmd, self.integral, self.filtered_derivative


class PIDCameraControlService:
    """Dual-axis visual servoing controller driving camera boresight to optical beacon."""

    def __init__(self, config: Optional[PIDConfig] = None):
        self.config = config or PIDConfig()
        self._init_controllers()

    def _init_controllers(self) -> None:
        self.pan_pid = SingleAxisPID(
            kp=self.config.kp_pan,
            ki=self.config.ki_pan,
            kd=self.config.kd_pan,
            max_speed=self.config.max_pan_speed_deg,
            anti_windup=self.config.anti_windup_limit,
            deadband=self.config.deadband_px,
            alpha=self.config.derivative_filter_alpha,
        )
        self.tilt_pid = SingleAxisPID(
            kp=self.config.kp_tilt,
            ki=self.config.ki_tilt,
            kd=self.config.kd_tilt,
            max_speed=self.config.max_tilt_speed_deg,
            anti_windup=self.config.anti_windup_limit,
            deadband=self.config.deadband_px,
            alpha=self.config.derivative_filter_alpha,
        )

    def reset(self) -> None:
        """Reset PID controllers."""
        self.pan_pid.reset()
        self.tilt_pid.reset()

    def update_gains(
        self,
        kp_pan: Optional[float] = None,
        ki_pan: Optional[float] = None,
        kd_pan: Optional[float] = None,
        kp_tilt: Optional[float] = None,
        ki_tilt: Optional[float] = None,
        kd_tilt: Optional[float] = None,
    ) -> PIDConfig:
        """Dynamically tune PID gains."""
        if kp_pan is not None:
            self.config.kp_pan = kp_pan
        if ki_pan is not None:
            self.config.ki_pan = ki_pan
        if kd_pan is not None:
            self.config.kd_pan = kd_pan
        if kp_tilt is not None:
            self.config.kp_tilt = kp_tilt
        if ki_tilt is not None:
            self.config.ki_tilt = ki_tilt
        if kd_tilt is not None:
            self.config.kd_tilt = kd_tilt
        self._init_controllers()
        return self.config

    def compute(
        self,
        target_pos: Tuple[float, float],
        desired_center: Optional[Tuple[float, float]] = None,
        dt: float = 0.0333,
    ) -> PIDControlOutput:
        """
        Compute commanded pan/tilt speeds to center target onto sensor boresight.

        Args:
            target_pos: (cx, cy) target centroid on sensor in pixels
            desired_center: (bx, by) boresight center in pixels (default: 320, 240)
            dt: elapsed time step in seconds
        """
        center = desired_center or self.config.default_center
        error_x = target_pos[0] - center[0]
        error_y = target_pos[1] - center[1]
        total_error = math.hypot(error_x, error_y)

        # Pan axis control: positive error (target to right) requires positive pan speed
        pan_speed, ix, dx = self.pan_pid.compute(error_x, dt)

        # Tilt axis control: positive error (target below center) requires positive tilt speed
        tilt_speed, iy, dy = self.tilt_pid.compute(error_y, dt)

        in_deadband = (abs(error_x) <= self.config.deadband_px) and (abs(error_y) <= self.config.deadband_px)

        return PIDControlOutput(
            pan_speed_deg=round(pan_speed, 4),
            tilt_speed_deg=round(tilt_speed, 4),
            error_x=round(error_x, 3),
            error_y=round(error_y, 3),
            total_error_px=round(total_error, 3),
            in_deadband=in_deadband,
            integral_x=round(ix, 4),
            integral_y=round(iy, 4),
            derivative_x=round(dx, 4),
            derivative_y=round(dy, 4),
        )
