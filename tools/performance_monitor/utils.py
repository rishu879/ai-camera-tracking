"""Performance metrics mathematics and system telemetry sampling."""
import math
from typing import Dict, List, Tuple
import numpy as np
import psutil


def get_system_telemetry() -> Tuple[float, float, float]:
    """
    Sample CPU utilization %, Process Memory in MB, and GPU utilization if available.
    Returns: (cpu_pct, memory_mb, gpu_pct)
    """
    cpu_pct = psutil.cpu_percent(interval=None)
    process = psutil.Process()
    memory_mb = process.memory_info().rss / (1024.0 * 1024.0)

    # Optional GPU telemetry
    gpu_pct = 0.0
    try:
        import pynvml
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        gpu_pct = float(util.gpu)
    except Exception:
        pass

    return round(cpu_pct, 1), round(memory_mb, 1), round(gpu_pct, 1)


def compute_rmse(errors: List[float]) -> float:
    """Compute Root Mean Squared Error (RMSE)."""
    if len(errors) == 0:
        return 0.0
    arr = np.array(errors, dtype=np.float64)
    return float(np.sqrt(np.mean(arr**2)))


def compute_lock_retention(errors: List[float], threshold_px: float = 10.0) -> float:
    """Calculate percentage of frames where tracking error was within threshold."""
    if len(errors) == 0:
        return 1.0
    arr = np.array(errors, dtype=np.float64)
    locked_count = np.sum(arr <= threshold_px)
    return float(locked_count / len(arr))
