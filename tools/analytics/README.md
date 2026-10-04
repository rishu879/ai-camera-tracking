# Analytics Dashboard Tool

Plotting, Diagnostics, HTML Visualizer & PDF Benchmark Report Microservice for Mobile FSOC terminals.

## Responsibilities
- High-resolution Matplotlib diagnostic chart generation:
  - **Centroid Tracking Error Plot**: Time vs error with ISRO $10$ px threshold and RMSE baseline.
  - **Processing Speed Plot**: Time vs FPS with ISRO $20$ FPS threshold line.
  - **2D Trajectory Plot**: World Ground-Truth target path vs Camera optical axis boresight tracking trajectory.
- **Automated PDF Report Generation**:
  - Compiles full PDF evaluation report via ReportLab with executive summary, parameter compliance scorecard, embedded diagnostic plots, and system metrics.
- **Interactive HTML Dashboard**: Standalone dashboard with status badges and KPI cards.

## API Endpoints
- `GET /health`: Health status.
- `POST /generate/report`: Compile all plots, HTML dashboard, and PDF report for a session.
- `GET /reports/list`: List all generated benchmark reports.

## Running Locally
```bash
python -m tools.analytics.main --host 0.0.0.0 --port 8013
```

## Running with Docker
```bash
docker build -t fsoc-analytics -f tools/analytics/Dockerfile .
docker run -p 8013:8013 -v $(pwd)/outputs/reports:/app/outputs/reports fsoc-analytics
```
