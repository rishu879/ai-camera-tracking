# Logger Tool

Structured JSON Logging Microservice for the FSOC Virtual Camera Tracking System.

## Responsibilities
- Centralized asynchronous structured logging in JSON Lines (`.jsonl`) format.
- Independent specialized log streams:
  - `events.jsonl`: System lifecycle and control events.
  - `errors.jsonl`: Error logs with stack traces and execution contexts.
  - `tracking.jsonl`: High-speed frame-by-frame target detection coordinates, centroids, and lock states.
  - `camera.jsonl`: Camera PTZ position, commanded slew speeds, jitter, and platform motion.
  - `performance.jsonl`: Instantaneous FPS, RMSE, lock retention rate, CPU, and RAM telemetry.
- REST query and stats API.

## API Endpoints
- `GET /health`: Health status.
- `POST /logs/event`: Record system event.
- `POST /logs/tracking`: Record tracking state.
- `POST /logs/camera`: Record camera telemetry.
- `POST /logs/performance`: Record benchmark metrics.
- `GET /logs/query?category=tracking&limit=100`: Query log records.
- `GET /logs/stats`: Disk usage and file size stats.
- `DELETE /logs/clear`: Clear log files.

## Running Locally
```bash
python -m tools.logging.main --host 0.0.0.0 --port 8002
```

## Running with Docker
```bash
docker build -t fsoc-logger -f tools/logging/Dockerfile .
docker run -p 8002:8002 -v $(pwd)/outputs/logs:/app/outputs/logs fsoc-logger
```
