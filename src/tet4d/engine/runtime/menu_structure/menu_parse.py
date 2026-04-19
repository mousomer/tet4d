from __future__ import annotations

from typing import Any

from ..settings_schema import as_non_empty_string, require_object
from .parse_helpers import parse_copy_fields

_MENU_ITEM_TYPES = {
    "action",
    "action_group",
    "submenu",
    "route",
    "section",
    "info",
    "toggle",
    "selector",
    "slider",
    "stepper",
    "keybinding_group",
    "legacy_dispatch",
}
_SETTING_SEMANTIC_TYPES = {"bool", "enum", "int", "float"}
_MENU_ENTRYPOINT_KEYS = ("launcher", "pause", "settings", "keybindings")
_DEFAULT_MENU_ENTRYPOINTS = {
    "launcher": "launcher_root",
    "pause": "pause_root",
    "settings": "settings_root",
    "keybindings": "keybindings_root",
}


def _parse_action_group_item(item: dict[str, Any], *, path: str) -> dict[str, Any]:
    default_action_id = as_non_empty_string(
        item.get("default_action_id"),
        path=f"{path}.default_action_id",
    ).lower()
    raw_actions = item.get("actions")
    if not isinstance(raw_actions, list) or not raw_actions:
        raise RuntimeError(f"{path}.actions must be a non-empty list")
    actions: list[dict[str, str]] = []
    action_ids: set[str] = set()
    default_seen = False
    for action_idx, raw_action in enumerate(raw_actions):
        action = require_object(raw_action, path=f"{path}.actions[{action_idx}]")
        nested_id = as_non_empty_string(
            action.get("id"),
            path=f"{path}.actions[{action_idx}].id",
        ).lower()
        if nested_id in action_ids:
            raise RuntimeError(
                f"{path}.actions[{action_idx}] duplicates action id: {nested_id}"
            )
        action_ids.add(nested_id)
        action_label = as_non_empty_string(
            action.get("label"),
            path=f"{path}.actions[{action_idx}].label",
        )
        action_id = as_non_empty_string(
            action.get("action_id"),
            path=f"{path}.actions[{action_idx}].action_id",
        ).lower()
        if nested_id == default_action_id:
            default_seen = True
        actions.append(
            {
                "id": nested_id,
                "label": action_label,
                "action_id": action_id,
            }
        )
    if not default_seen:
        raise RuntimeError(
            f"{path}.default_action_id must reference one of {path}.actions[*].id"
        )
    return {
        "default_action_id": default_action_id,
        "actions": tuple(actions),
    }


def _parse_setting_item(
    item: dict[str, Any],
    *,
    item_type: str,
    path: str,
) -> dict[str, Any]:
    setting_id = as_non_empty_string(
        item.get("setting_id"),
        path=f"{path}.setting_id",
    ).lower()
    semantic_type = as_non_empty_string(
        item.get("semantic_type"),
        path=f"{path}.semantic_type",
    ).lower()
    if semantic_type not in _SETTING_SEMANTIC_TYPES:
        raise RuntimeError(
            f"{path}.semantic_type must be one of: "
            + ", ".join(sorted(_SETTING_SEMANTIC_TYPES))
        )
    parsed: dict[str, Any] = {
        "setting_id": setting_id,
        "semantic_type": semantic_type,
    }
    options_key = str(item.get("options_key", "")).strip().lower()
    if item_type == "toggle":
        if semantic_type != "bool":
            raise RuntimeError(f"{path}.toggle rows must declare semantic_type='bool'")
        if options_key:
            raise RuntimeError(f"{path}.toggle rows must not define options_key")
        return parsed
    if item_type == "selector":
        if semantic_type != "enum":
            raise RuntimeError(f"{path}.selector rows must declare semantic_type='enum'")
        parsed["options_key"] = as_non_empty_string(
            item.get("options_key"),
            path=f"{path}.options_key",
        ).lower()
        return parsed
    if semantic_type not in {"int", "float"}:
        raise RuntimeError(
            f"{path}.{item_type} rows must declare semantic_type='int' or 'float'"
        )
    if options_key:
        raise RuntimeError(f"{path}.{item_type} rows must not define options_key")
    return parsed


