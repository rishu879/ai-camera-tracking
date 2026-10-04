"""FastAPI REST API for Analytics Dashboard."""
from typing import Any, Dict
from fastapi import FastAPI, HTTPException
from tools.utilities.network import json_success_response
from .config import AnalyticsReportRequest
from .service import AnalyticsService

app = FastAPI(
    title="FSOC Analytics Dashboard API",
    description="Analytics microservice generating diagnostic plots, HTML dashboards, and PDF evaluation reports.",
    version="1.0.0",
)

service = AnalyticsService()


@app.get("/health")
def health():
    return json_success_response({"service": "analytics", "status": "healthy"})


@app.post("/generate/report")
def generate_report_endpoint(req: AnalyticsReportRequest):
    try:
        results = service.generate_report(req)
        return json_success_response(results, f"Analytics report generated for '{req.session_name}'")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reports/list")
def list_reports():
    reports = [d.name for d in service.output_dir.iterdir() if d.is_dir()]
    return json_success_response(reports, "Available generated reports")
