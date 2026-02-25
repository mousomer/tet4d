from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pygame


ActionHandler = Callable[[], bool]
RouteHandler = Callable[[str], bool]
RenderHandler = Callable[[str, str, tuple[dict[str, str], ...], int, int], None]
SimpleHandler = Callable[[], bool]


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
    running: bool = True


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
        self._initial_selected = dict(initial_selected or {})
        self._fps = max(1, int(fps))

    def run(self) -> None:  # noqa: C901
        state = _RunnerState(
            stack=[self._start_menu_id],
            selected_by_menu={
                menu_id.strip().lower(): int(idx)
                for menu_id, idx in self._initial_selected.items()
            },
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
                if event.type != pygame.KEYDOWN:
                    continue
                if event.key == pygame.K_ESCAPE:
                    if len(state.stack) > 1:
                        state.stack.pop()
                        if self._on_move is not None:
                            self._on_move()
                        break
                    close = True
                    if self._on_root_escape is not None:
                        close = bool(self._on_root_escape())
                    if close:
                        state.running = False
                        break
                    continue
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(items)
                    state.selected_by_menu[current_menu_id] = selected
                    if self._on_move is not None:
                        self._on_move()
                    continue
                if event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(items)
                    state.selected_by_menu[current_menu_id] = selected
                    if self._on_move is not None:
                        self._on_move()
                    continue
                if event.key not in (pygame.K_RETURN, pygame.K_KP_ENTER):
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
                if item_type != "action":
                    break

                action_id = str(item.get("action_id", "")).strip().lower()
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
            self._render_menu(current_menu_id, title, items, selected, len(state.stack))
