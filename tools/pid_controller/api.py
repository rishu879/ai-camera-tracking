"""FastAPI REST API for PID Camera Controller."""
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from tools.utilities.network import json_success_response
from .service import PIDCameraControlService

app = FastAPI(
    title="FSOC PID Camera Controller API",
    description="Closed-loop PTZ gimbal servo controller computing smooth Pan and Tilt speeds.",
    version="1.0.0",
)

service = PIDCameraControlService()


class ComputePIDRequest(BaseModel):
    target_pos: List[float]  # [cx, cy]
    desired_center: Optional[List[float]] = None  # [bx, by] (defaults to 320, 240)
    dt: float = Field(default=0.0333, ge=0.001, le=1.0)


class TuneGainsRequest(BaseModel):
    kp_pan: Optional[float] = None
    ki_pan: Optional[float] = None
    kd_pan: Optional[float] = None
    kp_tilt: Optional[float] = None
    ki_tilt: Optional[float] = None
    kd_tilt: Optional[float] = None


@app.get("/health")
def health():
    return json_success_response({"service": "pid_controller", "status": "healthy"})


@app.post("/compute")
def compute_control(req: ComputePIDRequest):
    if len(req.target_pos) < 2:
        raise HTTPException(status_code=400, detail="target_pos must contain [cx, cy]")

    center = (req.desired_center[0], req.desired_center[1]) if req.desired_center and len(req.desired_center) >= 2 else None
    out = service.compute(
        target_pos=(req.target_pos[0], req.target_pos[1]),
        desired_center=center,
        dt=req.dt,
    )
    return json_success_response(out.model_dump(), "PID control command computed")


@app.post("/tune")
def tune_gains(req: TuneGainsRequest):
    cfg = service.update_gains(
        kp_pan=req.kp_pan,
        ki_pan=req.ki_pan,
        kd_pan=req.kd_pan,
        kp_tilt=req.kp_tilt,
        ki_tilt=req.ki_tilt,
        kd_tilt=req.kd_tilt,
    )
    return json_success_response(cfg.model_dump(), "PID gains updated")


@app.post("/reset")
def reset_pid():
    service.reset()
    return json_success_response({}, "PID controller reset")


@app.get("/config")
def get_pid_config():
    return json_success_response(service.config.model_dump(), "PID configuration")


@app.post("/config")
def update_pid_config(patch: Dict[str, Any]):
    current = service.config.model_dump()
    current.update(patch)
    service.config = service.config.__class__(**current)
    service._init_controllers()
    return json_success_response(service.config.model_dump(), "PID configuration updated")
