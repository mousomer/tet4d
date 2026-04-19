from __future__ import annotations

from dataclasses import dataclass
from typing import Any


_HIDDEN_VISIBILITY_VALUES = {"hidden", "never", "false", "0"}
_UTILITY_ACTION_IDS = {"back", "save", "reset", "display_apply"}
_ACTIONABLE_ITEM_TYPES = {
    "action",
    "action_group",
    "submenu",
    "route",
    "toggle",
    "selector",
    "slider",
    "stepper",
    "keybinding_group",
    "legacy_dispatch",
}
_INLINE_COLLAPSIBLE_ITEM_TYPES = {
    "action",
    "toggle",
    "selector",
    "slider",
    "stepper",
    "legacy_dispatch",
}
_EXEMPT_LAYOUT_ROLES = {
    "modal",
    "confirmation",
    "capture",
    "text_entry",
    "preview",
    "test_modal",
    "binding_capture",
}


@dataclass(frozen=True)
class MenuCompileResult:
    kind: str
    menu_id: str
    menu: dict[str, Any] | None = None
    target_menu_id: str = ""
    inline_items: tuple[dict[str, Any], ...] = ()


def _is_visible_item(item: dict[str, Any]) -> bool:
    visibility = str(item.get("visibility", "always")).strip().lower()
    return visibility not in _HIDDEN_VISIBILITY_VALUES


def _is_actionable_item(item: dict[str, Any]) -> bool:
    item_type = str(item.get("type", "")).strip().lower()
    return item_type in _ACTIONABLE_ITEM_TYPES


def _is_utility_action(item: dict[str, Any]) -> bool:
    item_type = str(item.get("type", "")).strip().lower()
    if item_type != "action":
        return False
    action_id = str(item.get("action_id", "")).strip().lower()
    return action_id in _UTILITY_ACTION_IDS


def _has_semantic_metadata(item: dict[str, Any]) -> bool:
    if str(item.get("description", "")).strip():
        return True
    if str(item.get("subtitle", "")).strip():
        return True
    if str(item.get("help_text_key", "")).strip():
        return True
    layout_role = str(item.get("layout_role", "")).strip().lower()
    item_type = str(item.get("type", "")).strip().lower()
    return bool(layout_role and layout_role not in {"", item_type, "menu"})


def _section_group_bounds(
    items: tuple[dict[str, Any], ...],
    start_idx: int,
) -> tuple[int, int]:
    end_idx = start_idx + 1
    while end_idx < len(items):
        if str(items[end_idx].get("type", "")).strip().lower() == "section":
            break
        end_idx += 1
    return start_idx + 1, end_idx


def _section_should_survive(
    section_item: dict[str, Any],
    group_items: tuple[dict[str, Any], ...],
) -> bool:
    actionable_count = sum(1 for item in group_items if _is_actionable_item(item))
    if actionable_count >= 2:
        return True
    if _has_semantic_metadata(section_item):
        return True
    return False


def _normalize_sections(
    items: tuple[dict[str, Any], ...],
) -> tuple[dict[str, Any], ...]:
    normalized: list[dict[str, Any]] = []
    idx = 0
    while idx < len(items):
        item = items[idx]
        item_type = str(item.get("type", "")).strip().lower()
        if item_type != "section":
            normalized.append(item)
            idx += 1
            continue
        group_start, group_end = _section_group_bounds(items, idx)
        group_items = tuple(items[group_start:group_end])
        if _section_should_survive(item, group_items):
            normalized.append(item)
        normalized.extend(group_items)
        idx = group_end
    return tuple(normalized)


def _nonutility_items(
    items: tuple[dict[str, Any], ...],
) -> tuple[dict[str, Any], ...]:
    return tuple(
        item
        for item in items
        if _is_actionable_item(item) and not _is_utility_action(item)
    )


def _menu_is_exempt(
    menu_id: str,
    menu: dict[str, Any],
    *,
    entrypoint_ids: set[str],
) -> bool:
    if menu_id in entrypoint_ids:
        return True
    layout_role = str(menu.get("layout_role", "menu")).strip().lower()
    return layout_role in _EXEMPT_LAYOUT_ROLES


def _menu_has_binding_density(items: tuple[dict[str, Any], ...]) -> bool:
    return any(
        str(item.get("type", "")).strip().lower() == "keybinding_group"
        for item in items
    )


