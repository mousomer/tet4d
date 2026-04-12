from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import pygame
from tet4d.ui.pygame.menu.menu_navigation_keys import normalize_menu_navigation_key
from tet4d.ui.pygame.ui_utils import default_menu_back_chip_rect


ActionHandler = Callable[[], bool]
RouteHandler = Callable[[str], bool]
RenderHandler = Callable[
    [str, str, tuple[dict[str, Any], ...], int, int, dict[str, int]],
    None,
]
SimpleHandler = Callable[[], bool]
KeydownHandler = Callable[[str, int, int], bool]


class ActionRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, ActionHandler] = {}

    def register(self, action_id: str, handler: ActionHandler) -> None:
        clean_id = action_id.strip().lower()
        if not clean_id:
            raise ValueError("action_id must be a non-empty string")
        self._handlers[clean_id] = handler

    def dispatch(self, action_id: str) -> bool:
        clean_id = action_id.strip().lower()
        handler = self._handlers.get(clean_id)
        if handler is None:
            raise KeyError(clean_id)
        return bool(handler())

    def action_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._handlers))


@dataclass
class _RunnerState:
    stack: list[str]
    selected_by_menu: dict[str, int]
    selected_action_by_item: dict[str, int]
    running: bool = True


def _action_group_actions(item: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    raw_actions = item.get("actions", ())
    if not isinstance(raw_actions, tuple):
        return tuple()
    return tuple(action for action in raw_actions if isinstance(action, dict))


def _action_group_state_key(menu_id: str, item_id: str) -> str:
    return f"{menu_id.strip().lower()}::{item_id.strip().lower()}"


def _default_action_group_index(item: dict[str, Any]) -> int:
    default_action_id = str(item.get("default_action_id", "")).strip().lower()
    actions = _action_group_actions(item)
    for idx, action in enumerate(actions):
        if str(action.get("id", "")).strip().lower() == default_action_id:
            return idx
    return 0


def _selected_action_group_index(
    state: _RunnerState,
    *,
    menu_id: str,
    item: dict[str, Any],
) -> int:
    actions = _action_group_actions(item)
    if not actions:
        return 0
    item_id = str(item.get("id", "")).strip().lower()
    state_key = _action_group_state_key(menu_id, item_id)
    selected = int(
        state.selected_action_by_item.get(
            state_key,
            _default_action_group_index(item),
        )
    )
    selected = max(0, min(len(actions) - 1, selected))
    state.selected_action_by_item[state_key] = selected
    return selected


def _current_menu_action_group_indexes(
    state: _RunnerState,
    *,
    menu_id: str,
    items: tuple[dict[str, Any], ...],
) -> dict[str, int]:
    indexes: dict[str, int] = {}
    for item in items:
        if str(item.get("type", "")).strip().lower() != "action_group":
            continue
        item_id = str(item.get("id", "")).strip().lower()
        if not item_id:
            continue
        indexes[item_id] = _selected_action_group_index(
            state,
            menu_id=menu_id,
            item=item,
        )
    return indexes


class MenuRunner:
    def __init__(
        self,
        *,
        menus: dict[str, dict[str, object]],
        start_menu_id: str,
        action_registry: ActionRegistry,
        render_menu: RenderHandler,
        handle_route: RouteHandler | None = None,
        handle_missing_action: Callable[[str], bool] | None = None,
        on_root_escape: SimpleHandler | None = None,
        on_quit_event: SimpleHandler | None = None,
        on_move: SimpleHandler | None = None,
        on_confirm: SimpleHandler | None = None,
        on_keydown: KeydownHandler | None = None,
        initial_selected: dict[str, int] | None = None,
        fps: int = 60,
    ) -> None:
        clean_start = start_menu_id.strip().lower()
        if clean_start not in menus:
            raise KeyError(f"Unknown start menu id: {clean_start}")
        self._menus = menus
        self._start_menu_id = clean_start
        self._action_registry = action_registry
        self._render_menu = render_menu
        self._handle_route = handle_route
        self._handle_missing_action = handle_missing_action
        self._on_root_escape = on_root_escape
        self._on_quit_event = on_quit_event
        self._on_move = on_move
        self._on_confirm = on_confirm
        self._on_keydown = on_keydown
        self._initial_selected = dict(initial_selected or {})
        self._fps = max(1, int(fps))

    def run(self) -> None:  # noqa: C901
        state = _RunnerState(
            stack=[self._start_menu_id],
            selected_by_menu={
                menu_id.strip().lower(): int(idx)
                for menu_id, idx in self._initial_selected.items()
            },
            selected_action_by_item={},
        )
        clock = pygame.time.Clock()

        while state.running:
            _dt = clock.tick(self._fps)
            current_menu_id = state.stack[-1]
            current_menu = self._menus[current_menu_id]
            items_obj = current_menu.get("items")
            if not isinstance(items_obj, tuple) or not items_obj:
                raise RuntimeError(f"menu '{current_menu_id}' has no items")
            items = items_obj

            selected = state.selected_by_menu.get(current_menu_id, 0)
            selected = max(0, min(len(items) - 1, selected))
            state.selected_by_menu[current_menu_id] = selected

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    close = True
                    if self._on_quit_event is not None:
                        close = bool(self._on_quit_event())
                    if close:
                        state.running = False
                        break
                    continue
                if (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and int(getattr(event, "button", 0)) == 1
                    and default_menu_back_chip_rect().collidepoint(
                        getattr(event, "pos", (-1, -1))
                    )
                ):
                    if len(state.stack) > 1:
                        state.stack.pop()
                        if self._on_move is not None:
                            self._on_move()
                        break
                    close = False
                    if self._on_root_escape is not None:
                        close = bool(self._on_root_escape())
                    if close:
                        state.running = False
                        break
                    continue
                if event.type != pygame.KEYDOWN:
                    continue
                key = normalize_menu_navigation_key(int(event.key))
                if self._on_keydown is not None and self._on_keydown(
                    current_menu_id,
                    key,
                    len(state.stack),
                ):
                    continue
                if event.key == pygame.K_q:
                    close = True
                    if self._on_quit_event is not None:
                        close = bool(self._on_quit_event())
                    elif self._on_root_escape is not None:
                        close = bool(self._on_root_escape())
                    if close:
                        state.running = False
                        break
                    continue
                if key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    if len(state.stack) > 1:
                        state.stack.pop()
                        if self._on_move is not None:
                            self._on_move()
                        break
                    close = False
                    if self._on_root_escape is not None:
                        close = bool(self._on_root_escape())
                    if close:
                        state.running = False
                        break
                    continue
                if key == pygame.K_UP:
                    selected = (selected - 1) % len(items)
                    state.selected_by_menu[current_menu_id] = selected
                    if self._on_move is not None:
                        self._on_move()
                    continue
                if key == pygame.K_DOWN:
                    selected = (selected + 1) % len(items)
                    state.selected_by_menu[current_menu_id] = selected
                    if self._on_move is not None:
                        self._on_move()
                    continue
                if key in (pygame.K_LEFT, pygame.K_RIGHT):
                    item = items[selected]
                    if str(item.get("type", "")).lower() != "action_group":
                        continue
                    actions = _action_group_actions(item)
                    if not actions:
                        continue
                    delta = -1 if key == pygame.K_LEFT else 1
                    action_index = _selected_action_group_index(
                        state,
                        menu_id=current_menu_id,
                        item=item,
                    )
                    state.selected_action_by_item[
                        _action_group_state_key(
                            current_menu_id,
                            str(item.get("id", "")),
                        )
                    ] = (action_index + delta) % len(actions)
                    if self._on_move is not None:
                        self._on_move()
                    continue
                if key not in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    continue

                if self._on_confirm is not None:
                    self._on_confirm()
                selected = state.selected_by_menu.get(current_menu_id, 0)
                selected = max(0, min(len(items) - 1, selected))
                item = items[selected]
                item_type = str(item.get("type", "")).lower()
                if item_type == "submenu":
                    target_menu_id = str(item.get("menu_id", "")).strip().lower()
                    if target_menu_id in self._menus:
                        state.stack.append(target_menu_id)
                    break
                if item_type == "route":
                    if self._handle_route is None:
                        break
                    route_id = str(item.get("route_id", "")).strip().lower()
                    if self._handle_route(route_id):
                        state.running = False
                    break
                if item_type == "action_group":
                    actions = _action_group_actions(item)
                    if not actions:
                        break
                    action = actions[
                        _selected_action_group_index(
                            state,
                            menu_id=current_menu_id,
                            item=item,
                        )
                    ]
                    action_id = str(action.get("action_id", "")).strip().lower()
                    try:
                        close = self._action_registry.dispatch(action_id)
                    except KeyError:
                        if self._handle_missing_action is None:
                            close = False
                        else:
                            close = bool(self._handle_missing_action(action_id))
                    if close:
                        state.running = False
                    break
                if item_type != "action":
                    break

                action_id = str(item.get("action_id", "")).strip().lower()
                if action_id == "back":
                    if len(state.stack) > 1:
                        state.stack.pop()
                        if self._on_move is not None:
                            self._on_move()
                        break
                    close = False
                    if self._on_root_escape is not None:
                        close = bool(self._on_root_escape())
                    if close:
                        state.running = False
                    break
                try:
                    close = self._action_registry.dispatch(action_id)
                except KeyError:
                    if self._handle_missing_action is None:
                        close = False
                    else:
                        close = bool(self._handle_missing_action(action_id))
                if close:
                    state.running = False
                break

            if not state.running:
                break
            current_menu_id = state.stack[-1]
            current_menu = self._menus[current_menu_id]
            items = current_menu["items"]
            selected = state.selected_by_menu.get(current_menu_id, 0)
            selected = max(0, min(len(items) - 1, selected))
            state.selected_by_menu[current_menu_id] = selected
            title = str(current_menu.get("title", current_menu_id))
            self._render_menu(
                current_menu_id,
                title,
                items,
                selected,
                len(state.stack),
                _current_menu_action_group_indexes(
                    state,
                    menu_id=current_menu_id,
                    items=items,
                ),
            )
