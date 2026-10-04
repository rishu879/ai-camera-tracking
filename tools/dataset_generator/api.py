"""FastAPI REST API for Dataset Generator."""
from typing import Any, Dict
from fastapi import FastAPI, HTTPException
from tools.utilities.network import json_success_response
from .config import DatasetGenerationRequest
from .service import DatasetGeneratorService

app = FastAPI(
    title="FSOC Dataset Generator API",
    description="Automated synthetic dataset generation microservice exporting YOLO, COCO, and MOT annotations.",
    version="1.0.0",
)

service = DatasetGeneratorService()


@app.get("/health")
def health():
    return json_success_response({"service": "dataset_generator", "status": "healthy"})


@app.post("/generate/batch")
def generate_dataset_batch(req: DatasetGenerationRequest):
    try:
        summary = service.generate(req)
        return json_success_response(summary, f"Dataset '{req.dataset_name}' generated successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/datasets/list")
def list_datasets():
    return json_success_response(service.list_datasets(), "Available generated datasets")