def _menu_has_meaningful_context(menu: dict[str, Any]) -> bool:
    if str(menu.get("subtitle", "")).strip():
        return True
    layout_role = str(menu.get("layout_role", "menu")).strip().lower()
    return layout_role not in {"", "menu"}


def _inline_items_for_single_leaf(
    items: tuple[dict[str, Any], ...],
) -> tuple[dict[str, Any], ...]:
    leaf_items = [
        dict(item)
        for item in items
        if str(item.get("type", "")).strip().lower() in _INLINE_COLLAPSIBLE_ITEM_TYPES
        and not _is_utility_action(item)
    ]
    utility_items = [
        dict(item)
        for item in items
        if _is_utility_action(item)
        and str(item.get("action_id", "")).strip().lower() != "back"
    ]
    if len(leaf_items) != 1:
        return tuple()
    return tuple((leaf_items[0], *utility_items))


def _compile_keep_result(
    menu_id: str,
    menu: dict[str, Any],
    items: tuple[dict[str, Any], ...],
) -> MenuCompileResult:
    return MenuCompileResult(
        kind="keep",
        menu_id=menu_id,
        menu={
            "title": str(menu.get("title", "")),
            "subtitle": str(menu.get("subtitle", "")).strip(),
            "layout_role": str(menu.get("layout_role", "menu")).strip().lower(),
            "items": items,
        },
    )


def _collapse_result_for_menu(
    menu_id: str,
    menu: dict[str, Any],
    items: tuple[dict[str, Any], ...],
    *,
    entrypoint_ids: set[str],
) -> MenuCompileResult:
    if _menu_is_exempt(menu_id, menu, entrypoint_ids=entrypoint_ids):
        return _compile_keep_result(menu_id, menu, items)
    if _menu_has_binding_density(items):
        return _compile_keep_result(menu_id, menu, items)
    nonutility = _nonutility_items(items)
    if not nonutility:
        return _compile_keep_result(menu_id, menu, items)
    if _menu_has_meaningful_context(menu):
        return _compile_keep_result(menu_id, menu, items)

    submenu_items = [
        item
        for item in nonutility
        if str(item.get("type", "")).strip().lower() == "submenu"
    ]
    inline_items = _inline_items_for_single_leaf(items)
    if len(submenu_items) == 1 and len(nonutility) == 1:
        return MenuCompileResult(
            kind="alias",
            menu_id=menu_id,
            target_menu_id=str(submenu_items[0].get("menu_id", "")).strip().lower(),
        )
    if len(inline_items) > 1 and len(nonutility) == 1:
        return MenuCompileResult(
            kind="inline",
            menu_id=menu_id,
            inline_items=inline_items,
        )
    return _compile_keep_result(menu_id, menu, items)


def compile_runtime_menu_graph(
    authored_menus: dict[str, dict[str, Any]],
    *,
    authored_entrypoints: dict[str, str],
) -> dict[str, Any]:
    memo: dict[str, MenuCompileResult] = {}
    stack: set[str] = set()
    entrypoint_ids = set(authored_entrypoints.values())

    def compile_menu(menu_id: str) -> MenuCompileResult:
        if menu_id in memo:
            return memo[menu_id]
        if menu_id in stack:
            raise RuntimeError(f"menu normalization cycle detected at {menu_id}")
        stack.add(menu_id)
        menu = authored_menus[menu_id]
        visible_items = tuple(
            dict(item) for item in menu["items"] if _is_visible_item(item)
        )
        normalized_items = _normalize_sections(visible_items)
        compiled_items: list[dict[str, Any]] = []
        for item in normalized_items:
            if str(item.get("type", "")).strip().lower() != "submenu":
                compiled_items.append(dict(item))
                continue
            target_menu_id = str(item.get("menu_id", "")).strip().lower()
            target_result = compile_menu(target_menu_id)
            if target_result.kind == "keep":
                rewritten = dict(item)
                rewritten["menu_id"] = target_result.menu_id
                compiled_items.append(rewritten)
                continue
            if target_result.kind == "alias":
                rewritten = dict(item)
                rewritten["menu_id"] = target_result.target_menu_id
                compiled_items.append(rewritten)
                continue
            compiled_items.extend(dict(inlined) for inlined in target_result.inline_items)
        compiled_tuple = _normalize_sections(tuple(compiled_items))
        result = _collapse_result_for_menu(
            menu_id,
            menu,
            compiled_tuple,
            entrypoint_ids=entrypoint_ids,
        )
        memo[menu_id] = result
        stack.remove(menu_id)
        return result

    for menu_id in authored_menus:
        compile_menu(menu_id)

    runtime_menus = {
        menu_id: result.menu
        for menu_id, result in memo.items()
        if result.kind == "keep" and result.menu is not None
    }
    runtime_entrypoints = {
        key: authored_entrypoints[key]
        for key in authored_entrypoints
    }
    return {
        "menus": runtime_menus,
        "menu_entrypoints": runtime_entrypoints,
        "compile_results": memo,
    }


