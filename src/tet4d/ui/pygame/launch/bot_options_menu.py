from __future__ import annotations

from dataclasses import dataclass

import pygame

import tet4d.engine.api as engine_api
from tet4d.ui.pygame.audio import play_sfx
from tet4d.ai.playbot.types import (
    bot_mode_from_index,
    bot_planner_algorithm_from_index,
    bot_planner_profile_from_index,
)
from tet4d.ui.pygame.ui_utils import draw_vertical_gradient


_BG_TOP = (14, 18, 44)
_BG_BOTTOM = (4, 7, 20)
_TEXT_COLOR = (232, 232, 240)
_HIGHLIGHT_COLOR = (255, 224, 128)
_MUTED_COLOR = (192, 200, 228)

_BOT_DIMENSIONS = (2, 3, 4)
_BOT_MENU_ROWS = engine_api.bot_options_rows_runtime()
_BOT_DEFAULTS = engine_api.bot_defaults_by_mode_runtime()


@dataclass
class _BotMenuState:
    payload: dict[str, object]
    dimension: int = 2
    selected: int = 0
    status: str = ""
    status_error: bool = False
    pending_reset_confirm: bool = False
    dirty: bool = False
    running: bool = True


def _draw_gradient(surface: pygame.Surface) -> None:
    draw_vertical_gradient(surface, _BG_TOP, _BG_BOTTOM)


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
        engine_api.bot_mode_label(bot_mode),
        engine_api.bot_planner_algorithm_label(algorithm),
        engine_api.bot_planner_profile_label(profile),
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
    ok, msg = engine_api.save_menu_payload_runtime(loop.payload)
    if ok:
        _set_bot_status(loop, "Saved bot options")
        loop.dirty = False
        play_sfx("menu_confirm")
        return True, "Saved bot options"
    _set_bot_status(loop, msg, is_error=True)
    return False, msg


def _reset_bot_defaults(loop: _BotMenuState) -> None:
    mode_key = _mode_key_from_dimension(loop.dimension)
    mode_settings = _bot_mode_settings(loop)
    mode_settings.update(_BOT_DEFAULTS[mode_key])
    loop.pending_reset_confirm = False
    loop.dirty = True
    _set_bot_status(loop, f"Reset {mode_key.upper()} bot settings (not saved yet)")
    play_sfx("menu_move")


