from __future__ import annotations

from typing import Any

from .menu_structure.menu_parse import (
    parse_branding,
    parse_launcher_route_actions,
    parse_launcher_subtitles,
    parse_menu_entrypoints,
    parse_menus,
)
from .menu_structure.parse_helpers import parse_ui_copy
from .menu_structure.policy import (
    _entrypoint_reachability,
    enforce_menu_entrypoint_parity,
    enforce_settings_split_policy,
    validate_launcher_route_actions,
)
from .menu_structure.settings_parse import (
    parse_keybinding_category_docs,
    parse_launcher_settings_routes,
    parse_pause_copy,
    parse_settings_category_docs,
    parse_settings_category_metrics,
    parse_settings_hub_layout_rows,
    parse_settings_option_labels,
    parse_settings_sections,
    parse_settings_split_rules,
    parse_setup_fields,
    parse_setup_hints,
    resolve_field_max,
)
from .settings_schema import string_tuple


def validate_structure_payload(payload: dict[str, Any]) -> dict[str, Any]:
    menus = parse_menus(payload.get("menus"))
    entrypoints = parse_menu_entrypoints(payload, menus=menus)
    launcher_subtitles = parse_launcher_subtitles(payload)
    launcher_route_actions = parse_launcher_route_actions(payload)
    branding = parse_branding(payload)
    ui_copy = parse_ui_copy(payload)

    _, launcher_actions, launcher_route_ids = _entrypoint_reachability(
        menus, start_menu_id=entrypoints["launcher"]
    )
    validate_launcher_route_actions(
        launcher_route_actions=launcher_route_actions,
        launcher_route_ids=launcher_route_ids,
        launcher_actions=launcher_actions,
    )

    pause_rows = string_tuple(
        payload.get("pause_menu_rows"), path="structure.pause_menu_rows"
    )
    pause_actions = string_tuple(
        payload.get("pause_menu_actions"),
        path="structure.pause_menu_actions",
        normalize_lower=True,
    )
    if len(pause_rows) != len(pause_actions):
        raise RuntimeError(
            "pause_menu_rows and pause_menu_actions must have equal length"
        )

    settings_docs = parse_settings_category_docs(payload)
    settings_hub_layout_rows = parse_settings_hub_layout_rows(
        payload.get("settings_hub_layout_rows")
    )
    settings_sections = parse_settings_sections(
        payload,
        layout_rows=settings_hub_layout_rows,
    )
    launcher_settings_menu = menus.get("launcher_settings_root", {})
    launcher_settings_items = launcher_settings_menu.get("items", ())
    launcher_settings_action_ids = {
        str(item["action_id"])
        for item in launcher_settings_items
        if isinstance(item, dict) and item.get("type") == "action"
    }
    launcher_settings_routes = parse_launcher_settings_routes(
        payload,
        settings_sections=settings_sections,
        launcher_settings_action_ids=launcher_settings_action_ids,
    )
    validated = {
        "menus": menus,
        "menu_entrypoints": entrypoints,
        "launcher_subtitles": launcher_subtitles,
        "launcher_route_actions": launcher_route_actions,
        "branding": branding,
        "ui_copy": ui_copy,
        "settings_hub_rows": string_tuple(
            payload.get("settings_hub_rows"),
            path="structure.settings_hub_rows",
        ),
        "settings_hub_layout_rows": settings_hub_layout_rows,
        "settings_sections": settings_sections,
        "launcher_settings_routes": launcher_settings_routes,
        "bot_options_rows": string_tuple(
            payload.get("bot_options_rows"),
            path="structure.bot_options_rows",
        ),
        "pause_menu_rows": pause_rows,
        "pause_menu_actions": pause_actions,
        "pause_copy": parse_pause_copy(payload),
        "setup_fields": parse_setup_fields(payload),
        "setup_hints": parse_setup_hints(payload),
        "settings_option_labels": parse_settings_option_labels(payload),
        "keybinding_category_docs": parse_keybinding_category_docs(payload),
        "settings_category_docs": settings_docs,
        "settings_split_rules": parse_settings_split_rules(payload),
        "settings_category_metrics": parse_settings_category_metrics(
            payload,
            settings_docs,
        ),
    }
    enforce_settings_split_policy(validated)
    enforce_menu_entrypoint_parity(validated)
    return validated


__all__ = ["resolve_field_max", "validate_structure_payload"]