def _parse_keybinding_group_item(item: dict[str, Any], *, path: str) -> dict[str, Any]:
    binding_group = as_non_empty_string(
        item.get("binding_group"),
        path=f"{path}.binding_group",
    ).lower()
    binding_dimension = as_non_empty_string(
        item.get("binding_dimension"),
        path=f"{path}.binding_dimension",
    ).lower()
    binding_bucket = str(item.get("binding_bucket", "all")).strip().lower()
    return {
        "binding_group": binding_group,
        "binding_dimension": binding_dimension,
        "binding_bucket": binding_bucket or "all",
    }


def parse_menu_item(raw: object, *, path: str) -> dict[str, Any]:
    item = require_object(raw, path=path)
    item_id = as_non_empty_string(item.get("id"), path=f"{path}.id").lower()
    item_type = as_non_empty_string(item.get("type"), path=f"{path}.type").lower()
    label = as_non_empty_string(item.get("label"), path=f"{path}.label")
    if item_type not in _MENU_ITEM_TYPES:
        raise RuntimeError(
            f"{path}.type must be one of: " + ", ".join(sorted(_MENU_ITEM_TYPES))
        )
    parsed: dict[str, str] = {
        "id": item_id,
        "type": item_type,
        "label": label,
        "description": str(item.get("description", "")).strip(),
        "subtitle": str(item.get("subtitle", "")).strip(),
        "help_text_key": str(item.get("help_text_key", "")).strip().lower(),
        "visibility": str(item.get("visibility", "always")).strip().lower(),
        "enabled": str(item.get("enabled", "always")).strip().lower(),
        "layout_role": str(item.get("layout_role", item_type)).strip().lower(),
    }
    if item_type == "action":
        action_id = as_non_empty_string(
            item.get("action_id"),
            path=f"{path}.action_id",
        ).lower()
        parsed["action_id"] = action_id
        return parsed
    if item_type == "action_group":
        parsed.update(_parse_action_group_item(item, path=path))
        return parsed
    if item_type == "submenu":
        menu_id = as_non_empty_string(
            item.get("menu_id"), path=f"{path}.menu_id"
        ).lower()
        parsed["menu_id"] = menu_id
        return parsed
    if item_type == "route":
        route_id = as_non_empty_string(
            item.get("route_id"), path=f"{path}.route_id"
        ).lower()
        parsed["route_id"] = route_id
        return parsed
    if item_type in {"section", "info"}:
        return parsed
    if item_type in {"toggle", "selector", "slider", "stepper"}:
        parsed.update(_parse_setting_item(item, item_type=item_type, path=path))
        return parsed
    if item_type == "legacy_dispatch":
        action_id = as_non_empty_string(
            item.get("action_id"),
            path=f"{path}.action_id",
        ).lower()
        parsed["action_id"] = action_id
        return parsed
    parsed.update(_parse_keybinding_group_item(item, path=path))
    return parsed


