"""FastAPI REST API for Structured Logging Service."""
from typing import Any, Dict, Optional
from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from tools.utilities.network import json_success_response
from .service import LoggingService

app = FastAPI(
    title="FSOC Logger API",
    description="Enterprise structured JSON logging microservice for tracking, camera, errors, and performance.",
    version="1.0.0",
)

service = LoggingService()


class EventLogRequest(BaseModel):
    event_type: str
    details: Dict[str, Any] = Field(default_factory=dict)
    severity: str = "INFO"


class TrackingLogRequest(BaseModel):
    frame_idx: int
    track_id: Optional[int] = None
    centroid_x: Optional[float] = None
    centroid_y: Optional[float] = None
    tracking_error: float
    locked: bool
    confidence: float = 1.0
    extra: Optional[Dict[str, Any]] = None


class CameraLogRequest(BaseModel):
    frame_idx: int
    pan_deg: float
    tilt_deg: float
    pan_speed: float = 0.0
    tilt_speed: float = 0.0
    jitter: Optional[list] = None
    platform_motion: Optional[list] = None


class PerformanceLogRequest(BaseModel):
    fps: float
    latency_ms: float
    tracking_error_rmse: float
    lock_retention_rate: float
    cpu_usage_pct: float
    memory_mb: float


@app.get("/health")
def health():
    return json_success_response({"service": "logger", "status": "healthy"})


@app.post("/logs/event")
def log_event_endpoint(req: EventLogRequest):
    entry = service.log_event(req.event_type, req.details, req.severity)
    return json_success_response(entry, "Event logged successfully")


@app.post("/logs/tracking")
def log_tracking_endpoint(req: TrackingLogRequest):
    entry = service.log_tracking(
        req.frame_idx,
        req.track_id,
        req.centroid_x,
        req.centroid_y,
        req.tracking_error,
        req.locked,
        req.confidence,
        req.extra,
    )
    return json_success_response(entry, "Tracking state logged")


@app.post("/logs/camera")
def log_camera_endpoint(req: CameraLogRequest):
    entry = service.log_camera(
        req.frame_idx,
        req.pan_deg,
        req.tilt_deg,
        req.pan_speed,
        req.tilt_speed,
        req.jitter,
        req.platform_motion,
    )
    return json_success_response(entry, "Camera state logged")


@app.post("/logs/performance")
def log_performance_endpoint(req: PerformanceLogRequest):
    entry = service.log_performance(
        req.fps,
        req.latency_ms,
        req.tracking_error_rmse,
        req.lock_retention_rate,
        req.cpu_usage_pct,
        req.memory_mb,
    )
    return json_success_response(entry, "Performance metrics logged")


@app.get("/logs/query")
def query_logs(
    category: str = Query("tracking", description="Category: event, error, tracking, camera, performance"),
    limit: int = Query(100, ge=1, le=1000),
    severity: Optional[str] = Query(None),
):
    entries = service.query_logs(category=category, limit=limit, severity=severity)
    return json_success_response(entries, f"Retrieved {len(entries)} entries for '{category}'")


@app.get("/logs/stats")
def log_stats():
    return json_success_response(service.get_stats(), "Log storage statistics")


@app.delete("/logs/clear")
def clear_all_logs():
    service.clear_logs()
    return json_success_response({}, "All log channels cleared")