def _draw_bot_options_menu(screen: pygame.Surface, fonts, loop: _BotMenuState) -> None:
    _draw_gradient(screen)
    width, height = screen.get_size()
    title = fonts.title_font.render("Bot Options", True, _TEXT_COLOR)
    subtitle = fonts.hint_font.render(
        "Dimension-specific bot controls in one place", True, _MUTED_COLOR
    )
    screen.blit(title, ((width - title.get_width()) // 2, 40))
    screen.blit(subtitle, ((width - subtitle.get_width()) // 2, 88))

    values = _bot_values(loop)
    panel_w = min(640, width - 40)
    panel_h = 92 + len(_BOT_MENU_ROWS) * 46
    panel_x = (width - panel_w) // 2
    panel_y = max(132, (height - panel_h) // 2)
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (0, 0, 0, 150), panel.get_rect(), border_radius=12)
    screen.blit(panel, (panel_x, panel_y))

    y = panel_y + 24
    for idx, row in enumerate(_BOT_MENU_ROWS):
        selected = idx == loop.selected
        color = _HIGHLIGHT_COLOR if selected else _TEXT_COLOR
        if selected:
            hi = pygame.Surface(
                (panel_w - 28, fonts.menu_font.get_height() + 8), pygame.SRCALPHA
            )
            pygame.draw.rect(hi, (255, 255, 255, 38), hi.get_rect(), border_radius=8)
            screen.blit(hi, (panel_x + 14, y - 3))
        label = fonts.menu_font.render(row, True, color)
        screen.blit(label, (panel_x + 20, y))
        if values[idx]:
            value = fonts.menu_font.render(values[idx], True, color)
            screen.blit(value, (panel_x + panel_w - value.get_width() - 20, y))
        y += 46

    hint_lines = (
        "Left/Right adjust values   Up/Down select",
        "F5 save   F8 reset defaults   Esc back",
    )
    hy = panel_y + panel_h + 12
    for line in hint_lines:
        surf = fonts.hint_font.render(line, True, _MUTED_COLOR)
        screen.blit(surf, ((width - surf.get_width()) // 2, hy))
        hy += surf.get_height() + 3

    if loop.status:
        color = (255, 150, 150) if loop.status_error else (170, 240, 170)
        surf = fonts.hint_font.render(loop.status, True, color)
        screen.blit(surf, ((width - surf.get_width()) // 2, hy + 2))


def _adjust_bot_value(loop: _BotMenuState, key: int) -> bool:
    if key not in (pygame.K_LEFT, pygame.K_RIGHT):
        return False

    delta = -1 if key == pygame.K_LEFT else 1
    if loop.selected == 0:
        idx = _BOT_DIMENSIONS.index(loop.dimension)
        loop.dimension = _BOT_DIMENSIONS[(idx + delta) % len(_BOT_DIMENSIONS)]
        play_sfx("menu_move")
        return True

    mode_settings = _bot_mode_settings(loop)
    if loop.selected == 1:
        value = mode_settings["bot_mode_index"] + delta
        mode_settings["bot_mode_index"] = max(
            0, min(len(engine_api.BOT_MODE_OPTIONS) - 1, value)
        )
    elif loop.selected == 2:
        value = mode_settings["bot_algorithm_index"] + delta
        mode_settings["bot_algorithm_index"] = max(
            0, min(len(engine_api.BOT_PLANNER_ALGORITHM_OPTIONS) - 1, value)
        )
    elif loop.selected == 3:
        value = mode_settings["bot_profile_index"] + delta
        mode_settings["bot_profile_index"] = max(
            0, min(len(engine_api.BOT_PLANNER_PROFILE_OPTIONS) - 1, value)
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
            _set_bot_status(loop, "Press Enter on Reset defaults again to confirm")
            return
        _reset_bot_defaults(loop)
        return
    if loop.selected == 8:
        loop.pending_reset_confirm = False
        loop.running = False


def _handle_bot_menu_key(loop: _BotMenuState, key: int) -> None:
    reset_trigger = key == pygame.K_F8 or (
        key in (pygame.K_RETURN, pygame.K_KP_ENTER) and loop.selected == 7
    )
    if not reset_trigger:
        loop.pending_reset_confirm = False

    if key == pygame.K_ESCAPE:
        loop.running = False
        return
    if key == pygame.K_UP:
        loop.selected = (loop.selected - 1) % len(_BOT_MENU_ROWS)
        play_sfx("menu_move")
        return
    if key == pygame.K_DOWN:
        loop.selected = (loop.selected + 1) % len(_BOT_MENU_ROWS)
        play_sfx("menu_move")
        return
    if _adjust_bot_value(loop, key):
        return
    if key == pygame.K_F8:
        if not loop.pending_reset_confirm:
            loop.pending_reset_confirm = True
            _set_bot_status(loop, "Press F8 again to confirm reset defaults")
            return
        _reset_bot_defaults(loop)
        return
    if key == pygame.K_F5:
        loop.pending_reset_confirm = False
        _save_bot_menu(loop)
        return
    if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        _handle_bot_menu_confirm(loop)


def run_bot_options_menu(
    screen: pygame.Surface,
    fonts,
    *,
    start_dimension: int,
) -> tuple[bool, str]:
    loop = _BotMenuState(
        payload=engine_api.load_menu_payload_runtime(),
        dimension=start_dimension if start_dimension in _BOT_DIMENSIONS else 2,
    )
    clock = pygame.time.Clock()

    while loop.running:
        _dt = clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                loop.running = False
                break
            if event.type != pygame.KEYDOWN:
                continue
            _handle_bot_menu_key(loop, event.key)
            if not loop.running:
                break

        _draw_bot_options_menu(screen, fonts, loop)
        pygame.display.flip()

    if loop.dirty:
        return _save_bot_menu(loop)
    if loop.status:
        return (not loop.status_error), loop.status
    return True, "Bot options unchanged"
