from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .json_storage import read_json_object_or_empty

def read_json_object(path: Path) -> dict[str, Any]:
    return read_json_object_or_empty(path)


def write_json_object(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
