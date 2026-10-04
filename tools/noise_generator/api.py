"""FastAPI REST API for Noise & Disturbance Generator."""
from typing import Any, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from tools.utilities.image_processing import decode_image_base64, encode_image_base64
from tools.utilities.network import json_success_response
from .service import NoiseGeneratorService

app = FastAPI(
    title="FSOC Noise Generator API",
    description="Sensor disturbance microservice simulating Gaussian, Poisson, Salt & Pepper noise, and blurs.",
    version="1.0.0",
)

service = NoiseGeneratorService()


class ApplyNoiseRequest(BaseModel):
    image_base64: str


@app.get("/health")
def health():
    return json_success_response({"service": "noise_generator", "status": "healthy"})


@app.get("/config")
def get_noise_config():
    return json_success_response(service.get_state(), "Noise configuration")


@app.post("/config")
def update_noise_config(patch: Dict[str, Any]):
    try:
        updated = service.update_config(patch)
        return json_success_response(updated.model_dump(), "Noise parameters updated")
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/apply")
def apply_noise_endpoint(req: ApplyNoiseRequest):
    try:
        img = decode_image_base64(req.image_base64)
        processed = service.process_frame(img)
        b64 = encode_image_base64(processed)
        return json_success_response({"image_base64": b64}, "Noise effects applied")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/reset")
def reset_noise():
    service.reset()
    return json_success_response(service.get_state(), "Noise reset to zero")
