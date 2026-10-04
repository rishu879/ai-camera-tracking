# Virtual PTZ Camera Tool

Software Focal Plane Array (FPA) Pan-Tilt-Zoom Camera with Disturbances for Mobile FSOC coarse alignment.

## Responsibilities
- Models an electro-optical camera payload with Pan $[-\pi, \pi]$, Tilt $[-\pi/2, \pi/2]$, and Zoom $[0.2, 10\times]$.
- Sensor parameters:
  - Resolution: $640 \times 480$ pixels (monochrome default or color RGB).
  - Field of View (FOV): $4^\circ \times 3^\circ$ (configurable).
  - Update rate: $30$ Hz (FPS).
- Dynamics & Constraints:
  - Slew rate clamping: Max Pan and Tilt speed bounded to $5-10^\circ/\text{s}$ per ISRO specifications.
- Environmental and Mechanical Disturbances:
  - High-frequency camera jitter: $\pm 20$ pixels/frame.
  - Low-frequency platform vibration / drift: $\pm 20$ pixels/frame (Linear, Circular, Random, Spiral).
- Live MJPEG video stream at `/stream` and snapshot REST API at `/frame`.

## API Endpoints
- `GET /health`: Health status.
- `GET /state`: Retrieve current pan/tilt angles, speeds, zoom, jitter, and platform displacement.
- `POST /ptz/speed`: Command slew speeds (`pan_speed_deg`, `tilt_speed_deg`).
- `POST /ptz/position`: Set direct orientation angles.
- `POST /reset`: Recenter camera boresight.
- `GET /frame?format=base64`: Capture single frame with camera telemetry.
- `GET /stream`: Live 30 FPS MJPEG multipart stream.

## Running Locally
```bash
python -m tools.virtual_camera.main --host 0.0.0.0 --port 8004
```

## Running with Docker
```bash
docker build -t fsoc-camera -f tools/virtual_camera/Dockerfile .
docker run -p 8004:8004 fsoc-camera
```
