from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from .menu_action_contracts import (
    LAUNCHER_ACTION_IDS,
    PARITY_ACTION_IDS,
    PAUSE_ACTION_IDS,
)
from .menu_config import (
    launcher_menu_id,
    menu_graph,
    pause_menu_id,
    reachable_action_ids,
)


@dataclass(frozen=True)
class MenuGraphIssue:
    kind: str
    message: str


def _reachable_menu_ids(
    menus: dict[str, dict[str, object]],
    *,
    start_ids: tuple[str, ...],
) -> set[str]:
    seen: set[str] = set()
    queue: deque[str] = deque(start_ids)
    while queue:
        menu_id = queue.popleft()
        if menu_id in seen:
            continue
        menu = menus.get(menu_id)
        if menu is None:
            continue
        seen.add(menu_id)
        raw_items = menu.get("items")
        if not isinstance(raw_items, tuple):
            continue
        for item in raw_items:
            if str(item.get("type", "")).lower() != "submenu":
                continue
            target = str(item.get("menu_id", "")).strip().lower()
            if target and target not in seen:
                queue.append(target)
    return seen


def lint_menu_graph() -> list[MenuGraphIssue]:
    menus = menu_graph()
    launch_root = launcher_menu_id()
    pause_root = pause_menu_id()
    issues: list[MenuGraphIssue] = []

    reachable_menus = _reachable_menu_ids(menus, start_ids=(launch_root, pause_root))
    unreachable = sorted(set(menus) - reachable_menus)
    if unreachable:
        issues.append(
            MenuGraphIssue(
                "reachability",
                "unreachable menus detected: " + ", ".join(unreachable),
            )
        )

    launcher_actions = set(reachable_action_ids(launch_root))
    pause_actions = set(reachable_action_ids(pause_root))

    launcher_missing_handlers = sorted(launcher_actions - set(LAUNCHER_ACTION_IDS))
    if launcher_missing_handlers:
        issues.append(
            MenuGraphIssue(
                "handlers",
                "launcher actions missing handlers: "
                + ", ".join(launcher_missing_handlers),
            )
        )

    pause_missing_handlers = sorted(pause_actions - set(PAUSE_ACTION_IDS))
    if pause_missing_handlers:
        issues.append(
            MenuGraphIssue(
                "handlers",
                "pause actions missing handlers: " + ", ".join(pause_missing_handlers),
            )
        )

    parity = set(PARITY_ACTION_IDS)
    launcher_parity_missing = sorted(parity - launcher_actions)
    pause_parity_missing = sorted(parity - pause_actions)
    if launcher_parity_missing:
        issues.append(
            MenuGraphIssue(
                "parity",
                "launcher parity actions missing: "
                + ", ".join(launcher_parity_missing),
            )
        )
    if pause_parity_missing:
        issues.append(
            MenuGraphIssue(
                "parity",
                "pause parity actions missing: " + ", ".join(pause_parity_missing),
            )
        )

    return issues
