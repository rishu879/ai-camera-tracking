"""Performance Monitor Service tracking ISRO benchmark KPIs in real-time."""
import time
from typing import Any, Dict, List, Optional
import numpy as np
from .config import MonitorConfig, PerformanceMetricSample, PerformanceSummary
from .utils import compute_lock_retention, compute_rmse, get_system_telemetry


class PerformanceMonitorService:
    """Computes, validates, and logs real-time tracking metrics against ISRO criteria."""

    def __init__(self, config: Optional[MonitorConfig] = None):
        self.config = config or MonitorConfig()
        self.samples: List[PerformanceMetricSample] = []

        # Acquisition tracking states
        self.sim_start_time: Optional[float] = None
        self.acquisition_time: Optional[float] = None
        self.consecutive_locked_count = 0
        self.initial_acquisition_done = False

        # Re-acquisition tracking states
        self.occlusion_active = False
        self.occlusion_end_time: Optional[float] = None
        self.reacquisition_time: Optional[float] = None

        self.errors_all: List[float] = []
        self.fps_all: List[float] = []
        self.latencies_all: List[float] = []

    def reset(self) -> None:
        """Clear all metrics and counters."""
        self.samples.clear()
        self.sim_start_time = None
        self.acquisition_time = None
        self.consecutive_locked_count = 0
        self.initial_acquisition_done = False
        self.occlusion_active = False
        self.occlusion_end_time = None
        self.reacquisition_time = None
        self.errors_all.clear()
        self.fps_all.clear()
        self.latencies_all.clear()

    def record_frame(
        self,
        frame_idx: int,
        fps: float,
        latency_ms: float,
        tracking_error_px: float,
        is_locked: bool,
        is_occluded: bool = False,
    ) -> PerformanceMetricSample:
        """Record instantaneous metrics for a single video frame."""
        now = time.time()
        if self.sim_start_time is None:
            self.sim_start_time = now

        # System telemetry
        cpu_pct, mem_mb, _ = get_system_telemetry()

        sample = PerformanceMetricSample(
            timestamp=now,
            frame_idx=frame_idx,
            fps=fps,
            latency_ms=latency_ms,
            tracking_error_px=tracking_error_px,
            is_locked=is_locked,
            is_occluded=is_occluded,
            cpu_percent=cpu_pct,
            memory_mb=mem_mb,
        )
        self.samples.append(sample)

        # Track historical values
        self.errors_all.append(tracking_error_px)
        self.fps_all.append(fps)
        self.latencies_all.append(latency_ms)

        # --- 1. Initial Acquisition Detection ---
        # Time from start until tracking error stays <= 10 px for 5 consecutive frames
        if not self.initial_acquisition_done:
            if tracking_error_px <= self.config.error_threshold_px and not is_occluded:
                self.consecutive_locked_count += 1
                if self.consecutive_locked_count >= 5:
                    self.acquisition_time = round(now - self.sim_start_time, 3)
                    self.initial_acquisition_done = True
            else:
                self.consecutive_locked_count = 0

        # --- 2. Re-acquisition Detection ---
        # When occlusion transitions from True -> False, start clock until re-locked <= 10 px
        if is_occluded:
            self.occlusion_active = True
        elif self.occlusion_active and not is_occluded:
            # Re-emerged from occlusion
            if self.occlusion_end_time is None:
                self.occlusion_end_time = now
            if tracking_error_px <= self.config.error_threshold_px:
                self.reacquisition_time = round(now - self.occlusion_end_time, 3)
                self.occlusion_active = False
                self.occlusion_end_time = None

        return sample

    def get_summary(self) -> PerformanceSummary:
        """Compute aggregate benchmark metrics and verify compliance with ISRO SIH criteria."""
        total = len(self.errors_all)
        if total == 0:
            return PerformanceSummary(
                total_frames=0,
                mean_fps=0.0,
                mean_latency_ms=0.0,
                mean_tracking_error_px=0.0,
                max_tracking_error_px=0.0,
                rmse_px=0.0,
                lock_retention_rate=1.0,
                target_loss_rate=0.0,
                acquisition_time_sec=None,
                reacquisition_time_sec=None,
                cpu_percent=0.0,
                memory_mb=0.0,
                compliance={"status": "NO_DATA"},
            )

        mean_fps = float(np.mean(self.fps_all))
        mean_lat = float(np.mean(self.latencies_all))
        mean_err = float(np.mean(self.errors_all))
        max_err = float(np.max(self.errors_all))
        rmse = compute_rmse(self.errors_all)
        lock_rate = compute_lock_retention(self.errors_all, self.config.error_threshold_px)
        loss_rate = 1.0 - lock_rate

        cpu_pct, mem_mb, _ = get_system_telemetry()

        # ISRO Compliance Evaluation
        compliance = {
            "fps_pass": mean_fps >= self.config.fps_min,
            "tracking_error_pass": rmse <= self.config.error_threshold_px,
            "lock_retention_pass": lock_rate >= self.config.lock_retention_min_rate,
            "target_loss_pass": loss_rate <= (1.0 - self.config.lock_retention_min_rate),
            "acquisition_time_pass": (
                self.acquisition_time <= self.config.acquisition_max_sec
                if self.acquisition_time is not None
                else True
            ),
            "reacquisition_time_pass": (
                self.reacquisition_time <= self.config.reacquisition_max_sec
                if self.reacquisition_time is not None
                else True
            ),
        }
        all_passed = all(compliance.values())
        compliance["overall_status"] = "PASSED (ISRO Compliant)" if all_passed else "ATTENTION NEEDED"

        return PerformanceSummary(
            total_frames=total,
            mean_fps=round(mean_fps, 2),
            mean_latency_ms=round(mean_lat, 2),
            mean_tracking_error_px=round(mean_err, 3),
            max_tracking_error_px=round(max_err, 3),
            rmse_px=round(rmse, 3),
            lock_retention_rate=round(lock_rate, 4),
            target_loss_rate=round(loss_rate, 4),
            acquisition_time_sec=self.acquisition_time,
            reacquisition_time_sec=self.reacquisition_time,
            cpu_percent=cpu_pct,
            memory_mb=mem_mb,
            compliance=compliance,
        )
