"""Synthetic Dataset Generator Service."""
import json
from pathlib import Path
import random
from typing import Any, Dict, List, Optional
import cv2
import numpy as np
from tools.noise_generator.service import NoiseGeneratorService
from tools.simulator.service import SimulatorService
from tools.utilities.geometry import world_to_camera_pixel
from tools.virtual_camera.service import VirtualCameraService
from tools.weather_engine.service import WeatherEngineService
from .config import DatasetGenerationRequest
from .utils import (
    create_coco_template,
    export_video_clip,
    format_mot_line,
    format_yolo_label,
)


class DatasetGeneratorService:
    """Generates synthetic multi-condition training and benchmark datasets for FSOC tracking."""

    def __init__(self, root_output_dir: str = "datasets"):
        self.root_dir = Path(root_output_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, req: DatasetGenerationRequest) -> Dict[str, Any]:
        """Execute automated dataset generation pipeline."""
        dataset_path = self.root_dir / req.dataset_name
        images_dir = dataset_path / "images"
        labels_dir = dataset_path / "labels"
        gt_dir = dataset_path / "gt"

        images_dir.mkdir(parents=True, exist_ok=True)
        labels_dir.mkdir(parents=True, exist_ok=True)
        gt_dir.mkdir(parents=True, exist_ok=True)

        # Microservice pipelines
        sim = SimulatorService()
        cam = VirtualCameraService()
        weather = WeatherEngineService()
        noise = NoiseGeneratorService()

        coco_data = create_coco_template()
        mot_lines = []
        metadata_records = []
        frames_for_video = []

        ann_id_counter = 1
        cam_w, cam_h = cam.config.resolution

        for frame_idx in range(1, req.num_frames + 1):
            # Select condition variation
            motion = random.choice(req.motion_types)
            sim.targets[0].motion_type = motion

            w_cond = random.choice(req.weather_types)
            if w_cond == "fog":
                weather.config.fog_density = random.uniform(0.2, 0.6)
                weather.config.low_light = False
            elif w_cond == "rain":
                weather.config.rain_intensity = random.uniform(0.2, 0.5)
            elif w_cond == "low_light":
                weather.config.low_light = True
                weather.config.fog_density = 0.0
            else:
                weather.reset()

            n_std = random.choice(req.noise_levels)
            noise.config.gaussian_std = n_std
            noise.config.salt_pepper_ratio = 0.02 if n_std > 5.0 else 0.0

            # 1. Simulator physics step
            dt = 1.0 / cam.config.fps
            targets = sim.step(dt)
            target = targets[0]

            # 2. Camera step & crop
            canvas = sim.render_canvas()
            raw_camera_frame = cam.step(dt, canvas)

            # 3. Apply disturbances
            weather_frame = weather.process_frame(raw_camera_frame)
            final_frame = noise.process_frame(weather_frame)

            # Compute true target centroid on sensor pixel coordinates
            u, v, in_fov = world_to_camera_pixel(
                target_pos=(target.x, target.y),
                camera_center=cam.canvas_center,
                pan_deg=cam.pan_deg,
                tilt_deg=cam.tilt_deg,
                fov_deg=cam.config.fov,
                resolution=cam.config.resolution,
                jitter=cam.current_jitter,
                platform_motion=cam.current_platform_motion,
            )

            # Save frame image
            frame_filename = f"frame_{frame_idx:06d}.png"
            img_path = images_dir / frame_filename
            cv2.imwrite(str(img_path), final_frame)

            if req.export_video:
                frames_for_video.append(final_frame)

            # Register COCO Image
            coco_data["images"].append(
                {"id": frame_idx, "file_name": frame_filename, "width": cam_w, "height": cam_h}
            )

            # Bounding box on camera frame
            sw, sh = target.size
            bx = max(0.0, u - sw / 2.0)
            by = max(0.0, v - sh / 2.0)
            bw = min(float(cam_w - bx), float(sw))
            bh = min(float(cam_h - by), float(sh))

            if in_fov and bw > 2 and bh > 2:
                # 1. YOLO Label
                yolo_txt = format_yolo_label((bx, by, bw, bh), cam_w, cam_h, class_id=0)
                label_path = labels_dir / f"frame_{frame_idx:06d}.txt"
                with open(label_path, "w", encoding="utf-8") as f:
                    f.write(yolo_txt)

                # 2. COCO Annotation
                coco_data["annotations"].append(
                    {
                        "id": ann_id_counter,
                        "image_id": frame_idx,
                        "category_id": 1,
                        "bbox": [round(bx, 2), round(by, 2), round(bw, 2), round(bh, 2)],
                        "area": round(bw * bh, 2),
                        "iscrowd": 0,
                    }
                )
                ann_id_counter += 1

                # 3. MOT format line
                mot_lines.append(format_mot_line(frame_idx, target.target_id, (bx, by, bw, bh)))

            # 4. Metadata record
            metadata_records.append(
                {
                    "frame_idx": frame_idx,
                    "target_id": target.target_id,
                    "world_x": round(target.x, 3),
                    "world_y": round(target.y, 3),
                    "sensor_cx": round(u, 3),
                    "sensor_cy": round(v, 3),
                    "in_fov": in_fov,
                    "camera_pan_deg": round(cam.pan_deg, 3),
                    "camera_tilt_deg": round(cam.tilt_deg, 3),
                    "weather_condition": w_cond,
                    "noise_std": n_std,
                }
            )

        # Write COCO JSON
        coco_file = dataset_path / "annotations_coco.json"
        with open(coco_file, "w", encoding="utf-8") as f:
            json.dump(coco_data, f, indent=2)

        # Write MOT ground truth
        mot_file = gt_dir / "gt.txt"
        with open(mot_file, "w", encoding="utf-8") as f:
            f.writelines(mot_lines)

        # Write Metadata JSON
        meta_file = dataset_path / "metadata.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(metadata_records, f, indent=2)

        # Optional MP4 video export
        video_path = None
        if req.export_video and len(frames_for_video) > 0:
            video_file = dataset_path / f"{req.dataset_name}.mp4"
            export_video_clip(frames_for_video, video_file, fps=cam.config.fps)
            video_path = str(video_file)

        return {
            "dataset_name": req.dataset_name,
            "path": str(dataset_path),
            "total_frames": req.num_frames,
            "annotations_count": ann_id_counter - 1,
            "coco_file": str(coco_file),
            "mot_file": str(mot_file),
            "video_file": video_path,
        }

    def list_datasets(self) -> List[str]:
        """List all generated datasets."""
        return [d.name for d in self.root_dir.iterdir() if d.is_dir()]
