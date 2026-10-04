"""Image processing, encoding, and HUD visualization utilities."""
import base64
from typing import Any, Dict, Optional, Tuple
import cv2
import numpy as np


def encode_image_base64(image: np.ndarray, quality: int = 85) -> str:
    """Encode OpenCV BGR or Monochrome image to Base64 JPEG string."""
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    success, buffer = cv2.imencode(".jpg", image, encode_param)
    if not success:
        raise ValueError("Failed to encode image to JPEG")
    return base64.b64encode(buffer).decode("utf-8")


def decode_image_base64(b64_string: str) -> np.ndarray:
    """Decode Base64 string to OpenCV BGR numpy array."""
    # Strip optional data URL header if present
    if "," in b64_string:
        b64_string = b64_string.split(",", 1)[1]
    raw_data = base64.b64decode(b64_string)
    np_arr = np.frombuffer(raw_data, dtype=np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError("Failed to decode base64 buffer to image")
    return image


def encode_image_jpeg(image: np.ndarray, quality: int = 85) -> bytes:
    """Encode OpenCV image to raw JPEG bytes (useful for MJPEG streaming)."""
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    success, buffer = cv2.imencode(".jpg", image, encode_param)
    if not success:
        raise ValueError("Failed to encode image to JPEG bytes")
    return buffer.tobytes()


def draw_crosshair(
    image: np.ndarray,
    center: Tuple[Any, Any],
    color: Tuple[int, int, int] = (0, 255, 0),
    length: int = 20,
    thickness: int = 1,
) -> None:
    """Draw a crosshair at target or boresight center."""
    cx, cy = int(round(float(center[0]))), int(round(float(center[1])))
    cv2.line(image, (cx - length, cy), (cx + length, cy), color, thickness)
    cv2.line(image, (cx, cy - length), (cx, cy + length), color, thickness)
    cv2.circle(image, (cx, cy), 4, color, 1)


def draw_telemetry_hud(
    image: np.ndarray,
    telemetry: Dict[str, Any],
    target_pos: Optional[Tuple[float, float]] = None,
    predicted_pos: Optional[Tuple[float, float]] = None,
    bbox: Optional[Tuple[int, int, int, int]] = None,
) -> np.ndarray:
    """
    Render professional aerospace/defense HUD overlay on top of frame.

    Overlay elements:
    - Boresight reticle at sensor center (320, 240)
    - 10-pixel error tolerance circle / threshold ring
    - Detected target bounding box and centroid marker
    - Kalman prediction vector
    - Real-time telemetry panel (FPS, Error, Lock Status, Pan/Tilt angles, Weather)
    """
    canvas = image.copy()
    if len(canvas.shape) == 2:
        canvas = cv2.cvtColor(canvas, cv2.COLOR_GRAY2BGR)

    h, w = canvas.shape[:2]
    cx_bore, cy_bore = w // 2, h // 2

    # 1. Boresight reticle (yellow) and 10-pixel requirement boundary (cyan)
    draw_crosshair(canvas, (int(cx_bore), int(cy_bore)), color=(0, 255, 255), length=15, thickness=1)
    # 10-pixel error circle (ISRO SIH requirement: error <= 10 px)
    cv2.circle(canvas, (int(cx_bore), int(cy_bore)), 10, (255, 255, 0), 1, cv2.LINE_AA)

    # 2. Detected target bounding box and centroid
    if bbox is not None:
        try:
            bx = int(round(float(bbox[0])))
            by = int(round(float(bbox[1])))
            bw = int(round(float(bbox[2])))
            bh = int(round(float(bbox[3])))
            cv2.rectangle(canvas, (bx, by), (bx + bw, by + bh), (0, 255, 0), 2)
        except Exception:
            pass

    if target_pos is not None:
        try:
            tx = int(round(float(target_pos[0])))
            ty = int(round(float(target_pos[1])))
            if 0 <= tx < w and 0 <= ty < h:
                draw_crosshair(canvas, (tx, ty), color=(0, 255, 0), length=10, thickness=2)
                # Draw line connecting boresight to target (tracking error vector)
                error_val = float(telemetry.get("tracking_error", np.hypot(tx - cx_bore, ty - cy_bore)))
                line_color = (0, 255, 0) if error_val <= 10.0 else (0, 0, 255)
                cv2.line(canvas, (int(cx_bore), int(cy_bore)), (tx, ty), line_color, 1, cv2.LINE_AA)
        except Exception:
            pass

    # 3. Kalman prediction vector (magenta)
    if predicted_pos is not None:
        try:
            px = int(round(float(predicted_pos[0])))
            py = int(round(float(predicted_pos[1])))
            if 0 <= px < w and 0 <= py < h:
                cv2.circle(canvas, (px, py), 5, (255, 0, 255), 2)
                if target_pos is not None:
                    tx = int(round(float(target_pos[0])))
                    ty = int(round(float(target_pos[1])))
                    cv2.arrowedLine(
                        canvas,
                        (tx, ty),
                        (px, py),
                        (255, 0, 255),
                        1,
                        tipLength=0.3,
                    )
        except Exception:
            pass

    # 4. Top Telemetry Banner (Semi-transparent overlay)
    overlay = canvas.copy()
    cv2.rectangle(overlay, (0, 0), (w, 55), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.7, canvas, 0.3, 0, canvas)

    fps = telemetry.get("fps", 0.0)
    error_px = telemetry.get("tracking_error", 0.0)
    locked = telemetry.get("locked", error_px <= 10.0)
    lock_rate = telemetry.get("lock_retention_rate", 0.0) * 100.0
    pan_deg = telemetry.get("pan_deg", 0.0)
    tilt_deg = telemetry.get("tilt_deg", 0.0)

    # Lock status badge
    lock_text = "LOCK ACQUIRED" if locked else "SEARCHING / LOST"
    lock_badge_color = (0, 255, 0) if locked else (0, 0, 255)
    cv2.putText(
        canvas,
        f"STATUS: {lock_text}",
        (10, 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        lock_badge_color,
        2,
        cv2.LINE_AA,
    )

    # Metrics row
    metrics_str = f"FPS: {fps:.1f} | ERR: {error_px:.1f}px | LOCK%: {lock_rate:.1f}% | PAN: {pan_deg:.2f}* | TILT: {tilt_deg:.2f}*"
    cv2.putText(
        canvas,
        metrics_str,
        (10, 45),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (220, 220, 220),
        1,
        cv2.LINE_AA,
    )

    return canvas
