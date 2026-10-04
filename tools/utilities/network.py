"""Networking, JSON serialization, and HTTP client utilities."""
import json
from typing import Any, Dict, Optional
import numpy as np


class NumpyJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder handling numpy types and dataclasses."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return super().default(obj)


def json_success_response(
    data: Any = None, message: str = "Success", meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Format standardized success JSON response."""
    res = {
        "status": "success",
        "message": message,
        "data": data if data is not None else {},
    }
    if meta is not None:
        res["meta"] = meta
    return res


def json_error_response(
    message: str, code: int = 400, details: Optional[Any] = None
) -> Dict[str, Any]:
    """Format standardized error JSON response."""
    res = {
        "status": "error",
        "code": code,
        "message": message,
    }
    if details is not None:
        res["details"] = details
    return res
