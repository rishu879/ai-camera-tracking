# Object Detection Tool

Optical Beacon Spot Detection with YOLOv11 & Sub-pixel Intensity-Weighted Centroiding for Mobile FSOC.

## Responsibilities
- Implements pluggable detection strategies adhering to the **Strategy Pattern**:
  - **`AdaptiveSpotDetector`**: Top-Hat morphological spatial filtering, Otsu adaptive thresholding, and sub-pixel intensity-weighted Center of Gravity ($M_{10}/M_{00}$, $M_{01}/M_{00}$). Operating at $>100$ FPS with $<0.05$ px precision.
  - **`YOLOv11Detector`**: YOLOv11 deep-learning model wrapper (ONNX/Torch) for detecting optical beacon spot signatures and terminal docking fixtures.
  - **`HybridDetector`**: High-confidence bounding box candidate extraction combined with sub-pixel moment refinement.
- Outputs for each detection:
  - Bounding Box `[x, y, w, h]`
  - Confidence `conf`
  - Class ID `class_id` and name `class_name`
  - Target Sub-pixel Centroid `(cx, cy)`
- Supports hot model swapping at runtime via REST API.

## API Endpoints
- `GET /health`: Health status.
- `POST /detect`: Run detection on input base64 image and return detected beacons and centroids.
- `POST /model/load`: Swap detector strategy (`adaptive`, `yolov11`, `hybrid`) or load new weights.
- `GET /model/current`: Active detector info and settings.
- `GET /config`: Current detection parameters.
- `POST /config`: Update confidence and area thresholds.

## Running Locally
```bash
python -m tools.object_detection.main --host 0.0.0.0 --port 8007 --model adaptive
```

## Running with Docker
```bash
docker build -t fsoc-detector -f tools/object_detection/Dockerfile .
docker run -p 8007:8007 fsoc-detector
```
