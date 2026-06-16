from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import pygame

from tet4d.ui.pygame.menu.menu_navigation_keys import normalize_menu_navigation_key


ActionHandler = Callable[[], bool]
RouteHandler = Callable[[str], bool]
RenderHandler = Callable[
    [
        str,
        str,
        tuple[dict[str, Any], ...],
        int,
        int,
        dict[str, int],
        "MenuPointerTarget | None",
        "MenuPointerTarget | None",
    ],
    tuple["MenuPointerTarget", ...] | None,
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


@dataclass(frozen=True)
class MenuPointerTarget:
    kind: str
    rect: pygame.Rect
    item_index: int = -1
    item_id: str = ""
    action_index: int = -1


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
        on_root_backspace: SimpleHandler | None = None,
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
        self._on_root_backspace = on_root_backspace
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
        hovered_target: MenuPointerTarget | None = None
        pressed_target: MenuPointerTarget | None = None
        pointer_targets: tuple[MenuPointerTarget, ...] = tuple()

        def _current_menu_bundle() -> tuple[str, dict[str, object], tuple[dict[str, Any], ...]]:
            current_menu_id = state.stack[-1]
            current_menu = self._menus[current_menu_id]
            items_obj = current_menu.get("items")
            if not isinstance(items_obj, tuple) or not items_obj:
                raise RuntimeError(f"menu '{current_menu_id}' has no items")
            return current_menu_id, current_menu, items_obj

        def _clamp_selected(
            menu_id: str,
            items: tuple[dict[str, Any], ...],
        ) -> int:
            selected = state.selected_by_menu.get(menu_id, 0)
            selected = max(0, min(len(items) - 1, selected))
            state.selected_by_menu[menu_id] = selected
            return selected

        def _clear_pointer_state() -> None:
            nonlocal hovered_target, pressed_target, pointer_targets
            hovered_target = None
            pressed_target = None
            pointer_targets = tuple()

        def _pointer_target_at_pos(pos: tuple[int, int]) -> MenuPointerTarget | None:
            for target in reversed(pointer_targets):
                if target.rect.collidepoint(pos):
                    return target
            return None

        def _set_pointer_focus(
            menu_id: str,
            items: tuple[dict[str, Any], ...],
            target: MenuPointerTarget | None,
        ) -> bool:
            if target is None:
                return False
            changed = False
            if target.kind in {"item", "action_group_action"}:
                selected = _clamp_selected(menu_id, items)
                if selected != target.item_index:
                    state.selected_by_menu[menu_id] = target.item_index
                    changed = True
            if target.kind == "action_group_action" and 0 <= target.item_index < len(items):
                item = items[target.item_index]
                if str(item.get("type", "")).strip().lower() == "action_group":
                    state_key = _action_group_state_key(
                        menu_id,
                        str(item.get("id", "")),
                    )
                    selected_action = _selected_action_group_index(
                        state,
                        menu_id=menu_id,
                        item=item,
                    )
                    if selected_action != target.action_index:
                        state.selected_action_by_item[state_key] = target.action_index
                        changed = True
            return changed

        def _dispatch_action(action_id: str) -> None:
            try:
                close = self._action_registry.dispatch(action_id)
            except KeyError:
                if self._handle_missing_action is None:
                    close = False
                else:
                    close = bool(self._handle_missing_action(action_id))
            if close:
                state.running = False

        def _pop_stack() -> None:
            if len(state.stack) <= 1:
                return
            state.stack.pop()
            _clear_pointer_state()
            if self._on_move is not None:
                self._on_move()

        def _handle_quit() -> bool:
            close = True
            if self._on_quit_event is not None:
                close = bool(self._on_quit_event())
            elif self._on_root_escape is not None:
                close = bool(self._on_root_escape())
            if close:
                state.running = False
                _clear_pointer_state()
            return close

        def _handle_root_escape() -> bool:
            close = False
            if self._on_root_escape is not None:
                close = bool(self._on_root_escape())
            if close:
                state.running = False
                _clear_pointer_state()
            return close

        def _handle_backspace() -> bool:
            if len(state.stack) > 1:
                _pop_stack()
                return True
            if self._on_root_backspace is None:
                return False
            close = bool(self._on_root_backspace())
            if close:
                state.running = False
                _clear_pointer_state()
            return close

        def _handle_escape() -> bool:
            if len(state.stack) > 1:
                return False
            return _handle_root_escape()

        def _activate_item(  # noqa: C901
            menu_id: str,
            item: dict[str, Any],
            *,
            action_index: int | None = None,
        ) -> None:
            item_type = str(item.get("type", "")).strip().lower()
            if item_type == "submenu":
                target_menu_id = str(item.get("menu_id", "")).strip().lower()
                if target_menu_id in self._menus:
                    state.stack.append(target_menu_id)
                    _clear_pointer_state()
                return
            if item_type == "route":
                if self._handle_route is None:
                    return
                route_id = str(item.get("route_id", "")).strip().lower()
                if self._handle_route(route_id):
                    state.running = False
                    _clear_pointer_state()
                return
            if item_type == "action_group":
                actions = _action_group_actions(item)
                if not actions:
                    return
                if action_index is None:
                    action_index = _selected_action_group_index(
                        state,
                        menu_id=menu_id,
                        item=item,
                    )
                safe_action_index = max(0, min(len(actions) - 1, int(action_index)))
                action = actions[safe_action_index]
                action_id = str(action.get("action_id", "")).strip().lower()
                _dispatch_action(action_id)
                if not state.running:
                    _clear_pointer_state()
                return
            if item_type != "action":
                return

            action_id = str(item.get("action_id", "")).strip().lower()
            if action_id == "back":
                if len(state.stack) > 1:
                    _pop_stack()
                    return
                _handle_root_escape()
                return
            _dispatch_action(action_id)
            if not state.running:
                _clear_pointer_state()

        def _render_current_menu() -> tuple[str, tuple[dict[str, Any], ...]]:
            nonlocal pointer_targets
            current_menu_id, current_menu, items = _current_menu_bundle()
            selected = _clamp_selected(current_menu_id, items)
            title = str(current_menu.get("title", current_menu_id))
            rendered_targets = self._render_menu(
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
                hovered_target,
                pressed_target,
            )
            pointer_targets = tuple(rendered_targets or ())
            return current_menu_id, items

        current_menu_id, items = _render_current_menu()

        while state.running:
            _dt = clock.tick(self._fps)
            current_menu_id, _current_menu, items = _current_menu_bundle()
            selected = _clamp_selected(current_menu_id, items)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    close = True
                    if self._on_quit_event is not None:
                        close = bool(self._on_quit_event())
                    if close:
                        state.running = False
                        break
                    continue
                if event.type == pygame.MOUSEMOTION:
                    hovered_target = _pointer_target_at_pos(
                        getattr(event, "pos", (-1, -1))
                    )
                    if _set_pointer_focus(current_menu_id, items, hovered_target):
                        selected = _clamp_selected(current_menu_id, items)
                        if self._on_move is not None:
                            self._on_move()
                    continue
                if (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and int(getattr(event, "button", 0)) == 1
                ):
                    hovered_target = _pointer_target_at_pos(
                        getattr(event, "pos", (-1, -1))
                    )
                    if _set_pointer_focus(current_menu_id, items, hovered_target):
                        selected = _clamp_selected(current_menu_id, items)
                        if self._on_move is not None:
                            self._on_move()
                    pressed_target = hovered_target
                    continue
                if (
                    event.type == pygame.MOUSEBUTTONUP
                    and int(getattr(event, "button", 0)) == 1
                ):
                    hovered_target = _pointer_target_at_pos(
                        getattr(event, "pos", (-1, -1))
                    )
                    clicked_target = (
                        hovered_target
                        if hovered_target is not None and hovered_target == pressed_target
                        else None
                    )
                    pressed_target = None
                    if clicked_target is None:
                        continue
                    if self._on_confirm is not None:
                        self._on_confirm()
                    if clicked_target.kind == "back":
                        if len(state.stack) > 1:
                            _pop_stack()
                            break
                        if _handle_root_escape():
                            break
                        continue
                    if clicked_target.kind == "side_back":
                        if _handle_backspace():
                            break
                        continue
                    if clicked_target.kind == "side_escape":
                        if _handle_escape():
                            break
                        continue
                    if clicked_target.kind == "side_quit":
                        if _handle_quit():
                            break
                        continue
                    if clicked_target.kind not in {"item", "action_group_action"}:
                        continue
                    if 0 <= clicked_target.item_index < len(items):
                        item = items[clicked_target.item_index]
                        _activate_item(
                            current_menu_id,
                            item,
                            action_index=(
                                clicked_target.action_index
                                if clicked_target.kind == "action_group_action"
                                else None
                            ),
                        )
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
                if key == pygame.K_BACKSPACE:
                    if _handle_backspace():
                        break
                    continue
                if key == pygame.K_ESCAPE:
                    if _handle_escape():
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
                selected = _clamp_selected(current_menu_id, items)
                item = items[selected]
                _activate_item(current_menu_id, item)
                break

            if not state.running:
                break
            current_menu_id, items = _render_current_menu()
