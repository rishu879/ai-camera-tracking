"""Unit tests for Analytics Dashboard."""
from pathlib import Path
from fastapi.testclient import TestClient
from tools.analytics.api import app, service
from tools.analytics.config import AnalyticsReportRequest


def test_analytics_health():
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["data"]["service"] == "analytics"


def test_analytics_report_generation(tmp_path):
    temp_service = service.__class__()
    temp_service.output_dir = tmp_path

    req = AnalyticsReportRequest(
        session_name="test_session",
        timestamps=[0.0, 0.033, 0.066, 0.1, 0.133],
        tracking_errors=[12.0, 8.5, 5.2, 3.1, 2.0],
        fps_values=[29.5, 30.1, 30.0, 29.8, 30.2],
        target_path_world=[[1000.0, 1000.0], [1010.0, 1005.0], [1020.0, 1010.0]],
        camera_path_world=[[1000.0, 1000.0], [1005.0, 1002.0], [1015.0, 1008.0]],
        summary_metrics={
            "rmse_px": 5.4,
            "mean_fps": 29.9,
            "lock_retention_rate": 0.8,
            "acquisition_time_sec": 0.08,
            "compliance": {
                "tracking_error_pass": True,
                "fps_pass": True,
                "overall_status": "PASSED (ISRO Compliant)",
            },
        },
    )

    result = temp_service.generate_report(req)
    assert Path(result["pdf_report"]).exists()
    assert Path(result["html_dashboard"]).exists()
    assert Path(result["error_plot"]).exists()
    assert Path(result["fps_plot"]).exists()
    assert Path(result["trajectory_plot"]).exists()
