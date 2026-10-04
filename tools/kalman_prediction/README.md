# Kalman Prediction Engine Tool

Discrete State-Space Kalman Filter for Future Trajectory Prediction and Occlusion Coasting in Mobile FSOC terminals.

## Responsibilities
- Models optical beacon kinematics in state space:
  - **Constant Acceleration (CA)** model: $\mathbf{x} = [p_x, p_y, v_x, v_y, a_x, a_y]^T$ (6 states).
  - **Constant Velocity (CV)** model: $\mathbf{x} = [p_x, p_y, v_x, v_y]^T$ (4 states).
- Predicts:
  - **Future Target Positions**: $k$-step forward projection ($\hat{\mathbf{x}}_{t+k} = \mathbf{F}^k \hat{\mathbf{x}}_t$) to compensate for processing/sensor latency.
  - **Velocity Vector**: Smoothed instantaneous kinematic speed and direction.
  - **Acceleration Vector**: Dynamic second-order rate of change.
- **Occlusion Handling & Rapid Re-acquisition**:
  - Automatically transitions to coasting mode when target detections drop out (due to clouds, obstacles, or severe attenuation).
  - Propagates covariance $\mathbf{P}$ without observation, maintaining stable trajectory extrapolation.
  - Immediately contracts covariance and re-locks within $\le 1$ second upon signal reappearance (meeting the ISRO SIH re-acquisition requirement).

## API Endpoints
- `GET /health`: Health status.
- `POST /step`: Process new measurement observation `[cx, cy]` or signal dropout `None`.
- `GET /forecast?steps=5`: Get projected coordinates for future frames.
- `GET /state`: Current kinematic state, covariance, and occlusion status.
- `POST /reset`: Reset filter covariance and state.
- `GET /config`: Current Kalman parameters.
- `POST /config`: Update noise and model configurations.

## Running Locally
```bash
python -m tools.kalman_prediction.main --host 0.0.0.0 --port 8009
```

## Running with Docker
```bash
docker build -t fsoc-kalman -f tools/kalman_prediction/Dockerfile .
docker run -p 8009:8009 fsoc-kalman
```
