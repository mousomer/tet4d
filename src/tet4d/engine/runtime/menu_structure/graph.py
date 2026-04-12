from __future__ import annotations

from typing import Any

_UTILITY_ACTION_IDS = {"back", "save", "reset", "display_apply"}


def collect_reachable_menu_ids(
    menus: dict[str, dict[str, Any]],
    *,
    start_menu_id: str,
) -> set[str]:
    reachable: set[str] = set()
    queue = [start_menu_id]
    while queue:
        menu_id = queue.pop()
        if menu_id in reachable:
            continue
        menu = menus.get(menu_id)
        if menu is None:
            continue
        reachable.add(menu_id)
        for item in menu["items"]:
            if item["type"] == "submenu":
                queue.append(item["menu_id"])
    return reachable


def collect_actions_for_menu_ids(
    menus: dict[str, dict[str, Any]],
    *,
    menu_ids: set[str],
) -> set[str]:
    action_ids = _collect_item_values_for_menu_ids(
        menus,
        menu_ids=menu_ids,
        item_type="action",
        item_field="action_id",
    )
    action_ids.update(
        _collect_item_values_for_menu_ids(
            menus,
            menu_ids=menu_ids,
            item_type="legacy_dispatch",
            item_field="action_id",
        )
    )
    action_ids.update(
        _collect_action_group_action_ids_for_menu_ids(
            menus,
            menu_ids=menu_ids,
        )
    )
    return action_ids


def collect_route_ids_for_menu_ids(
    menus: dict[str, dict[str, Any]],
    *,
    menu_ids: set[str],
) -> set[str]:
    return _collect_item_values_for_menu_ids(
        menus,
        menu_ids=menu_ids,
        item_type="route",
        item_field="route_id",
    )


def _collect_action_group_action_ids_for_menu_ids(
    menus: dict[str, dict[str, Any]],
    *,
    menu_ids: set[str],
) -> set[str]:
    values: set[str] = set()
    for menu_id in menu_ids:
        menu = menus.get(menu_id)
        if menu is None:
            continue
        for item in menu["items"]:
            if item["type"] != "action_group":
                continue
            for action in item.get("actions", ()):
                action_id = str(action.get("action_id", "")).strip().lower()
                if action_id and action_id not in _UTILITY_ACTION_IDS:
                    values.add(action_id)
    return values


def _collect_item_values_for_menu_ids(
    menus: dict[str, dict[str, Any]],
    *,
    menu_ids: set[str],
    item_type: str,
    item_field: str,
) -> set[str]:
    values: set[str] = set()
    for menu_id in menu_ids:
        menu = menus.get(menu_id)
        if menu is None:
            continue
        for item in menu["items"]:
            if item["type"] == item_type:
                value = item[item_field]
                if item_type == "action" and value in _UTILITY_ACTION_IDS:
                    continue
                values.add(value)
    return values
