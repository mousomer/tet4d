from __future__ import annotations

from pathlib import Path
from typing import Any

from .keybinding_runtime_state import KEYBINDING_STATE
from .keybinding_store import PROFILE_TINY
from .menu_config import (
    bot_defaults_by_mode,
    bot_options_rows,
    ui_copy_section,
)
from .project_config import project_root_path
from .settings_schema import read_json_object_or_raise


def topology_lab_menu_payload_runtime() -> dict[str, Any]:
    path = project_root_path() / "config" / "topology" / "lab_menu.json"
    payload = read_json_object_or_raise(Path(path))
    return dict(payload)


def bot_options_rows_runtime() -> tuple[str, ...]:
    return bot_options_rows()


def bot_defaults_by_mode_runtime() -> dict[str, dict[str, int]]:
    return bot_defaults_by_mode()


def ui_copy_section_runtime(section: str) -> dict[str, Any]:
    return ui_copy_section(section)


def active_key_profile_runtime() -> str:
    return KEYBINDING_STATE.active_profile


def runtime_binding_groups_for_dimension_runtime(dimension: int):
    return KEYBINDING_STATE.runtime_binding_groups_for_dimension(dimension)


def profile_tiny_runtime() -> str:
    return PROFILE_TINY


__all__ = [name for name in globals() if name.endswith("_runtime")]
