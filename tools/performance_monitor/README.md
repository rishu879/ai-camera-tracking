# Performance Monitor Tool

Real-Time Telemetry & ISRO SIH Benchmark Compliance Evaluation Microservice.

## Responsibilities
- Real-time KPI telemetry computation:
  - **FPS**: Processing speed ($\ge 20$ FPS required).
  - **Latency**: End-to-end processing delay in milliseconds.
  - **Tracking Error**: Instantaneous centroid error $e(t) = \sqrt{(c_x - x_0)^2 + (c_y - y_0)^2}$ pixels ($\le 10$ pixels required).
  - **Acquisition Time**: Time to acquire stable boresight lock ($\le 2$ seconds required).
  - **Re-acquisition Time**: Time to recover lock after occlusion / dropout ($\le 1$ second required).
  - **RMSE**: Root Mean Squared Error across all active frames.
  - **Lock Retention Rate**: Percentage of operational frames meeting error constraint ($>95\%$ required / target loss $<5\%$).
  - **Hardware Utilization**: CPU %, GPU %, Memory in MB via `psutil`.
- Evaluates operational compliance against **ISRO SIH benchmark specifications**.

## API Endpoints
- `GET /health`: Health status.
- `POST /record`: Ingest frame telemetry sample.
- `GET /summary`: Aggregated KPIs and ISRO compliance evaluation.
- `GET /metrics/latest`: Most recent telemetry sample.
- `POST /reset`: Reset counters and history.
- `GET /config`: Current threshold settings.
- `POST /config`: Update threshold values.

## Running Locally
```bash
python -m tools.performance_monitor.main --host 0.0.0.0 --port 8012
```

## Running with Docker
```bash
docker build -t fsoc-monitor -f tools/performance_monitor/Dockerfile .
docker run -p 8012:8012 fsoc-monitor
```
