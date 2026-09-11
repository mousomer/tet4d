from __future__ import annotations

import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest
from support import build_checkout


@pytest.fixture(autouse=True)
def isolated_user_overlay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[Path]:
    """Keep the host's inherited overlay out of every test in this suite.

    The resolver reads a machine-wide overlay keyed by workspace identity, so
    without isolation a workspace configured on the developer's machine would
    silently change what these tests resolve. Subprocess cases inherit the
    substituted configuration root through the environment.
    """
    # A sibling of the checkout, never inside it: a real inherited overlay
    # lives in the user's configuration directory, and a path inside the
    # repository would be reported relative rather than absolute.
    config_root = tmp_path.parent / f"{tmp_path.name}-xdg-config"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_root))
    try:
        yield config_root
    finally:
        shutil.rmtree(config_root, ignore_errors=True)


@pytest.fixture
def checkout(tmp_path: Path) -> Path:
    return build_checkout(tmp_path)
