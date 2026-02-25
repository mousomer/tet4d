from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json_file(path: Path) -> Any:
    """Read and decode JSON from disk for keybindings persistence."""
    return json.loads(path.read_text(encoding="utf-8"))
