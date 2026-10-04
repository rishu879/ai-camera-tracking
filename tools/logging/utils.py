"""Log formatting and rotating file writer utilities."""
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def get_iso_timestamp() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


def append_jsonl(file_path: Path, entry: Dict[str, Any], max_bytes: int = 10 * 1024 * 1024) -> None:
    """Safely append a single JSON object to a JSON Lines file with size rotation."""
    file_path.parent.mkdir(parents=True, exist_ok=True)

    if file_path.exists() and file_path.stat().st_size >= max_bytes:
        # Rotate file
        rotated_path = file_path.with_name(f"{file_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl")
        file_path.rename(rotated_path)

    line = json.dumps(entry, default=str) + "\n"
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(line)


def read_jsonl(
    file_path: Path,
    limit: int = 100,
    severity: Optional[str] = None,
    filter_fn: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """Read entries from a JSONL file with optional filtering and reverse limit."""
    if not file_path.exists():
        return []

    results = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if severity and entry.get("severity", "").upper() != severity.upper():
                    continue
                if filter_fn and not filter_fn(entry):
                    continue
                results.append(entry)
            except Exception:
                continue

    # Return last 'limit' records
    return results[-limit:]
