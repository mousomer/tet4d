from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from uuid import uuid4

import pytest
from tet4d.engine.runtime.project_config import state_dir_path

_USE_TMP_WORKAROUND = (
    os.environ.get("CODEX_MODE") == "1"
    or os.environ.get("TET4D_PYTEST_TMP_WORKAROUND") == "1"
)


def _pytest_tmp_root() -> Path:
    return state_dir_path() / "pytest_temp"


def _sanitize_node_name(node_name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", node_name).strip("_") or "test"


if _USE_TMP_WORKAROUND:

    @pytest.fixture
    def tmp_path(request: pytest.FixtureRequest) -> Path:
        tmp_root = _pytest_tmp_root()
        tmp_root.mkdir(parents=True, exist_ok=True)
        leaf = f"{_sanitize_node_name(request.node.name)}_{uuid4().hex}"
        path = tmp_root / leaf
        path.mkdir(parents=True, exist_ok=False)
        try:
            yield path
        finally:
            shutil.rmtree(path, ignore_errors=True)
