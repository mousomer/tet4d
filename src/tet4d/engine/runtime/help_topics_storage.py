from __future__ import annotations

from pathlib import Path
from typing import Any

from .json_storage import read_json_value_or_raise


def load_json_file(path: Path) -> Any:
    return read_json_value_or_raise(path)
