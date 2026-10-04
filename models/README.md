# Models Registry

This directory contains deep-learning model weights, ONNX export configurations, and inference scripts for the FSOC Coarse Tracking System.

## Architecture
The system employs a dual-tier perception architecture:
1. **Lightweight Sub-pixel Moment Centroiding (`AdaptiveSpotDetector`)**:
   - Zero-weight algorithm computing intensity-weighted Center of Gravity ($M_{10}/M_{00}, M_{01}/M_{00}$)
   - Throughput: $> 100$ FPS
   - Sub-pixel precision: $< 0.05$ pixels
   - Default primary detector for laser/beacon spots.

2. **YOLOv11 Deep-Learning Detector (`YOLOv11Detector`)**:
   - State-of-the-art single-stage object detector trained on optical beacon signatures and mobile terminal geometries.
   - Weights stored as `.onnx` for high-throughput cross-platform execution via ONNX Runtime with CPU/CUDA execution providers.

## Training & Exporting YOLOv11 for FSOC
1. Generate synthetic training dataset:
   ```bash
   python -m tools.dataset_generator.main --generate --name fsoc_yolo_train --frames 500
   ```
2. Export YOLOv11 model to ONNX:
   ```bash
   python models/download_or_export_yolov11.py --export
   ```
3. Load in detector:
   ```bash
   curl -X POST http://localhost:8007/model/load -H "Content-Type: application/json" -d '{"model_type": "yolov11", "model_path": "models/yolov11_beacon.onnx"}'
   ```
