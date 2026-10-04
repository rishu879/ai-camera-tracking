# Object Tracking Tool

ByteTrack Multi-Object Tracking Microservice for Optical Laser Beacons in FSOC terminals.

## Responsibilities
- Implements the **ByteTrack** two-stage data association algorithm:
  - **Stage 1**: Associates active tracks with high-confidence detections using Hungarian linear assignment.
  - **Stage 2**: Associates surviving unmatched tracks with low-confidence detections (recovering targets degraded by transient atmospheric haze, motion blur, or noise).
- Tracks unique identity (`track_id`), bounding boxes, and sub-pixel centroids over time.
- Maintains multi-frame kinematic trajectory history buffers.
- Estimates instantaneous and smoothed 2D target velocity vectors ($v_x, v_y$).
- Tracks lifecycle states: *New*, *Tracked*, *Lost*, *Removed*.

## API Endpoints
- `GET /health`: Health status.
- `POST /track`: Ingest frame detections and update track associations.
- `GET /tracks`: Retrieve list of active tracks and trajectories.
- `POST /reset`: Reset tracker state and track IDs.
- `GET /config`: Current tracking parameters.
- `POST /config`: Update association and loss thresholds.

## Running Locally
```bash
python -m tools.object_tracking.main --host 0.0.0.0 --port 8008
```

## Running with Docker
```bash
docker build -t fsoc-tracker -f tools/object_tracking/Dockerfile .
docker run -p 8008:8008 fsoc-tracker
```
