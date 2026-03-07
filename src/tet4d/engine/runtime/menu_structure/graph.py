from __future__ import annotations

from typing import Any


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
    return _collect_item_values_for_menu_ids(
        menus,
        menu_ids=menu_ids,
        item_type="action",
        item_field="action_id",
    )


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
                values.add(item[item_field])
    return values
