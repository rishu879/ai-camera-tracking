"""Logging service orchestrating structured JSON logging channels."""
from pathlib import Path
from typing import Any, Dict, List, Optional
from .config import LoggingConfig
from .utils import append_jsonl, get_iso_timestamp, read_jsonl


class LoggingService:
    """Manages categorized structured JSON logs for events, tracking, camera, and performance."""

    def __init__(self, config: Optional[LoggingConfig] = None):
        self.config = config or LoggingConfig()
        self.log_dir = Path(self.config.log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.events_log = self.log_dir / "events.jsonl"
        self.errors_log = self.log_dir / "errors.jsonl"
        self.tracking_log = self.log_dir / "tracking.jsonl"
        self.camera_log = self.log_dir / "camera.jsonl"
        self.performance_log = self.log_dir / "performance.jsonl"

    def log_event(
        self, event_type: str, details: Dict[str, Any], severity: str = "INFO"
    ) -> Dict[str, Any]:
        """Record system lifecycle or control event."""
        entry = {
            "timestamp": get_iso_timestamp(),
            "category": "event",
            "event_type": event_type,
            "severity": severity.upper(),
            "details": details,
        }
        append_jsonl(self.events_log, entry, self.config.max_bytes)
        if self.config.console_output:
            print(f"[{entry['timestamp']}] [{severity}] {event_type}: {details}")
        return entry

    def log_error(
        self,
        error_message: str,
        exception_type: Optional[str] = None,
        traceback_str: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Record system error or exception with stack trace."""
        entry = {
            "timestamp": get_iso_timestamp(),
            "category": "error",
            "severity": "ERROR",
            "error_message": error_message,
            "exception_type": exception_type,
            "traceback": traceback_str,
            "context": context or {},
        }
        append_jsonl(self.errors_log, entry, self.config.max_bytes)
        append_jsonl(self.events_log, entry, self.config.max_bytes)
        if self.config.console_output:
            print(f"[{entry['timestamp']}] [ERROR] {error_message}")
        return entry

    def log_tracking(
        self,
        frame_idx: int,
        track_id: Optional[int],
        centroid_x: Optional[float],
        centroid_y: Optional[float],
        tracking_error: float,
        locked: bool,
        confidence: float = 1.0,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Record target detection and tracking state for a frame."""
        entry = {
            "timestamp": get_iso_timestamp(),
            "category": "tracking",
            "frame_idx": frame_idx,
            "track_id": track_id,
            "centroid_x": round(centroid_x, 3) if centroid_x is not None else None,
            "centroid_y": round(centroid_y, 3) if centroid_y is not None else None,
            "tracking_error": round(tracking_error, 3),
            "locked": locked,
            "confidence": round(confidence, 3),
            "extra": extra or {},
        }
        append_jsonl(self.tracking_log, entry, self.config.max_bytes)
        return entry

    def log_camera(
        self,
        frame_idx: int,
        pan_deg: float,
        tilt_deg: float,
        pan_speed: float,
        tilt_speed: float,
        jitter: Optional[List[float]] = None,
        platform_motion: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """Record camera PTZ position, commanded speeds, and platform disturbances."""
        entry = {
            "timestamp": get_iso_timestamp(),
            "category": "camera",
            "frame_idx": frame_idx,
            "pan_deg": round(pan_deg, 3),
            "tilt_deg": round(tilt_deg, 3),
            "pan_speed": round(pan_speed, 3),
            "tilt_speed": round(tilt_speed, 3),
            "jitter": jitter or [0.0, 0.0],
            "platform_motion": platform_motion or [0.0, 0.0],
        }
        append_jsonl(self.camera_log, entry, self.config.max_bytes)
        return entry

    def log_performance(
        self,
        fps: float,
        latency_ms: float,
        tracking_error_rmse: float,
        lock_retention_rate: float,
        cpu_usage_pct: float,
        memory_mb: float,
    ) -> Dict[str, Any]:
        """Record high-level system benchmark and performance telemetry."""
        entry = {
            "timestamp": get_iso_timestamp(),
            "category": "performance",
            "fps": round(fps, 2),
            "latency_ms": round(latency_ms, 2),
            "tracking_error_rmse": round(tracking_error_rmse, 3),
            "lock_retention_rate": round(lock_retention_rate, 4),
            "cpu_usage_pct": round(cpu_usage_pct, 1),
            "memory_mb": round(memory_mb, 1),
        }
        append_jsonl(self.performance_log, entry, self.config.max_bytes)
        return entry

    def query_logs(
        self, category: str, limit: int = 100, severity: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Query logged entries by category."""
        mapping = {
            "event": self.events_log,
            "error": self.errors_log,
            "tracking": self.tracking_log,
            "camera": self.camera_log,
            "performance": self.performance_log,
        }
        target_file = mapping.get(category.lower(), self.events_log)
        return read_jsonl(target_file, limit=limit, severity=severity)

    def get_stats(self) -> Dict[str, Any]:
        """Return file sizes and total recorded entries per channel."""
        stats = {}
        for cat, file_p in [
            ("events", self.events_log),
            ("errors", self.errors_log),
            ("tracking", self.tracking_log),
            ("camera", self.camera_log),
            ("performance", self.performance_log),
        ]:
            if file_p.exists():
                size_bytes = file_p.stat().st_size
                stats[cat] = {"file": file_p.name, "size_bytes": size_bytes}
            else:
                stats[cat] = {"file": file_p.name, "size_bytes": 0}
        return stats

    def clear_logs(self) -> None:
        """Clear all active log files."""
        for f in [self.events_log, self.errors_log, self.tracking_log, self.camera_log, self.performance_log]:
            if f.exists():
                f.unlink()
