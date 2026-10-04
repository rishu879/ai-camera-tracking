# Dataset Generator Tool

Automated Synthetic Optical Beacon Dataset Generator for Mobile FSOC AI Training and Benchmarking.

## Responsibilities
- Generates synthetic optical sequences with dynamic atmospheric and sensor degradation.
- Multi-format label generation:
  - **YOLO format**: Normalized bounding boxes (`.txt` per frame).
  - **COCO format**: Full `annotations_coco.json` with categories, images, and bounding boxes.
  - **MOT format**: `gt/gt.txt` multiple object tracking labels (`frame, id, x, y, w, h, conf`).
  - **Metadata log**: Ground-truth sub-pixel centroids, camera pan/tilt angles, weather states, and noise levels.
- Video generation: Auto-encodes `.mp4` video clips at 30 FPS.

## API Endpoints
- `GET /health`: Health status.
- `POST /generate/batch`: Run synthetic dataset generation pipeline.
- `GET /datasets/list`: List generated dataset archives.

## Running Locally
```bash
python -m tools.dataset_generator.main --generate --name fsoc_benchmark_train --frames 60
```

## Running with Docker
```bash
docker build -t fsoc-dataset-gen -f tools/dataset_generator/Dockerfile .
docker run -p 8011:8011 -v $(pwd)/datasets:/app/datasets fsoc-dataset-gen
```