def _parse_menu_items(menu_id: str, menu: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    raw_items = menu.get("items")
    if not isinstance(raw_items, list):
        raise RuntimeError(f"structure.menus.{menu_id}.items must be a list")
    if not raw_items:
        raise RuntimeError(f"structure.menus.{menu_id}.items must not be empty")
    items = tuple(
        parse_menu_item(
            raw_item,
            path=f"structure.menus.{menu_id}.items[{idx}]",
        )
        for idx, raw_item in enumerate(raw_items)
    )
    item_ids: set[str] = set()
    for idx, item in enumerate(items):
        item_id = str(item["id"])
        if item_id in item_ids:
            raise RuntimeError(
                f"structure.menus.{menu_id}.items[{idx}] duplicates item id: {item_id}"
            )
        item_ids.add(item_id)
    return items


def _validate_submenu_targets(menus: dict[str, dict[str, Any]]) -> None:
    for menu_id, menu in menus.items():
        for idx, item in enumerate(menu["items"]):
            if item["type"] != "submenu":
                continue
            target = item["menu_id"]
            if target not in menus:
                raise RuntimeError(
                    f"structure.menus.{menu_id}.items[{idx}] references unknown submenu target: {target}"
                )


def parse_menus(raw: object) -> dict[str, dict[str, Any]]:
    menus_obj = require_object(raw, path="structure.menus")
    if not menus_obj:
        raise RuntimeError("structure.menus must not be empty")

    menus: dict[str, dict[str, Any]] = {}
    for raw_menu_id, raw_menu in menus_obj.items():
        menu_id = as_non_empty_string(raw_menu_id, path="structure.menus keys").lower()
        menu = require_object(raw_menu, path=f"structure.menus.{menu_id}")
        title = as_non_empty_string(
            menu.get("title"),
            path=f"structure.menus.{menu_id}.title",
        )
        items = _parse_menu_items(menu_id, menu)
        menus[menu_id] = {
            "title": title,
            "subtitle": str(menu.get("subtitle", "")).strip(),
            "layout_role": str(menu.get("layout_role", "menu")).strip().lower(),
            "items": items,
        }

    _validate_submenu_targets(menus)
    return menus


def parse_menu_entrypoints(
    payload: dict[str, Any],
    *,
    menus: dict[str, dict[str, Any]],
) -> dict[str, str]:
    raw = payload.get("menu_entrypoints")
    entrypoints = dict(_DEFAULT_MENU_ENTRYPOINTS)
    if raw is not None:
        entry_obj = require_object(raw, path="structure.menu_entrypoints")
        for key in _MENU_ENTRYPOINT_KEYS:
            if key in entry_obj:
                entrypoints[key] = as_non_empty_string(
                    entry_obj[key],
                    path=f"structure.menu_entrypoints.{key}",
                ).lower()
    for key, menu_id in entrypoints.items():
        if menu_id not in menus:
            raise RuntimeError(
                f"structure.menu_entrypoints.{key} references unknown menu id: {menu_id}"
            )
    return entrypoints


def parse_launcher_subtitles(payload: dict[str, Any]) -> dict[str, str]:
    raw = require_object(
        payload.get("launcher_subtitles"), path="structure.launcher_subtitles"
    )
    subtitles = parse_copy_fields(
        raw,
        base_path="structure.launcher_subtitles",
        string_fields=("launcher_root", "launcher_play", "default"),
    )
    for raw_key, raw_value in raw.items():
        key = as_non_empty_string(
            raw_key,
            path="structure.launcher_subtitles keys",
        )
        if key in subtitles:
            continue
        subtitles[key] = as_non_empty_string(
            raw_value,
            path=f"structure.launcher_subtitles.{key}",
        )
    return subtitles


def parse_launcher_route_actions(payload: dict[str, Any]) -> dict[str, str]:
    raw = require_object(
        payload.get("launcher_route_actions"),
        path="structure.launcher_route_actions",
    )
    route_actions: dict[str, str] = {}
    for raw_route_id, raw_action_id in raw.items():
        route_id = as_non_empty_string(
            raw_route_id,
            path="structure.launcher_route_actions keys",
        ).lower()
        action_id = as_non_empty_string(
            raw_action_id,
            path=f"structure.launcher_route_actions.{route_id}",
        ).lower()
        route_actions[route_id] = action_id
    return route_actions


def parse_branding(payload: dict[str, Any]) -> dict[str, str]:
    raw = require_object(payload.get("branding"), path="structure.branding")
    return parse_copy_fields(
        raw,
        base_path="structure.branding",
        string_fields=("game_title", "signature_author", "signature_message"),
    )
