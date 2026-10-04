"""FastAPI REST API for Weather Engine."""
from typing import Any, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from tools.utilities.image_processing import decode_image_base64, encode_image_base64
from tools.utilities.network import json_success_response
from .service import WeatherEngineService

app = FastAPI(
    title="FSOC Weather Engine API",
    description="Atmospheric degradation microservice simulating fog, rain, snow, haze, and low-light.",
    version="1.0.0",
)

service = WeatherEngineService()


class ApplyWeatherRequest(BaseModel):
    image_base64: str


@app.get("/health")
def health():
    return json_success_response({"service": "weather_engine", "status": "healthy"})


@app.get("/config")
def get_weather_config():
    return json_success_response(service.get_state(), "Weather configuration")


@app.post("/config")
def update_weather_config(patch: Dict[str, Any]):
    try:
        updated = service.update_config(patch)
        return json_success_response(updated.model_dump(), "Weather parameters updated")
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/apply")
def apply_weather_endpoint(req: ApplyWeatherRequest):
    try:
        img = decode_image_base64(req.image_base64)
        processed = service.process_frame(img)
        b64 = encode_image_base64(processed)
        return json_success_response({"image_base64": b64}, "Weather effects applied")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/reset")
def reset_weather():
    service.reset()
    return json_success_response(service.get_state(), "Weather reset to clear sky")
