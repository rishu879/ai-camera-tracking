# Replay System & Benchmark-2 Runner Tool

Simulation Playback, Video Annotation, and ISRO Benchmark-2 Evaluation Microservice.

## Responsibilities
- **Simulation Replay Engine**:
  - Controls: Play, Pause, Resume, Step Forward, Step Backward, Seek to Frame.
  - Video Export: Renders annotated telemetry overlay (bounding boxes, Kalman prediction vector, PID error vector, aerospace reticle HUD) to MP4.
- **ISRO Benchmark-2 Evaluator**:
  - Implements the mandatory ISRO evaluation workflow:
    - Ingests external `.mp4` video files covering the complete screen with noise and moving beacon spot.
    - Bypasses PTZ simulator and feeds video frames directly into the coarse pointing pipeline.
    - Measures Centroiding Error against ground-truth coordinates.
    - Evaluates performance parameters: RMSE, Acquisition Time, Re-acquisition Time, Lock Retention Rate, and Processing Speed (FPS).
    - Auto-exports full benchmark metrics and annotated verification video.

## API Endpoints
- `GET /health`: Health status.
- `GET /replay/state`: Current playback state (frame index, total frames, speed).
- `POST /replay/step?forward=true`: Step frame-by-frame.
- `POST /replay/seek`: Jump directly to a target frame.
- `POST /benchmark2/run`: Run Benchmark-2 evaluation on input `.mp4` video.

## Running Locally
```bash
# Run API server
python -m tools.replay_system.main --host 0.0.0.0 --port 8014

# Or run Benchmark-2 directly on an external video
python -m tools.replay_system.main --benchmark2 datasets/sample.mp4
```

## Running with Docker
```bash
docker build -t fsoc-replay -f tools/replay_system/Dockerfile .
docker run -p 8014:8014 -v $(pwd)/outputs:/app/outputs fsoc-replay
```
