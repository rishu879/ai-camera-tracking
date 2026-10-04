"""Analytics & Reporting Dashboard Service."""
import json
from pathlib import Path
from typing import Any, Dict, Optional
from .config import AnalyticsConfig, AnalyticsReportRequest
from .utils import (
    generate_pdf_report,
    plot_fps,
    plot_tracking_error,
    plot_trajectory_comparison,
)


class AnalyticsService:
    """Generates analytical charts, PDF benchmark evaluation reports, and HTML summaries."""

    def __init__(self, config: Optional[AnalyticsConfig] = None):
        self.config = config or AnalyticsConfig()
        self.output_dir = Path(self.config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(self, req: AnalyticsReportRequest) -> Dict[str, Any]:
        """Generate all diagnostic plots and full PDF evaluation report."""
        session_dir = self.output_dir / req.session_name
        session_dir.mkdir(parents=True, exist_ok=True)

        error_plot = session_dir / "tracking_error.png"
        fps_plot = session_dir / "fps_throughput.png"
        traj_plot = session_dir / "trajectory_comparison.png"
        pdf_file = session_dir / f"{req.session_name}_report.pdf"
        html_file = session_dir / f"{req.session_name}_dashboard.html"

        # 1. Error plot
        err_path_str = None
        if len(req.tracking_errors) > 0:
            err_path_str = plot_tracking_error(
                req.timestamps, req.tracking_errors, error_plot, dpi=self.config.dpi
            )

        # 2. FPS plot
        fps_path_str = None
        if len(req.fps_values) > 0:
            fps_path_str = plot_fps(req.timestamps, req.fps_values, fps_plot, dpi=self.config.dpi)

        # 3. Trajectory comparison plot
        traj_path_str = None
        if len(req.target_path_world) > 0 or len(req.camera_path_world) > 0:
            traj_path_str = plot_trajectory_comparison(
                req.target_path_world, req.camera_path_world, traj_plot, dpi=self.config.dpi
            )

        # 4. Compile PDF Report
        metrics = req.summary_metrics or {}
        pdf_path_str = generate_pdf_report(
            pdf_path=pdf_file,
            session_name=req.session_name,
            metrics=metrics,
            error_plot_path=err_path_str,
            fps_plot_path=fps_path_str,
            traj_plot_path=traj_path_str,
        )

        # 5. Compile HTML Report
        self._generate_html_report(html_file, req, metrics, err_path_str, fps_path_str, traj_path_str)

        return {
            "session_name": req.session_name,
            "pdf_report": pdf_path_str,
            "html_dashboard": str(html_file),
            "error_plot": err_path_str,
            "fps_plot": fps_path_str,
            "trajectory_plot": traj_path_str,
        }

    def _generate_html_report(
        self,
        html_file: Path,
        req: AnalyticsReportRequest,
        metrics: Dict[str, Any],
        err_plot: Optional[str],
        fps_plot: Optional[str],
        traj_plot: Optional[str],
    ) -> None:
        """Write standalone responsive HTML analytics dashboard."""
        compliance = metrics.get("compliance", {})
        status_color = "#27ae60" if compliance.get("overall_status", "").startswith("PASSED") else "#e74c3c"

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>FSOC Coarse Tracking Benchmark - {req.session_name}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
        .container {{ max-width: 1100px; margin: 0 auto; }}
        h1 {{ color: #38bdf8; margin-bottom: 5px; }}
        .badge {{ background: {status_color}; color: white; padding: 6px 14px; border-radius: 4px; font-weight: bold; display: inline-block; margin-bottom: 20px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 15px; margin-bottom: 25px; }}
        .card {{ background: #1e293b; padding: 15px; border-radius: 8px; border: 1px solid #334155; }}
        .card .title {{ font-size: 13px; color: #94a3b8; }}
        .card .val {{ font-size: 24px; font-weight: bold; color: #38bdf8; margin-top: 5px; }}
        .plot-container {{ background: #1e293b; padding: 20px; border-radius: 8px; margin-bottom: 20px; text-align: center; border: 1px solid #334155; }}
        img {{ max-width: 100%; height: auto; border-radius: 6px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>FSOC Virtual Camera Tracking Benchmark</h1>
        <p style="color: #94a3b8;">Session: {req.session_name} | ISRO Smart India Hackathon Evaluation</p>
        <div class="badge">{compliance.get('overall_status', 'EVALUATION REPORT')}</div>

        <div class="grid">
            <div class="card"><div class="title">RMSE Tracking Error</div><div class="val">{metrics.get('rmse_px', 0.0):.2f} px</div></div>
            <div class="card"><div class="title">Average Speed</div><div class="val">{metrics.get('mean_fps', 0.0):.1f} FPS</div></div>
            <div class="card"><div class="title">Lock Retention Rate</div><div class="val">{metrics.get('lock_retention_rate', 1.0)*100.0:.1f}%</div></div>
            <div class="card"><div class="title">Acquisition Time</div><div class="val">{metrics.get('acquisition_time_sec', 0.0) or 'N/A'} s</div></div>
        </div>

        {'<div class="plot-container"><h3>Tracking Centroid Error</h3><img src="' + Path(err_plot).name + '"></div>' if err_plot else ''}
        {'<div class="plot-container"><h3>Processing Throughput (FPS)</h3><img src="' + Path(fps_plot).name + '"></div>' if fps_plot else ''}
        {'<div class="plot-container"><h3>2D Spatial Trajectory</h3><img src="' + Path(traj_plot).name + '"></div>' if traj_plot else ''}
    </div>
</body>
</html>"""
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)
