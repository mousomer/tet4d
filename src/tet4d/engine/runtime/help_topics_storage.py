from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json_file(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))
