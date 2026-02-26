from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json_object_or_default(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
        loaded = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        return default
    if not isinstance(loaded, dict):
        return default
    return loaded
