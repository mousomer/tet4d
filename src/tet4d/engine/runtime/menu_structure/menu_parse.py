from __future__ import annotations

from typing import Any

from ..settings_schema import as_non_empty_string, require_object
from .parse_helpers import parse_copy_fields

_MENU_ITEM_TYPES = {"action", "submenu", "route"}
_MENU_ENTRYPOINT_KEYS = ("launcher", "pause")
_DEFAULT_MENU_ENTRYPOINTS = {
    "launcher": "launcher_root",
    "pause": "pause_root",
}


def parse_menu_item(raw: object, *, path: str) -> dict[str, str]:
    item = require_object(raw, path=path)
    item_type = as_non_empty_string(item.get("type"), path=f"{path}.type").lower()
    label = as_non_empty_string(item.get("label"), path=f"{path}.label")
    if item_type not in _MENU_ITEM_TYPES:
        raise RuntimeError(
            f"{path}.type must be one of: " + ", ".join(sorted(_MENU_ITEM_TYPES))
        )
    if item_type == "action":
        action_id = as_non_empty_string(
            item.get("action_id"),
            path=f"{path}.action_id",
        ).lower()
        return {"type": "action", "label": label, "action_id": action_id}
    if item_type == "submenu":
        menu_id = as_non_empty_string(
            item.get("menu_id"), path=f"{path}.menu_id"
        ).lower()
        return {"type": "submenu", "label": label, "menu_id": menu_id}
    route_id = as_non_empty_string(
        item.get("route_id"), path=f"{path}.route_id"
    ).lower()
    return {"type": "route", "label": label, "route_id": route_id}


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
        menus[menu_id] = {"title": title, "items": items}

    for menu_id, menu in menus.items():
        for idx, item in enumerate(menu["items"]):
            if item["type"] != "submenu":
                continue
            target = item["menu_id"]
            if target not in menus:
                raise RuntimeError(
                    f"structure.menus.{menu_id}.items[{idx}] references unknown submenu target: {target}"
                )
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
    return parse_copy_fields(
        raw,
        base_path="structure.launcher_subtitles",
        string_fields=("launcher_root", "launcher_play", "default"),
    )


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
