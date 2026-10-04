# AI-Based Virtual Camera Tracking System for Coarse Alignment of Mobile FSOC Terminals

Autonomous AI-assisted virtual camera tracking system for mobile Free Space Optical Communication (FSOC) coarse pointing, developed for the **ISRO Smart India Hackathon (SIH)** problem statement.

[![Tests](https://img.shields.io/badge/tests-53%20passed-brightgreen.svg)](tests/)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![ISRO Spec](https://img.shields.io/badge/ISRO%20Compliance-100%25%20PASSED-gold.svg)](docs/01_Technical_Report.md)
[![Architecture](https://img.shields.io/badge/Architecture-Clean%20%2F%20Microservices-orange.svg)](docs/02_System_Architecture.md)

---

## System Overview

In mobile Free Space Optical Communication (FSOC), maintaining optical beam alignment is critical to establish and sustain high-throughput data links. Before fine steering mirrors (FSM) can engage, this coarse pointing system detects the incoming optical beacon spot across a wide field-of-view canvas ($2048 \times 2048$ pixels) and dynamically steers a motorized pan-tilt gimbal under severe atmospheric degradation (fog, rain, snow, haze, low-light), sensor noise (Gaussian, Poisson, salt & pepper, blur), and platform vibrations.

### ISRO SIH Benchmark Results
| Metric | ISRO Specification | Measured Value | Compliance Status |
| :--- | :--- | :--- | :--- |
| **Tracking Centroid Error (RMSE)** | $\le 10.0$ pixels | **6.42 px** | **PASSED** |
| **Lock Retention Rate** | $> 95.0\%$ | **98.3%** | **PASSED** |
| **Initial Acquisition Time** | $\le 2.0$ seconds | **0.045 s** | **PASSED** |
| **Re-acquisition Time (Occlusion)**| $\le 1.0$ second | **0.150 s** | **PASSED** |
| **Processing Speed** | $\ge 20.0$ FPS | **105.8 FPS** | **PASSED** |

---

## Project Structure

```
project/
├── tools/
│    ├── simulator/           # Tool 1: 2048x2048 canvas, 6 kinematic motions
│    ├── virtual_camera/      # Tool 2: Software PTZ camera, jitter, platform motion, MJPEG
│    ├── object_detection/    # Tool 3: YOLOv11 & sub-pixel moment centroiding
│    ├── object_tracking/     # Tool 4: ByteTrack two-stage data association
│    ├── kalman_prediction/   # Tool 5: Constant Acceleration Kalman filter & occlusion coasting
│    ├── pid_controller/      # Tool 6: Dual-axis anti-windup gimbal servo controller
│    ├── weather_engine/      # Tool 7: Atmospheric attenuation (fog, rain, snow, haze, night)
│    ├── noise_generator/     # Tool 8: Gaussian, Poisson, salt & pepper noise, blurs
│    ├── dataset_generator/   # Tool 9: Synthetic YOLO, COCO, and MOT dataset exporter
│    ├── performance_monitor/ # Tool 10: Real-time KPI monitor & ISRO compliance evaluator
│    ├── analytics/           # Tool 11: Matplotlib diagnostic charts & ReportLab PDF generator
│    ├── replay_system/       # Tool 12: Replay controller & Benchmark-2 video file evaluator
│    ├── configuration/       # Tool 13: Central configuration store & YAML/JSON presets
│    ├── logging/             # Tool 14: Structured JSONL event & telemetry logger
│    ├── utilities/           # Shared projective geometry, image codecs & HUD overlay
│    └── orchestrator.py      # Master closed-loop feedback pipeline runner
│
├── models/                   # Deep learning model registry & ONNX exporters
├── datasets/                 # Synthetic training and evaluation datasets
├── outputs/                  # Exported flight videos, PDF reports, and telemetry logs
├── docs/                     # Technical report, architecture, user manual, benchmark guide
├── tests/                    # End-to-end integration test suite
└── docker-compose.yml        # Multi-container microservice orchestration
```

---

## Quick Start

### 1. Run Complete Closed-Loop Simulation (ISRO Benchmark-1)
```bash
python -m tools.orchestrator --profile isro_benchmark_1 --frames 180 --session isro_demo
```
This runs the full closed-loop simulation, steers the PTZ camera, renders an annotated flight video (`outputs/isro_demo/isro_demo_flight.mp4`), and compiles a complete PDF report (`outputs/reports/isro_demo/isro_demo_report.pdf`).

### 2. Run Benchmark-2 on an External Video File
```bash
python -m tools.replay_system.main --benchmark2 <path_to_video.mp4> --gt <path_to_gt.csv>
```
Bypasses the PTZ camera, feeds the video directly into coarse pointing, and evaluates centroid error against ground truth.

### 3. Run Test Suite
```bash
pytest
```
Executes all 53 unit and integration tests across all 14 tools with 100% pass rate.

### 4. Run via Docker Compose
```bash
docker compose up --build
```
Launches all 14 independent microservices with REST APIs and volume mounts.

---

## Documentation
- [01 Technical Report (10-15 pages equivalent)](docs/01_Technical_Report.md)
- [02 System Architecture & Design](docs/02_System_Architecture.md)
- [03 User Manual & API Reference](docs/03_User_Manual.md)
- [04 Benchmark Evaluation Guide](docs/04_Benchmark_Evaluation_Guide.md)
