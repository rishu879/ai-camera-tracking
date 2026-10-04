# Benchmark Evaluation Guide: ISRO SIH Verification

Step-by-step instructions for reproducing and evaluating **Benchmark Performance-1** and **Benchmark Performance-2** according to ISRO SIH criteria.

---

## Evaluation Criteria Overview

| Milestone | Weightage | Evaluation Criteria |
| :--- | :--- | :--- |
| **Functional Verification** | 20% | All mandatory functions operational, GUI / stream working |
| **Benchmark Performance-1** | 30% | Closed-loop scenario execution, centroiding error log, auto-generated PDF performance report |
| **Benchmark Performance-2** | 30% | Bypass PTZ, ingest external `.mp4` video @ 30 FPS, measure centroiding error vs ground truth |
| **Technical Evaluation** | 20% | Architecture, algorithms, computer vision, novelty, code quality |

---

## 1. Running Benchmark Performance-1 (Closed-Loop Simulation)

Benchmark-1 tests the end-to-end autonomous closed loop:
- Canvas size: 2048 x 2048 pixels
- Camera resolution: 640 x 480 pixels @ 30 FPS
- Target motion: Figure-of-8 (Lemniscate)
- Disturbances: Mechanical jitter ($\pm 5$ px), platform vibration ($\pm 5$ px), Gaussian noise, atmospheric attenuation
- Gimbal slew limit: Max 5 deg/s pan/tilt speed

### Execution Command:
```bash
python -m tools.orchestrator --profile isro_benchmark_1 --frames 300 --session benchmark_1_eval
```

### Automatic Verification Checks:
1. **RMSE Tracking Error**: Automatically verified to be $\le 10.0$ pixels.
2. **Lock Retention Rate**: Automatically verified to be $> 95.0\%$.
3. **Acquisition Time**: Time to first lock $\le 2.0$ seconds.
4. **Processing Throughput**: Throughput $\ge 20.0$ FPS.
5. **Report Generation**: The system automatically compiles `outputs/reports/benchmark_1_eval/benchmark_1_eval_report.pdf` containing compliance scorecards and embedded trajectory graphs.

---

## 2. Running Benchmark Performance-2 (External Video Ingestion)

In Benchmark-2, evaluators provide arbitrary external `.mp4` video files recorded at 30 FPS containing noise and a moving beacon spot. The system bypasses the virtual camera PTZ simulator and feeds the video directly into the perception, tracking, and prediction pipeline to evaluate centroiding accuracy against predefined ground-truth coordinates.

### Execution Command:
```bash
python -m tools.replay_system.main --benchmark2 <path_to_video.mp4> --gt <path_to_ground_truth.csv>
```

### Or via REST API:
```bash
curl -X POST http://localhost:8014/benchmark2/run \
  -H "Content-Type: application/json" \
  -d '{
    "video_path": "datasets/test_video.mp4",
    "ground_truth_path": "datasets/test_gt.csv",
    "session_name": "isro_eval_video_01",
    "export_annotated_video": true
  }'
```

### Expected Deliverables:
- Centroid error log comparing detected centroids with predefined ground truth values.
- Automatically generated summary metrics JSON (`outputs/benchmark2/<session>/benchmark2_results.json`).
- Annotated verification video with HUD overlay reticles and centroid markers (`outputs/benchmark2/<session>/<session>_annotated.mp4`).

---

## 3. Automated Test Suite Execution

Run all 53 automated unit and integration tests:
```bash
pytest
```
Every single test passes with 0 failures, ensuring complete operational readiness.
