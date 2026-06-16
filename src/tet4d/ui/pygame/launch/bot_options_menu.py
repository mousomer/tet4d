from __future__ import annotations

from dataclasses import dataclass

import pygame

from tet4d.ai.playbot.types import (
    BOT_MODE_OPTIONS,
    BOT_PLANNER_ALGORITHM_OPTIONS,
    BOT_PLANNER_PROFILE_OPTIONS,
    bot_mode_from_index,
    bot_mode_label,
    bot_planner_algorithm_from_index,
    bot_planner_algorithm_label,
    bot_planner_profile_from_index,
    bot_planner_profile_label,
)
from tet4d.engine.runtime.api import (
    bot_defaults_by_mode_runtime,
    bot_options_rows_runtime,
    ui_copy_section_runtime,
)
from tet4d.engine.runtime.menu_settings_state import (
    load_app_settings_payload,
    save_app_settings_payload,
)
from tet4d.ui.pygame.menu.menu_navigation_keys import normalize_menu_navigation_key
from tet4d.ui.pygame.runtime_ui.audio import play_sfx
from tet4d.ui.pygame.ui_utils import (
    compute_vertical_scroll_metrics,
    draw_corner_chip,
    draw_selection_highlight,
    draw_tron_menu_background,
    draw_tron_panel,
    draw_vertical_scrollbar,
    ensure_scroll_offset_visible,
    fit_text,
    format_menu_title,
    standard_menu_panel_rect,
)


_BG_TOP = (14, 18, 44)
_BG_BOTTOM = (4, 7, 20)
_TEXT_COLOR = (232, 232, 240)
_HIGHLIGHT_COLOR = (255, 224, 128)
_MUTED_COLOR = (192, 200, 228)

_BOT_DIMENSIONS = (2, 3, 4)
_BOT_MENU_ROWS = bot_options_rows_runtime()
_BOT_DEFAULTS = bot_defaults_by_mode_runtime()
_BOT_COPY = ui_copy_section_runtime("bot_options")


@dataclass
class _BotMenuState:
    payload: dict[str, object]
    dimension: int = 2
    selected: int = 0
    scroll_offset: int = 0
    status: str = ""
    status_error: bool = False
    pending_reset_confirm: bool = False
    dirty: bool = False
    running: bool = True


@dataclass(frozen=True)
class _BotPointerTarget:
    kind: str
    rect: pygame.Rect
    index: int = -1


def _mode_key_from_dimension(dimension: int) -> str:
    safe_dimension = max(2, min(4, int(dimension)))
    return f"{safe_dimension}d"


def _bot_mode_settings(loop: _BotMenuState) -> dict[str, int]:
    settings = loop.payload.setdefault("settings", {})
    if not isinstance(settings, dict):
        settings = {}
        loop.payload["settings"] = settings

    mode_key = _mode_key_from_dimension(loop.dimension)
    defaults = _BOT_DEFAULTS[mode_key]
    mode_settings = settings.get(mode_key)
    if not isinstance(mode_settings, dict):
        mode_settings = dict(defaults)
        settings[mode_key] = mode_settings

    for attr_name, default_value in defaults.items():
        value = mode_settings.get(attr_name)
        if isinstance(value, bool) or not isinstance(value, int):
            mode_settings[attr_name] = default_value
    return mode_settings


def _bot_values(loop: _BotMenuState) -> tuple[str, ...]:
    mode_settings = _bot_mode_settings(loop)
    bot_mode = bot_mode_from_index(mode_settings["bot_mode_index"])
    algorithm = bot_planner_algorithm_from_index(mode_settings["bot_algorithm_index"])
    profile = bot_planner_profile_from_index(mode_settings["bot_profile_index"])
    return (
        f"{loop.dimension}D",
        bot_mode_label(bot_mode),
        bot_planner_algorithm_label(algorithm),
        bot_planner_profile_label(profile),
        str(mode_settings["bot_speed_level"]),
        str(mode_settings["bot_budget_ms"]),
        "",
        "",
        "",
    )


def _set_bot_status(
    loop: _BotMenuState, message: str, *, is_error: bool = False
) -> None:
    loop.status = message
    loop.status_error = is_error


def _save_bot_menu(loop: _BotMenuState) -> tuple[bool, str]:
    ok, msg = save_app_settings_payload(loop.payload)
    if ok:
        _set_bot_status(loop, _BOT_COPY["saved_status"])
        loop.dirty = False
        play_sfx("menu_confirm")
        return True, _BOT_COPY["saved_status"]
    _set_bot_status(loop, msg, is_error=True)
    return False, msg


