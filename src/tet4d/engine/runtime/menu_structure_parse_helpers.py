from __future__ import annotations

from typing import Any

from .settings_schema import MODE_KEYS, as_non_empty_string, require_list, require_object

UI_COPY_SECTION_SPECS: dict[str, dict[str, tuple[str, ...]]] = {
    "launcher": {
        "string_fields": (
            "info_active_profile_template",
            "info_continue_mode_template",
            "controls_hint_template",
            "controls_hint_template_tiny",
            "escape_hint_back",
            "escape_hint_quit",
        ),
    },
    "settings_hub": {
        "string_fields": (
            "title",
            "subtitle_categories_template",
            "reset_confirm_f8",
        ),
        "list_fields": ("hints",),
    },
    "keybindings_menu": {
        "string_fields": (
            "title",
            "subtitle_section_mode",
            "subtitle_binding_mode",
            "capture_template",
            "text_mode_confirm_hint",
        ),
        "list_fields": ("hints", "section_hints"),
    },
    "bot_options": {
        "string_fields": (
            "title",
            "subtitle",
            "saved_status",
            "reset_confirm_enter",
            "reset_confirm_f8",
            "reset_done_template",
        ),
        "list_fields": ("hints",),
    },
    "setup_menu": {
        "string_fields": (
            "title_template",
            "subtitle_template",
            "title_2d",
            "subtitle_2d",
            "bindings_hint_template",
            "compact_controls_hint",
        ),
    },
}


def parse_string_list(raw: object, *, path: str) -> tuple[str, ...]:
    values = require_list(raw, path=path)
    if not values:
        raise RuntimeError(f"{path} must not be empty")
    return tuple(
        as_non_empty_string(value, path=f"{path}[{idx}]")
        for idx, value in enumerate(values)
    )


def parse_mode_string_lists(
    raw_obj: dict[str, Any],
    *,
    base_path: str,
) -> dict[str, tuple[str, ...]]:
    parsed: dict[str, tuple[str, ...]] = {}
    for mode_key in MODE_KEYS:
        parsed[mode_key] = parse_string_list(
            raw_obj.get(mode_key),
            path=f"{base_path}.{mode_key}",
        )
    return parsed


def parse_copy_fields(
    raw: dict[str, Any],
    *,
    base_path: str,
    string_fields: tuple[str, ...],
    list_fields: tuple[str, ...] = (),
) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    for field in string_fields:
        parsed[field] = as_non_empty_string(
            raw.get(field),
            path=f"{base_path}.{field}",
        )
    for field in list_fields:
        parsed[field] = parse_string_list(
            raw.get(field),
            path=f"{base_path}.{field}",
        )
    return parsed


def parse_ui_copy(payload: dict[str, Any]) -> dict[str, Any]:
    raw = require_object(payload.get("ui_copy"), path="structure.ui_copy")
    parsed: dict[str, Any] = {}
    for section, spec in UI_COPY_SECTION_SPECS.items():
        section_path = f"structure.ui_copy.{section}"
        section_obj = require_object(raw.get(section), path=section_path)
        parsed[section] = parse_copy_fields(
            section_obj,
            base_path=section_path,
            string_fields=spec["string_fields"],
            list_fields=spec.get("list_fields", ()),
        )
    return parsed
