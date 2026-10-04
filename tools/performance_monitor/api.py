"""FastAPI REST API for Performance Monitor."""
from typing import Any, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from tools.utilities.network import json_success_response
from .service import PerformanceMonitorService

app = FastAPI(
    title="FSOC Performance Monitor API",
    description="Real-time KPI monitoring and ISRO SIH compliance evaluation microservice.",
    version="1.0.0",
)

service = PerformanceMonitorService()


class RecordFrameRequest(BaseModel):
    frame_idx: int
    fps: float
    latency_ms: float
    tracking_error_px: float
    is_locked: bool
    is_occluded: bool = False


@app.get("/health")
def health():
    return json_success_response({"service": "performance_monitor", "status": "healthy"})


@app.post("/record")
def record_frame_metric(req: RecordFrameRequest):
    sample = service.record_frame(
        frame_idx=req.frame_idx,
        fps=req.fps,
        latency_ms=req.latency_ms,
        tracking_error_px=req.tracking_error_px,
        is_locked=req.is_locked,
        is_occluded=req.is_occluded,
    )
    return json_success_response(sample.model_dump(), "Metric recorded")


@app.get("/summary")
def get_performance_summary():
    summary = service.get_summary()
    return json_success_response(summary.model_dump(), "Performance summary retrieved")


@app.get("/metrics/latest")
def get_latest_metrics():
    if len(service.samples) == 0:
        return json_success_response({}, "No samples recorded")
    return json_success_response(service.samples[-1].model_dump(), "Latest metric sample")


@app.post("/reset")
def reset_monitor():
    service.reset()
    return json_success_response({}, "Performance monitor reset")


@app.get("/config")
def get_monitor_config():
    return json_success_response(service.config.model_dump(), "Monitor configuration")


@app.post("/config")
def update_monitor_config(patch: Dict[str, Any]):
    current = service.config.model_dump()
    current.update(patch)
    service.config = service.config.__class__(**current)
    return json_success_response(service.config.model_dump(), "Monitor configuration updated")
