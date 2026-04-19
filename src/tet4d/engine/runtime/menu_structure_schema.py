from __future__ import annotations

from typing import Any

from .menu_runtime_graph import (
    compile_runtime_menu_graph,
    validate_runtime_menu_graph,
)
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
    parse_pause_copy,
    parse_settings_category_docs,
    parse_settings_category_metrics,
    parse_settings_option_labels,
    parse_settings_split_rules,
    parse_setup_fields,
    parse_setup_hints,
    resolve_field_max,
)
from .settings_schema import string_tuple


def _validate_setting_item_option_keys(
    menus: dict[str, dict[str, Any]],
    *,
    option_labels: dict[str, tuple[str, ...]],
) -> None:
    for menu_id, menu in menus.items():
        for idx, item in enumerate(menu["items"]):
            if str(item.get("type", "")).strip().lower() != "selector":
                continue
            options_key = str(item.get("options_key", "")).strip().lower()
            if options_key not in option_labels:
                raise RuntimeError(
                    "structure.menus."
                    f"{menu_id}.items[{idx}] selector references unknown options_key: "
                    f"{options_key}"
                )


def validate_structure_payload(payload: dict[str, Any]) -> dict[str, Any]:
    authored_menus = parse_menus(payload.get("menus"))
    authored_entrypoints = parse_menu_entrypoints(payload, menus=authored_menus)
    launcher_subtitles = parse_launcher_subtitles(payload)
    launcher_route_actions = parse_launcher_route_actions(payload)
    branding = parse_branding(payload)
    ui_copy = parse_ui_copy(payload)

    _, launcher_actions, launcher_route_ids = _entrypoint_reachability(
        authored_menus, start_menu_id=authored_entrypoints["launcher"]
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
    option_labels = parse_settings_option_labels(payload)
    _validate_setting_item_option_keys(authored_menus, option_labels=option_labels)
    runtime_graph = compile_runtime_menu_graph(
        authored_menus,
        authored_entrypoints=authored_entrypoints,
    )
    validate_runtime_menu_graph(
        runtime_graph["menus"],
        runtime_entrypoints=runtime_graph["menu_entrypoints"],
    )
    validated = {
        "authored_menus": authored_menus,
        "authored_menu_entrypoints": authored_entrypoints,
        "menus": authored_menus,
        "menu_entrypoints": authored_entrypoints,
        "runtime_menus": runtime_graph["menus"],
        "runtime_menu_entrypoints": runtime_graph["menu_entrypoints"],
        "runtime_menu_compile_results": runtime_graph["compile_results"],
        "launcher_subtitles": launcher_subtitles,
        "launcher_route_actions": launcher_route_actions,
        "branding": branding,
        "ui_copy": ui_copy,
        "bot_options_rows": string_tuple(
            payload.get("bot_options_rows"),
            path="structure.bot_options_rows",
        ),
        "pause_menu_rows": pause_rows,
        "pause_menu_actions": pause_actions,
        "pause_copy": parse_pause_copy(payload),
        "setup_fields": parse_setup_fields(payload),
        "setup_hints": parse_setup_hints(payload),
        "settings_option_labels": option_labels,
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
