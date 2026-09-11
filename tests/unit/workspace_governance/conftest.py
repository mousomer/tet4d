from __future__ import annotations

from pathlib import Path

import pytest
from support import build_checkout


@pytest.fixture
def checkout(tmp_path: Path) -> Path:
    return build_checkout(tmp_path)
