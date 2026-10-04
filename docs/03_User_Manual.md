# User Manual: AI-Based Virtual Camera Tracking System

Complete operating instructions, configuration guide, and API reference for the FSOC Coarse Tracking software suite.

---

## 1. System Requirements & Installation

### Prerequisites
- Operating System: Windows 10/11 or Ubuntu Linux 20.04+
- Python: Version 3.10 or 3.11
- Docker & Docker Compose (optional for containerized deployment)

### Setup Instructions
1. Clone repository and navigate to root directory:
   ```bash
   cd "ai camera tracking"
   ```
2. Activate Python virtual environment:
   ```bash
   # Windows
   .venv\Scripts\activate

   # Linux/macOS
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r tools/configuration/requirements.txt
   pip install -r tools/virtual_camera/requirements.txt
   pip install -r tools/analytics/requirements.txt
   ```

---

## 2. Quick Start: Running the Master Orchestrator

To execute a complete closed-loop coarse tracking simulation run:
```bash
python -m tools.orchestrator --profile isro_benchmark_1 --frames 180 --session isro_demo
```

### Outputs Generated:
- Annotated flight video: `outputs/isro_demo/isro_demo_flight.mp4`
- Full PDF Evaluation Report: `outputs/reports/isro_demo/isro_demo_report.pdf`
- Interactive HTML Dashboard: `outputs/reports/isro_demo/isro_demo_dashboard.html`
- Telemetry Logs: `outputs/logs/`

---

## 3. Configuration Profiles

Configuration files are located in `tools/configuration/presets/`:
- `default.yaml`: Baseline system parameters.
- `isro_benchmark_1.yaml`: Mandatory SIH evaluation scenario (2048x2048 canvas, Figure-8 motion, 640x480 monochrome camera @ 30 FPS, max 5 deg/s slew, jitter & platform motion active).
- `isro_benchmark_2.yaml`: Benchmark-2 scenario bypassing PTZ for external video evaluation.
- `harsh_environment.yaml`: Dense fog, rain, low-light night illumination, and high sensor noise.

To switch profiles dynamically via API:
```bash
curl -X POST "http://localhost:8001/config/load_profile?name=harsh_environment"
```

---

## 4. Live Video Streaming & Web Interface

The Virtual Camera microservice provides a live 30 FPS MJPEG video stream:
- Start Virtual Camera service:
  ```bash
  python -m tools.virtual_camera.main --host 0.0.0.0 --port 8004
  ```
- Open browser at: `http://localhost:8004/stream`
- Raw snapshot API: `http://localhost:8004/frame?format=base64`

---

## 5. Microservice REST API Reference

| Service | Port | Key Endpoints | Description |
| :--- | :--- | :--- | :--- |
| **Configuration** | 8001 | `GET /config`, `POST /config`, `POST /config/load_profile` | Manage parameters & presets |
| **Logger** | 8002 | `POST /logs/event`, `POST /logs/tracking`, `GET /logs/query` | Structured JSONL logging |
| **Simulator** | 8003 | `POST /step`, `GET /state`, `GET /canvas`, `POST /target/add` | 2048x2048 canvas & kinematics |
| **Virtual Camera** | 8004 | `POST /ptz/speed`, `GET /frame`, `GET /stream` | Software PTZ camera & MJPEG |
| **Weather Engine**| 8005 | `POST /apply`, `POST /config`, `POST /reset` | Fog, rain, snow, haze, night |
| **Noise Generator**| 8006 | `POST /apply`, `POST /config` | Gaussian, Poisson, S&P, blur |
| **Object Detection**| 8007 | `POST /detect`, `POST /model/load`, `GET /model/current` | YOLOv11 & sub-pixel moments |
| **Object Tracking** | 8008 | `POST /track`, `GET /tracks`, `POST /reset` | ByteTrack multi-target association |
| **Kalman Prediction**| 8009| `POST /step`, `GET /forecast`, `POST /reset` | CA/CV state-space prediction |
| **PID Controller** | 8010 | `POST /compute`, `POST /tune`, `POST /reset` | Pan-Tilt visual servoing |
| **Dataset Generator**| 8011| `POST /generate/batch`, `GET /datasets/list` | Synthetic dataset creation |
| **Performance Monitor**| 8012| `POST /record`, `GET /summary`, `GET /metrics/latest` | Real-time KPI & compliance |
| **Analytics** | 8013 | `POST /generate/report`, `GET /reports/list` | Matplotlib plots & PDF reports |
| **Replay System** | 8014 | `POST /replay/step`, `POST /replay/seek`, `POST /benchmark2/run` | Replay & Benchmark-2 video ingest |
