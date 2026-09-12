from __future__ import annotations

import os
import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest
from support import ROOT, build_checkout

from tools.workspace_governance.resolver.core import GovernanceResolver
from tools.workspace_governance.validators import core


def host_execution_mode() -> str:
    """The mode this machine declares, read before the overlay is isolated."""
    resolver = GovernanceResolver.for_root(ROOT)
    _, project, _ = resolver.load()
    local, _ = resolver.local_overlay()
    mode, _, _ = core.resolve_execution_mode(project, dict(os.environ), local)
    return mode


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
    # Read the host declaration first: isolating the overlay below would hide a
    # mode declared in it, and the fallback would silently answer instead.
    declared = host_execution_mode()
    config_root = tmp_path.parent / f"{tmp_path.name}-xdg-config"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_root))
    # Isolating the overlay also hides a mode declared there, so resolve the
    # host's declaration first and restate it. The suite must run in the mode
    # this machine is actually in: a runner installs the project and declares
    # installed, while a shared environment owning no distribution declares
    # source in its overlay. Fixing either here would assert against an
    # environment the suite is not running in.
    monkeypatch.setenv("TET4D_ENVIRONMENT_MODE", declared)
    try:
        yield config_root
    finally:
        shutil.rmtree(config_root, ignore_errors=True)


@pytest.fixture
def checkout(tmp_path: Path) -> Path:
    return build_checkout(tmp_path)
