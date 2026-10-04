# Configuration Manager Tool

The Central Configuration Service for the AI-Based Virtual Camera Tracking System for Coarse Alignment of Mobile FSOC Terminals.

## Responsibilities
- Stores and validates all simulation, camera, target, weather, noise, detector, tracker, Kalman filter, and PID controller parameters.
- Provides preset profiles conforming to **ISRO SIH specifications**:
  - `default`: Baseline configuration.
  - `isro_benchmark_1`: Mandatory benchmark with 2000x2000 canvas, 640x480 monochrome camera, 30 FPS, Figure-8 motion, max 5 deg/s pan/tilt speed, +-5px jitter, +-5px platform motion.
  - `isro_benchmark_2`: Benchmark scenario bypassing PTZ for external video input evaluation.
  - `harsh_environment`: Severe fog, rain, low light, and high sensor noise.
- Supports hot-reloading and live parameter tuning via REST APIs without restarting processes.
- Exposes typed Pydantic models for complete type safety.

## API Endpoints
- `GET /health`: Health status.
- `GET /config`: Retrieve current active configuration.
- `POST /config`: Partial update of configuration settings.
- `GET /config/profiles`: List available preset profiles.
- `POST /config/load_profile?name=<profile_name>`: Load preset profile.
- `POST /config/reset`: Reset active configuration to defaults.

## Running Locally
```bash
python -m tools.configuration.main --host 0.0.0.0 --port 8001
```

## Running with Docker
```bash
docker build -t fsoc-config -f tools/configuration/Dockerfile .
docker run -p 8001:8001 fsoc-config
```
