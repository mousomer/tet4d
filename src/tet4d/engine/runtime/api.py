from __future__ import annotations

from pathlib import Path
from typing import Any

from ..help_text import (
    help_action_group_heading,
    help_action_layout_payload,
    help_action_panel_specs,
    help_fallback_topic,
    help_layout_payload,
    help_topic_block_lines,
    help_topic_compact_limit,
    help_topic_compact_overflow_line,
    help_topic_media_rule,
    help_value_template,
)
from .help_topics import help_action_topic_registry, help_topics_for_context
from .keybinding_runtime_state import KEYBINDING_STATE
from .keybinding_store import PROFILE_TINY
from .menu_config import (
    bot_defaults_by_mode,
    bot_options_rows,
    branding_copy,
    menu_items,
    pause_copy,
    pause_menu_id,
    settings_category_docs,
    ui_copy_payload,
    ui_copy_section,
)
from .menu_settings_state import (
    get_audio_settings,
    get_display_settings,
    load_app_settings_payload,
    save_app_settings_payload,
)
from .project_config import project_root_path
from .runtime_config import audio_event_specs
from .settings_schema import read_json_object_or_raise


def topology_lab_menu_payload_runtime() -> dict[str, Any]:
    path = project_root_path() / "config" / "topology" / "lab_menu.json"
    payload = read_json_object_or_raise(Path(path))
    return dict(payload)


def audio_event_specs_runtime() -> dict[str, tuple[float, int, float]]:
    return audio_event_specs()


def bot_options_rows_runtime() -> tuple[str, ...]:
    return bot_options_rows()


def bot_defaults_by_mode_runtime() -> dict[str, dict[str, int]]:
    return bot_defaults_by_mode()


def settings_category_docs_runtime():
    return settings_category_docs()


def pause_menu_id_runtime() -> str:
    return pause_menu_id()


def menu_items_runtime(menu_id: str):
    return menu_items(menu_id)


def pause_copy_runtime() -> dict[str, Any]:
    return pause_copy()


def branding_copy_runtime() -> dict[str, str]:
    return branding_copy()


def ui_copy_payload_runtime() -> dict[str, Any]:
    return ui_copy_payload()


def ui_copy_section_runtime(section: str) -> dict[str, Any]:
    return ui_copy_section(section)


def load_menu_payload_runtime() -> dict[str, Any]:
    return load_app_settings_payload()


def save_menu_payload_runtime(payload: dict[str, Any]) -> tuple[bool, str]:
    return save_app_settings_payload(payload)


def load_audio_payload_runtime() -> dict[str, Any]:
    return get_audio_settings()


def load_display_payload_runtime() -> dict[str, Any]:
    return get_display_settings()


def help_action_topic_registry_runtime() -> dict[str, str]:
    return help_action_topic_registry()


def help_topics_for_context_runtime(*args: Any, **kwargs: Any):
    return help_topics_for_context(*args, **kwargs)


def help_topic_block_lines_runtime(*args: Any, **kwargs: Any):
    return help_topic_block_lines(*args, **kwargs)


def help_topic_compact_limit_runtime(*args: Any, **kwargs: Any):
    return help_topic_compact_limit(*args, **kwargs)


def help_topic_compact_overflow_line_runtime(*args: Any, **kwargs: Any):
    return help_topic_compact_overflow_line(*args, **kwargs)


def help_value_template_runtime(*args: Any, **kwargs: Any):
    return help_value_template(*args, **kwargs)


def help_action_group_heading_runtime(*args: Any, **kwargs: Any):
    return help_action_group_heading(*args, **kwargs)


def help_fallback_topic_runtime(*args: Any, **kwargs: Any):
    return help_fallback_topic(*args, **kwargs)


def help_layout_payload_runtime(*args: Any, **kwargs: Any):
    return help_layout_payload(*args, **kwargs)


def help_action_layout_payload_runtime(*args: Any, **kwargs: Any):
    return help_action_layout_payload(*args, **kwargs)


def help_action_panel_specs_runtime(*args: Any, **kwargs: Any):
    return help_action_panel_specs(*args, **kwargs)


def help_topic_media_rule_runtime(*args: Any, **kwargs: Any):
    return help_topic_media_rule(*args, **kwargs)


def active_key_profile_runtime() -> str:
    return KEYBINDING_STATE.active_profile


def runtime_binding_groups_for_dimension_runtime(dimension: int):
    return KEYBINDING_STATE.runtime_binding_groups_for_dimension(dimension)


def binding_actions_for_dimension_runtime(dimension: int):
    return KEYBINDING_STATE.binding_actions_for_dimension(dimension)


def profile_tiny_runtime() -> str:
    return PROFILE_TINY


__all__ = [name for name in globals() if name.endswith("_runtime")]
