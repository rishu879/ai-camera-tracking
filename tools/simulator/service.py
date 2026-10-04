"""Virtual Environment Simulator Service managing simulation state and physics."""
import math
import random
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from .config import SimulatorConfig, TargetState
from .utils import (
    compute_circular,
    compute_figure_8,
    compute_sinusoidal,
    compute_spiral,
    render_beacon_target,
)


class SimulatorService:
    """Core domain logic for the 2D/3D optical beacon environment simulator."""

    def __init__(self, config: Optional[SimulatorConfig] = None):
        self.config = config or SimulatorConfig()
        self.width = self.config.canvas_width
        self.height = self.config.canvas_height
        self.fps = self.config.fps
        self.dt = 1.0 / max(self.fps, 1.0)
        self.current_time = 0.0
        self.frame_index = 0
        self.targets: List[TargetState] = []
        self._target_meta: Dict[int, Dict[str, Any]] = {}
        self.reset()

    def reset(self) -> None:
        """Reset simulation time, counters, and restore default initial target."""
        self.current_time = 0.0
        self.frame_index = 0
        self.targets.clear()
        self._target_meta.clear()

        # Add default target (Center of screen, Figure-8 motion)
        self.add_target(
            target_id=1,
            shape="square",
            size=(10, 10),
            motion_type="figure_8",
            speed=25.0,
            intensity=255.0,
            initial_center=(self.width / 2.0, self.height / 2.0),
        )

    def add_target(
        self,
        target_id: Optional[int] = None,
        shape: str = "square",
        size: Tuple[int, int] = (10, 10),
        motion_type: str = "figure_8",
        speed: float = 25.0,
        intensity: float = 255.0,
        initial_center: Optional[Tuple[float, float]] = None,
    ) -> TargetState:
        """Add a new beacon target to the simulation."""
        tid = target_id if target_id is not None else (len(self.targets) + 1)
        center = initial_center or (self.width / 2.0, self.height / 2.0)

        # Meta tracking for straight / random motion state
        angle = random.uniform(0, 2 * math.pi)
        meta = {
            "center": center,
            "heading": angle,
            "x": center[0],
            "y": center[1],
            "vx": speed * math.cos(angle),
            "vy": speed * math.sin(angle),
        }
        self._target_meta[tid] = meta

        target = TargetState(
            target_id=tid,
            x=center[0],
            y=center[1],
            size=size,
            shape=shape,
            intensity=intensity,
            motion_type=motion_type.lower(),
            speed=speed,
            active=True,
        )
        self.targets.append(target)
        return target

    def step(self, custom_dt: Optional[float] = None) -> List[TargetState]:
        """Advance simulation clock by dt and update all active target positions."""
        dt = custom_dt if custom_dt is not None else self.dt
        self.current_time += dt
        self.frame_index += 1

        for target in self.targets:
            if not target.active:
                continue

            tid = target.target_id
            m_type = target.motion_type
            meta = self._target_meta.get(tid, {"center": (self.width / 2.0, self.height / 2.0)})
            center = meta.get("center", (self.width / 2.0, self.height / 2.0))

            if m_type == "figure_8":
                x, y, vx, vy, ax, ay = compute_figure_8(
                    self.current_time, center, scale=300.0, speed=target.speed
                )
            elif m_type == "circular":
                x, y, vx, vy, ax, ay = compute_circular(
                    self.current_time, center, radius=250.0, speed=target.speed
                )
            elif m_type == "sinusoidal":
                x, y, vx, vy, ax, ay = compute_sinusoidal(
                    self.current_time, center, amplitude=150.0, speed=target.speed, bounds=(self.width, self.height)
                )
            elif m_type == "spiral":
                x, y, vx, vy, ax, ay = compute_spiral(
                    self.current_time, center, speed=target.speed, max_radius=350.0
                )
            elif m_type == "straight":
                # Straight linear motion with boundary reflection
                px, py = meta["x"], meta["y"]
                vx, vy = meta["vx"], meta["vy"]
                margin = 80.0

                nx = px + vx * dt
                ny = py + vy * dt

                # Reflect at margins
                if nx < margin:
                    nx = margin
                    vx = -vx
                elif nx > self.width - margin:
                    nx = self.width - margin
                    vx = -vx

                if ny < margin:
                    ny = margin
                    vy = -vy
                elif ny > self.height - margin:
                    ny = self.height - margin
                    vy = -vy

                meta["x"], meta["y"] = nx, ny
                meta["vx"], meta["vy"] = vx, vy
                x, y = nx, ny
                ax, ay = 0.0, 0.0
            elif m_type == "random":
                # Ornstein-Uhlenbeck stochastic drift process
                px, py = meta["x"], meta["y"]
                vx, vy = meta["vx"], meta["vy"]
                theta_drift = 0.1
                sigma_drift = 15.0

                # Drift towards center + random perturbation
                dx_center = (self.width / 2.0) - px
                dy_center = (self.height / 2.0) - py

                ax = theta_drift * dx_center + random.gauss(0, sigma_drift)
                ay = theta_drift * dy_center + random.gauss(0, sigma_drift)

                vx += ax * dt
                vy += ay * dt

                # Clamp speed
                current_speed = math.hypot(vx, vy)
                if current_speed > target.speed:
                    scale = target.speed / max(current_speed, 1e-6)
                    vx *= scale
                    vy *= scale

                nx = px + vx * dt
                ny = py + vy * dt

                # Clamp within margins
                margin = 60.0
                nx = max(margin, min(self.width - margin, nx))
                ny = max(margin, min(self.height - margin, ny))

                meta["x"], meta["y"] = nx, ny
                meta["vx"], meta["vy"] = vx, vy
                x, y = nx, ny
            else:
                # Default static or unknown
                x, y = center
                vx, vy, ax, ay = 0.0, 0.0, 0.0, 0.0

            target.x = x
            target.y = y
            target.vx = vx
            target.vy = vy
            target.ax = ax
            target.ay = ay

        return self.targets

    def render_canvas(self) -> np.ndarray:
        """Render complete 2D world canvas with background and all active beacon targets."""
        # Initialize monochrome canvas
        canvas = np.full(
            (self.height, self.width), self.config.background_intensity, dtype=np.uint8
        )
        for target in self.targets:
            if target.active:
                render_beacon_target(
                    canvas,
                    x=target.x,
                    y=target.y,
                    size=target.size,
                    shape=target.shape,
                    intensity=target.intensity,
                )
        return canvas

    def get_state(self) -> Dict[str, Any]:
        """Return ground truth state of the simulator."""
        return {
            "frame_index": self.frame_index,
            "current_time": round(self.current_time, 4),
            "canvas_size": [self.width, self.height],
            "targets": [t.model_dump() for t in self.targets],
        }

