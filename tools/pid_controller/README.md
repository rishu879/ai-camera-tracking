# PID Camera Controller Tool

Closed-Loop Visual Servoing & Gimbal Pan-Tilt Controller for Mobile FSOC coarse alignment.

## Responsibilities
- Dual-axis decoupled controller (Pan and Tilt).
- Inputs:
  - Estimated or predicted target position $(c_x, c_y)$ on sensor.
  - Optical boresight center target $(x_{boresight}, y_{boresight}) = (320, 240)$.
- Outputs:
  - Commanded Pan speed $\omega_{pan}$ and Tilt speed $\omega_{tilt}$ in deg/s.
- Advanced Control Features:
  - **Slew Rate Clamping**: Enforces maximum physical gimbal speed limits ($5-10^\circ/\text{s}$) per ISRO SIH specifications to prevent mechanical strain.
  - **Anti-Windup Integration**: Saturated integral accumulation prevents excessive overshoot and settling delays.
  - **Low-pass Filtered Derivative**: Filters high-frequency sensor centroid noise to eliminate motor chatter.
  - **Deadband Protection**: Ignores sub-pixel error micro-oscillations ($<0.5$ px) to prevent mechanical hunting.

## API Endpoints
- `GET /health`: Health status.
- `POST /compute`: Ingest target centroid and return commanded pan/tilt speeds.
- `POST /tune`: Dynamically update proportional, integral, and derivative gains.
- `POST /reset`: Reset integrator and derivative state.
- `GET /config`: Current PID configuration.
- `POST /config`: Update configuration parameters.

## Running Locally
```bash
python -m tools.pid_controller.main --host 0.0.0.0 --port 8010
```

## Running with Docker
```bash
docker build -t fsoc-pid -f tools/pid_controller/Dockerfile .
docker run -p 8010:8010 fsoc-pid
```
