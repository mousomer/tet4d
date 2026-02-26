from __future__ import annotations

from pathlib import Path
from typing import Any

from .json_storage import atomic_write_json as _atomic_write_json, read_json_value_or_raise


def load_json_file(path: Path) -> Any:
    return read_json_value_or_raise(path)


def atomic_write_json(path: Path, payload: Any) -> None:
    _atomic_write_json(path, payload, trailing_newline=False)
