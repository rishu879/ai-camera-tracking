# Virtual Environment Simulator Tool

High-fidelity 2D/3D Optical Beacon and Environmental Dynamics Simulator for Mobile FSOC coarse alignment.

## Responsibilities
- Generates configurable virtual optical canvas (default $2048 \times 2048$ pixels, satisfying the $\ge 2000 \times 2000$ ISRO SIH requirement).
- Generates single or multiple moving optical beacon spot targets.
- Supports 6 analytical and stochastic kinematic trajectories:
  - **Straight Line**: Linear motion with boundary bounce reflection.
  - **Circular**: Constant angular velocity orbit.
  - **Figure-8**: Lemniscate parametric curve ($x = a\sin(\omega t), y = \frac{b}{2}\sin(2\omega t)$).
  - **Random**: Ornstein-Uhlenbeck stochastic drift process with soft centering force.
  - **Spiral**: Archimedean expanding/resetting spiral.
  - **Sinusoidal**: Harmonic oscillation with linear horizontal sweep.
- Computes ground-truth positions $(x, y, z)$, velocities $(v_x, v_y)$, and accelerations $(a_x, a_y)$ every frame at 30 FPS.
- Supports customizable target shapes (Square default, Gaussian spot profile), sizes (5-20 px), and radiant intensity.

## API Endpoints
- `GET /health`: Health status.
- `POST /step?dt=0.0333`: Advance physics simulation and return updated target states.
- `GET /state`: Retrieve current target ground-truth states.
- `POST /reset`: Reset simulation time and return targets to initial positions.
- `POST /target/add`: Dynamically spawn additional beacon targets.
- `GET /canvas?format=base64`: Render full world canvas frame (Base64 JPEG or binary JPEG stream).

## Running Locally
```bash
python -m tools.simulator.main --host 0.0.0.0 --port 8003
```

## Running with Docker
```bash
docker build -t fsoc-simulator -f tools/simulator/Dockerfile .
docker run -p 8003:8003 fsoc-simulator
```
