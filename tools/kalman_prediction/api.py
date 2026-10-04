"""FastAPI REST API for Kalman Prediction Engine."""
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from tools.utilities.network import json_success_response
from .service import KalmanPredictionService

app = FastAPI(
    title="FSOC Kalman Prediction Engine API",
    description="Kalman state estimator predicting future position, velocity, and acceleration with occlusion coasting.",
    version="1.0.0",
)

service = KalmanPredictionService()


class KalmanStepRequest(BaseModel):
    measurement: Optional[List[float]] = None  # [cx, cy] or None for occlusion


@app.get("/health")
def health():
    return json_success_response({"service": "kalman_prediction", "status": "healthy"})


@app.post("/step")
def step_filter(req: KalmanStepRequest):
    meas = (req.measurement[0], req.measurement[1]) if req.measurement and len(req.measurement) >= 2 else None
    output = service.update(meas)
    return json_success_response(output.model_dump(), "Kalman filter state updated")


@app.get("/forecast")
def get_forecast(steps: int = Query(5, ge=1, le=30)):
    future = service.forecast(steps)
    return json_success_response({"steps": steps, "forecast": future}, f"Forecasted {steps} frames ahead")


@app.get("/state")
def get_filter_state():
    return json_success_response(service.get_output().model_dump(), "Current Kalman state")


@app.post("/reset")
def reset_filter():
    service.reset()
    return json_success_response({}, "Kalman filter reset")


@app.get("/config")
def get_filter_config():
    return json_success_response(service.config.model_dump(), "Kalman filter configuration")


@app.post("/config")
def update_filter_config(patch: Dict[str, Any]):
    current = service.config.model_dump()
    current.update(patch)
    service.config = service.config.__class__(**current)
    service._build_matrices()
    return json_success_response(service.config.model_dump(), "Kalman filter configuration updated")
