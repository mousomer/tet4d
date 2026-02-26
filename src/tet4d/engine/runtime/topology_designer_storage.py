from __future__ import annotations

from pathlib import Path
from typing import Any

from .json_storage import read_json_object_or_empty, write_json_object as _write_json_object

def read_json_object(path: Path) -> dict[str, Any]:
    return read_json_object_or_empty(path)


def write_json_object(path: Path, payload: dict[str, Any]) -> None:
    _write_json_object(path, payload)