def validate_runtime_menu_graph(
    runtime_menus: dict[str, dict[str, Any]],
    *,
    runtime_entrypoints: dict[str, str],
) -> None:
    entrypoint_ids = set(runtime_entrypoints.values())
    seen_setting_ids: dict[str, str] = {}

    for menu_id, menu in runtime_menus.items():
        items = tuple(menu.get("items", ()))
        if not items:
            raise RuntimeError(f"runtime menu {menu_id} must not be empty")
        if _menu_is_exempt(menu_id, menu, entrypoint_ids=entrypoint_ids):
            continue
        if _menu_has_binding_density(items):
            continue
        _validate_runtime_menu_shape(menu_id, items)
        _validate_runtime_setting_authority(
            menu_id,
            items,
            seen_setting_ids=seen_setting_ids,
        )
        _validate_runtime_sections(menu_id, items)

    for menu_id in entrypoint_ids:
        if menu_id in runtime_menus:
            _validate_runtime_depth(runtime_menus, menu_id, 1, (menu_id,))


def _validate_runtime_menu_shape(
    menu_id: str,
    items: tuple[dict[str, Any], ...],
) -> None:
    nonutility = _nonutility_items(items)
    submenu_count = sum(
        1
        for item in nonutility
        if str(item.get("type", "")).strip().lower() == "submenu"
    )
    setting_count = sum(
        1
        for item in nonutility
        if str(item.get("type", "")).strip().lower()
        in {"toggle", "selector", "slider", "stepper"}
    )
    if submenu_count == 1 and len(nonutility) == 1:
        raise RuntimeError(f"runtime menu {menu_id} retains a unary submenu wrapper")
    if setting_count == 1 and len(nonutility) == 1:
        raise RuntimeError(f"runtime menu {menu_id} retains a single-setting wrapper")


def _validate_runtime_setting_authority(
    menu_id: str,
    items: tuple[dict[str, Any], ...],
    *,
    seen_setting_ids: dict[str, str],
) -> None:
    for item in items:
        item_type = str(item.get("type", "")).strip().lower()
        if item_type not in {"toggle", "selector", "slider", "stepper"}:
            continue
        setting_id = str(item.get("setting_id", "")).strip().lower()
        owner = seen_setting_ids.get(setting_id)
        if owner is not None and owner != menu_id:
            raise RuntimeError(
                f"runtime menu graph duplicates setting authority for {setting_id}: {owner}, {menu_id}"
            )
        seen_setting_ids[setting_id] = menu_id


def _validate_runtime_sections(
    menu_id: str,
    items: tuple[dict[str, Any], ...],
) -> None:
    idx = 0
    while idx < len(items):
        item = items[idx]
        if str(item.get("type", "")).strip().lower() != "section":
            idx += 1
            continue
        start, end = _section_group_bounds(items, idx)
        group_items = tuple(items[start:end])
        if not _section_should_survive(item, group_items):
            raise RuntimeError(
                f"runtime menu {menu_id} retains a singleton section without semantic value: "
                f"{item.get('id', '<unknown>')}"
            )
        idx = end


def _validate_runtime_depth(
    runtime_menus: dict[str, dict[str, Any]],
    menu_id: str,
    depth: int,
    visiting: tuple[str, ...],
) -> None:
    max_depth = 3
    menu = runtime_menus[menu_id]
    for item in menu["items"]:
        if str(item.get("type", "")).strip().lower() != "submenu":
            continue
        target = str(item.get("menu_id", "")).strip().lower()
        if target in visiting:
            raise RuntimeError(
                "runtime menu graph contains a submenu cycle: "
                + " -> ".join((*visiting, target))
            )
        next_depth = depth + 1
        if next_depth > max_depth:
            raise RuntimeError(
                f"runtime menu path depth exceeds {max_depth}: "
                + " -> ".join((*visiting, target))
            )
        _validate_runtime_depth(runtime_menus, target, next_depth, (*visiting, target))