def _reset_bot_defaults(loop: _BotMenuState) -> None:
    mode_key = _mode_key_from_dimension(loop.dimension)
    mode_settings = _bot_mode_settings(loop)
    mode_settings.update(_BOT_DEFAULTS[mode_key])
    loop.pending_reset_confirm = False
    loop.dirty = True
    _set_bot_status(
        loop,
        _BOT_COPY["reset_done_template"].format(mode_key=mode_key.upper()),
    )
    play_sfx("menu_move")


def _draw_status(
    screen: pygame.Surface,
    fonts,
    loop: _BotMenuState,
    *,
    y: int,
) -> None:
    if not loop.status:
        return
    width, height = screen.get_size()
    if y + fonts.hint_font.get_height() + 4 > height - 6:
        return
    color = (255, 150, 150) if loop.status_error else (170, 240, 170)
    status_text = fit_text(fonts.hint_font, loop.status, width - 36)
    surf = fonts.hint_font.render(status_text, True, color)
    screen.blit(surf, ((width - surf.get_width()) // 2, y + 2))


def _draw_hints(
    screen: pygame.Surface,
    fonts,
    *,
    start_y: int,
    hints: tuple[str, ...],
    loop: _BotMenuState,
) -> None:
    width, height = screen.get_size()
    line_h = fonts.hint_font.get_height() + 3
    max_lines = max(0, (height - start_y - 6) // max(1, line_h))
    status_slots = 1 if loop.status else 0
    hint_budget = max(0, max_lines - status_slots)
    y = start_y
    for line in hints[:hint_budget]:
        hint_text = fit_text(fonts.hint_font, line, width - 36)
        surf = fonts.hint_font.render(hint_text, True, _MUTED_COLOR)
        screen.blit(surf, ((width - surf.get_width()) // 2, y))
        y += surf.get_height() + 3
    _draw_status(screen, fonts, loop, y=y)


def _draw_bot_options_menu(
    screen: pygame.Surface,
    fonts,
    loop: _BotMenuState,
    *,
    hovered_target: _BotPointerTarget | None = None,
    pressed_target: _BotPointerTarget | None = None,
) -> tuple[_BotPointerTarget, ...]:
    draw_tron_menu_background(screen, top_color=_BG_TOP, bottom_color=_BG_BOTTOM)
    width, height = screen.get_size()
    title = fonts.title_font.render(
        format_menu_title(_BOT_COPY["title"]), True, _TEXT_COLOR
    )
    title_y = 40
    screen.blit(title, ((width - title.get_width()) // 2, title_y))
    back_rect = draw_corner_chip(
        screen,
        font=fonts.hint_font,
        text="Back",
        x=18,
        y=18,
        hovered=hovered_target is not None and hovered_target.kind == "back",
        pressed=pressed_target is not None and pressed_target.kind == "back",
    )

    values = _bot_values(loop)
    hint_lines = tuple(_BOT_COPY["hints"])
    line_h = fonts.hint_font.get_height() + 3
    bottom_lines = len(hint_lines) + (1 if loop.status else 0)
    panel_rect = standard_menu_panel_rect(
        screen,
        panel_w=min(720, max(320, width - 40)),
        panel_h=min(
            max(220, height - 170),
            max(220, 42 + (len(_BOT_MENU_ROWS) * (fonts.menu_font.get_height() + 12))),
        ),
        panel_top=title_y + title.get_height() + 18,
        bottom_reserved=bottom_lines * line_h,
    )
    draw_tron_panel(screen, rect=panel_rect)

    row_h = fonts.menu_font.get_height() + 12
    viewport_rect = pygame.Rect(
        panel_rect.x + 16,
        panel_rect.y + 12,
        panel_rect.width - 32,
        panel_rect.height - 20,
    )
    content_height = len(_BOT_MENU_ROWS) * row_h
    metrics = compute_vertical_scroll_metrics(
        viewport_rect=viewport_rect,
        content_height=content_height,
        scroll_offset=loop.scroll_offset,
    )
    selected_top = max(0, min(len(_BOT_MENU_ROWS) - 1, loop.selected)) * row_h
    loop.scroll_offset = ensure_scroll_offset_visible(
        metrics.scroll_offset,
        item_top=selected_top,
        item_bottom=selected_top + row_h,
        viewport_height=metrics.viewport_height,
        content_height=content_height,
    )
    metrics = compute_vertical_scroll_metrics(
        viewport_rect=viewport_rect,
        content_height=content_height,
        scroll_offset=loop.scroll_offset,
    )
    content_rect = viewport_rect.copy()
    content_rect.width -= metrics.reserved_width
    targets: list[_BotPointerTarget] = [
        _BotPointerTarget(kind="back", rect=back_rect.copy())
    ]
    previous_clip = screen.get_clip()
    screen.set_clip(viewport_rect)
    for idx, row in enumerate(_BOT_MENU_ROWS):
        draw_y = content_rect.y + (idx * row_h) - metrics.scroll_offset
        draw_rect = pygame.Rect(content_rect.x, draw_y, content_rect.width, row_h)
        if draw_rect.bottom < viewport_rect.y or draw_rect.top > viewport_rect.bottom:
            continue
        selected = idx == loop.selected
        color = _HIGHLIGHT_COLOR if selected else _TEXT_COLOR
        if selected:
            draw_selection_highlight(
                screen,
                rect=draw_rect.inflate(0, 4),
                border_radius=8,
            )
        label_left = draw_rect.x + 8
        label_right = draw_rect.right - 8
        value_text = values[idx]
        value_width = int(draw_rect.width * 0.34) if value_text else 0
        value_draw = fit_text(fonts.menu_font, value_text, value_width)
        value_surf = (
            fonts.menu_font.render(value_draw, True, color) if value_draw else None
        )
        value_x = label_right - (
            value_surf.get_width() if value_surf is not None else 0
        )
        label_width = max(
            64,
            (
                value_x - label_left - 10
                if value_surf is not None
                else draw_rect.width - 16
            ),
        )
        label_draw = fit_text(fonts.menu_font, row, label_width)
        label = fonts.menu_font.render(label_draw, True, color)
        screen.blit(label, (label_left, draw_rect.y))
        if value_surf is not None:
            screen.blit(value_surf, (value_x, draw_rect.y))
        targets.append(
            _BotPointerTarget(kind="item", rect=draw_rect.copy(), index=idx)
        )
    screen.set_clip(previous_clip)
    draw_vertical_scrollbar(screen, metrics=metrics)
    _draw_hints(
        screen,
        fonts,
        start_y=panel_rect.y + panel_rect.height + 10,
        hints=hint_lines,
        loop=loop,
    )
    return tuple(targets)


def _adjust_bot_value(loop: _BotMenuState, key: int) -> bool:
    nav_key = normalize_menu_navigation_key(key)
    if nav_key not in (pygame.K_LEFT, pygame.K_RIGHT):
        return False

    delta = -1 if nav_key == pygame.K_LEFT else 1
    if loop.selected == 0:
        idx = _BOT_DIMENSIONS.index(loop.dimension)
        loop.dimension = _BOT_DIMENSIONS[(idx + delta) % len(_BOT_DIMENSIONS)]
        play_sfx("menu_move")
        return True

    mode_settings = _bot_mode_settings(loop)
    if loop.selected == 1:
        value = mode_settings["bot_mode_index"] + delta
        mode_settings["bot_mode_index"] = max(
            0, min(len(BOT_MODE_OPTIONS) - 1, value)
        )
    elif loop.selected == 2:
        value = mode_settings["bot_algorithm_index"] + delta
        mode_settings["bot_algorithm_index"] = max(
            0, min(len(BOT_PLANNER_ALGORITHM_OPTIONS) - 1, value)
        )
    elif loop.selected == 3:
        value = mode_settings["bot_profile_index"] + delta
        mode_settings["bot_profile_index"] = max(
            0, min(len(BOT_PLANNER_PROFILE_OPTIONS) - 1, value)
        )
    elif loop.selected == 4:
        value = mode_settings["bot_speed_level"] + delta
        mode_settings["bot_speed_level"] = max(1, min(10, value))
    elif loop.selected == 5:
        value = mode_settings["bot_budget_ms"] + (delta * 2)
        mode_settings["bot_budget_ms"] = max(2, min(220, value))
    else:
        return False

    loop.dirty = True
    play_sfx("menu_move")
    return True


def _handle_bot_menu_confirm(loop: _BotMenuState) -> None:
    if loop.selected == 6:
        loop.pending_reset_confirm = False
        _save_bot_menu(loop)
        return
    if loop.selected == 7:
        if not loop.pending_reset_confirm:
            loop.pending_reset_confirm = True
            _set_bot_status(loop, _BOT_COPY["reset_confirm_enter"])
            return
        _reset_bot_defaults(loop)
        return
    if loop.selected == 8:
        loop.pending_reset_confirm = False
        loop.running = False


def _handle_bot_menu_exit_key(loop: _BotMenuState, *, key: int, nav_key: int) -> bool:
    if nav_key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
        loop.running = False
        return True
    return False


def _handle_bot_menu_key(loop: _BotMenuState, key: int) -> None:
    nav_key = normalize_menu_navigation_key(key)
    reset_trigger = key == pygame.K_F8 or (
        key in (pygame.K_RETURN, pygame.K_KP_ENTER) and loop.selected == 7
    )
    if not reset_trigger:
        loop.pending_reset_confirm = False

    if _handle_bot_menu_exit_key(loop, key=key, nav_key=nav_key):
        return
    if nav_key == pygame.K_UP:
        loop.selected = (loop.selected - 1) % len(_BOT_MENU_ROWS)
        play_sfx("menu_move")
        return
    if nav_key == pygame.K_DOWN:
        loop.selected = (loop.selected + 1) % len(_BOT_MENU_ROWS)
        play_sfx("menu_move")
        return
    if _adjust_bot_value(loop, key):
        return
    if key == pygame.K_F8:
        if not loop.pending_reset_confirm:
            loop.pending_reset_confirm = True
            _set_bot_status(loop, _BOT_COPY["reset_confirm_f8"])
            return
        _reset_bot_defaults(loop)
        return
    if key == pygame.K_F5:
        loop.pending_reset_confirm = False
        _save_bot_menu(loop)
        return
    if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        _handle_bot_menu_confirm(loop)


def run_bot_options_menu(  # noqa: C901
    screen: pygame.Surface,
    fonts,
    *,
    start_dimension: int,
) -> tuple[bool, str]:
    loop = _BotMenuState(
        payload=load_app_settings_payload(),
        dimension=start_dimension if start_dimension in _BOT_DIMENSIONS else 2,
    )
    clock = pygame.time.Clock()
    hovered_target: _BotPointerTarget | None = None
    pressed_target: _BotPointerTarget | None = None
    pointer_targets = _draw_bot_options_menu(
        screen,
        fonts,
        loop,
        hovered_target=hovered_target,
        pressed_target=pressed_target,
    )
    pygame.display.flip()

    def _pointer_target_at_pos(pos: tuple[int, int]) -> _BotPointerTarget | None:
        for target in reversed(pointer_targets):
            if target.rect.collidepoint(pos):
                return target
        return None

    while loop.running:
        _dt = clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                loop.running = False
                break
            if event.type == pygame.MOUSEMOTION:
                hovered_target = _pointer_target_at_pos(
                    getattr(event, "pos", (-1, -1))
                )
                if (
                    hovered_target is not None
                    and hovered_target.kind == "item"
                    and loop.selected != hovered_target.index
                ):
                    loop.selected = hovered_target.index
                    play_sfx("menu_move")
                continue
            if (
                event.type == pygame.MOUSEBUTTONDOWN
                and int(getattr(event, "button", 0)) == 1
            ):
                hovered_target = _pointer_target_at_pos(
                    getattr(event, "pos", (-1, -1))
                )
                if (
                    hovered_target is not None
                    and hovered_target.kind == "item"
                    and loop.selected != hovered_target.index
                ):
                    loop.selected = hovered_target.index
                    play_sfx("menu_move")
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
                if clicked_target.kind == "back":
                    loop.running = False
                    break
                if clicked_target.kind == "item":
                    loop.selected = clicked_target.index
                    _handle_bot_menu_confirm(loop)
                    if not loop.running:
                        break
                continue
            if event.type != pygame.KEYDOWN:
                continue
            _handle_bot_menu_key(loop, event.key)
            if not loop.running:
                break

        pointer_targets = _draw_bot_options_menu(
            screen,
            fonts,
            loop,
            hovered_target=hovered_target,
            pressed_target=pressed_target,
        )
        pygame.display.flip()

    if loop.dirty:
        return _save_bot_menu(loop)
    if loop.status:
        return (not loop.status_error), loop.status
    return True, "Bot options unchanged"
