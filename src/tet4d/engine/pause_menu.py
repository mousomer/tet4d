from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pygame

from .audio import AudioSettings
from .bot_options_menu import run_bot_options_menu
from .display import DisplaySettings
from .help_menu import run_help_menu
from .keybindings import (
    active_key_profile,
    cycle_key_profile,
    load_keybindings_file,
    save_keybindings_file,
)
from .keybindings_menu import run_keybindings_menu
from .launcher_settings import run_settings_hub_menu
from .runtime.menu_config import menu_items, pause_menu_id
from .menu_persistence import load_audio_payload, load_display_payload
from .menu_runner import ActionRegistry, MenuRunner
from tet4d.ui.pygame.ui_utils import draw_vertical_gradient, fit_text


PauseDecision = Literal["resume", "restart", "menu", "quit"]

_TEXT_COLOR = (230, 230, 240)
_HIGHLIGHT_COLOR = (255, 224, 128)
_MUTED_COLOR = (192, 200, 228)
_BG_TOP = (14, 18, 44)
_BG_BOTTOM = (4, 7, 20)

_PAUSE_MENU_ID = pause_menu_id()
_PAUSE_MENU_ITEMS = menu_items(_PAUSE_MENU_ID)
if any(item.get("type") != "action" for item in _PAUSE_MENU_ITEMS):
    raise RuntimeError("pause menu graph currently supports action items only")


@dataclass
class _PauseState:
    selected: int = 0
    running: bool = True
    decision: PauseDecision = "resume"
    status: str = ""
    status_error: bool = False


def _draw_clamped_hint_block(
    screen: pygame.Surface,
    font: pygame.font.Font,
    *,
    start_y: int,
    lines: tuple[str, ...],
    color: tuple[int, int, int],
    status: str,
    status_error: bool,
) -> None:
    width, height = screen.get_size()
    line_h = font.get_height() + 3
    max_lines = max(0, (height - start_y - 6) // max(1, line_h))
    status_slots = 1 if status else 0
    hint_budget = max(0, max_lines - status_slots)
    y = start_y
    for line in lines[:hint_budget]:
        text = fit_text(font, line, width - 24)
        surf = font.render(text, True, color)
        screen.blit(surf, ((width - surf.get_width()) // 2, y))
        y += surf.get_height() + 3

    if status and y + line_h <= height - 6:
        status_color = (255, 150, 150) if status_error else (170, 240, 170)
        status_text = fit_text(font, status, width - 24)
        surf = font.render(status_text, True, status_color)
        screen.blit(surf, ((width - surf.get_width()) // 2, y + 2))


def _draw_list_menu_panel(
    screen: pygame.Surface,
    fonts,
    *,
    title: str,
    subtitle: str,
    rows: tuple[str, ...],
    selected_index: int,
    values: tuple[str, ...],
    hints: tuple[str, ...],
    status: str,
    status_error: bool,
    panel_w: int = 660,
) -> None:
    draw_vertical_gradient(screen, _BG_TOP, _BG_BOTTOM)
    width, height = screen.get_size()
    title_surf = fonts.title_font.render(title, True, _TEXT_COLOR)
    subtitle_surf = fonts.hint_font.render(
        fit_text(fonts.hint_font, subtitle, width - 24), True, _MUTED_COLOR
    )
    title_y = 40
    subtitle_y = title_y + title_surf.get_height() + 8
    screen.blit(title_surf, ((width - title_surf.get_width()) // 2, title_y))
    screen.blit(subtitle_surf, ((width - subtitle_surf.get_width()) // 2, subtitle_y))

    panel_w = min(panel_w, max(320, width - 40))
    line_h = fonts.hint_font.get_height() + 3
    panel_top = subtitle_y + subtitle_surf.get_height() + 10
    bottom_lines = len(hints) + (1 if status else 0)
    panel_max_h = max(150, height - panel_top - (bottom_lines * line_h) - 10)
    row_h = min(
        42,
        max(fonts.menu_font.get_height() + 8, (panel_max_h - 36) // max(1, len(rows))),
    )
    panel_h = min(panel_max_h, 36 + len(rows) * row_h)
    panel_x = (width - panel_w) // 2
    panel_y = max(
        panel_top,
        min((height - panel_h) // 2, height - panel_h - (bottom_lines * line_h) - 8),
    )
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (0, 0, 0, 150), panel.get_rect(), border_radius=12)
    screen.blit(panel, (panel_x, panel_y))

    y = panel_y + 14
    option_bottom = panel_y + panel_h - 8
    label_left = panel_x + 20
    label_right = panel_x + panel_w - 20
    for idx, row in enumerate(rows):
        if y + fonts.menu_font.get_height() > option_bottom:
            break
        selected = idx == selected_index
        color = _HIGHLIGHT_COLOR if selected else _TEXT_COLOR
        if selected:
            hi = pygame.Surface(
                (panel_w - 28, fonts.menu_font.get_height() + 10), pygame.SRCALPHA
            )
            pygame.draw.rect(hi, (255, 255, 255, 38), hi.get_rect(), border_radius=8)
            screen.blit(hi, (panel_x + 14, y - 3))
        value_text = values[idx] if idx < len(values) else ""
        value_width = int(panel_w * 0.34) if value_text else 0
        value_draw = fit_text(fonts.menu_font, value_text, value_width)
        value_surf = (
            fonts.menu_font.render(value_draw, True, color) if value_draw else None
        )
        value_x = label_right - (
            value_surf.get_width() if value_surf is not None else 0
        )
        label_width = max(
            64, value_x - label_left - 10 if value_surf is not None else panel_w - 52
        )
        label_draw = fit_text(fonts.menu_font, row, label_width)
        label = fonts.menu_font.render(label_draw, True, color)
        screen.blit(label, (label_left, y))
        if value_surf is not None:
            screen.blit(value_surf, (value_x, y))
        y += row_h

    _draw_clamped_hint_block(
        screen,
        fonts.hint_font,
        start_y=panel_y + panel_h + 8,
        lines=hints,
        color=_MUTED_COLOR,
        status=status,
        status_error=status_error,
    )


def _pause_menu_values(dimension: int) -> tuple[str, ...]:
    profile = active_key_profile()
    action_values = {
        "settings": "Audio + Display + Analytics",
        "bot_options": f"{dimension}D planner/options",
        "keybindings": "General + 2D/3D/4D scopes",
        "profile_prev": profile,
        "profile_next": profile,
        "save_bindings": profile,
        "load_bindings": profile,
        "help": f"{dimension}D guidance",
    }
    return tuple(action_values.get(action, "") for action in _PAUSE_ACTION_CODES)


def _draw_pause_menu(
    screen: pygame.Surface,
    fonts,
    state: _PauseState,
    *,
    dimension: int,
    title: str,
) -> None:
    _draw_list_menu_panel(
        screen,
        fonts,
        title=title,
        subtitle=f"{dimension}D in-game controls and settings",
        rows=_PAUSE_ROWS,
        selected_index=state.selected,
        values=_pause_menu_values(dimension),
        hints=("Up/Down select   Enter apply", "Esc resume"),
        status=state.status,
        status_error=state.status_error,
    )


def _audio_settings_from_payload() -> AudioSettings:
    audio = load_audio_payload()
    return AudioSettings(
        master_volume=max(0.0, min(1.0, float(audio["master_volume"]))),
        sfx_volume=max(0.0, min(1.0, float(audio["sfx_volume"]))),
        mute=bool(audio["mute"]),
    )


def _display_settings_from_payload() -> DisplaySettings:
    display = load_display_payload()
    return DisplaySettings(
        fullscreen=bool(display["fullscreen"]),
        windowed_size=(
            int(display["windowed_size"][0]),
            int(display["windowed_size"][1]),
        ),
    )


_PAUSE_ROWS: tuple[str, ...] = tuple(item["label"] for item in _PAUSE_MENU_ITEMS)
_PAUSE_ACTION_CODES: tuple[str, ...] = tuple(
    item["action_id"] for item in _PAUSE_MENU_ITEMS
)
_SUPPORTED_PAUSE_ACTIONS = {
    "resume",
    "restart",
    "settings",
    "bot_options",
    "keybindings",
    "profile_prev",
    "profile_next",
    "save_bindings",
    "load_bindings",
    "help",
    "menu",
    "quit",
}

if len(_PAUSE_ROWS) != len(_PAUSE_ACTION_CODES):
    raise RuntimeError(
        f"pause menu labels length ({len(_PAUSE_ROWS)}) must match pause action count ({len(_PAUSE_ACTION_CODES)})"
    )
unknown_pause_actions = sorted(set(_PAUSE_ACTION_CODES) - _SUPPORTED_PAUSE_ACTIONS)
if unknown_pause_actions:
    raise RuntimeError(
        "pause menu contains unsupported actions: " + ", ".join(unknown_pause_actions)
    )


def _set_pause_decision(state: _PauseState, decision: PauseDecision) -> None:
    state.decision = decision
    state.running = False


def _set_pause_status(state: _PauseState, ok: bool, message: str) -> None:
    state.status = message
    state.status_error = not ok


def _run_pause_settings_hub(
    screen: pygame.Surface,
    fonts,
    state: _PauseState,
) -> tuple[pygame.Surface, bool]:
    result = run_settings_hub_menu(
        screen,
        fonts,
        audio_settings=_audio_settings_from_payload(),
        display_settings=_display_settings_from_payload(),
    )
    if not result.keep_running:
        _set_pause_status(state, False, "Settings exited application loop")
        return result.screen, False
    _set_pause_status(state, True, "Returned from settings")
    return result.screen, True


def _handle_pause_profile_cycle(state: _PauseState, step: int) -> None:
    ok, msg, _profile = cycle_key_profile(step)
    _set_pause_status(state, ok, msg)


def _handle_pause_bindings_io(
    state: _PauseState, dimension: int, *, save: bool
) -> None:
    if save:
        ok, msg = save_keybindings_file(dimension)
    else:
        ok, msg = load_keybindings_file(dimension)
    _set_pause_status(state, ok, msg)


def _handle_pause_action(
    action: str,
    screen: pygame.Surface,
    fonts,
    state: _PauseState,
    *,
    dimension: int,
) -> tuple[pygame.Surface, bool]:
    if action in {"resume", "restart", "menu", "quit"}:
        _set_pause_decision(state, action)
        return screen, True
    if action == "settings":
        return _run_pause_settings_hub(screen, fonts, state)
    if action == "bot_options":
        ok, msg = run_bot_options_menu(screen, fonts, start_dimension=dimension)
        _set_pause_status(state, ok, msg)
        return screen, True
    if action == "keybindings":
        run_keybindings_menu(screen, fonts, dimension=dimension, scope="general")
        _set_pause_status(state, True, "Returned from keybindings setup")
        return screen, True
    if action == "profile_prev":
        _handle_pause_profile_cycle(state, -1)
        return screen, True
    if action == "profile_next":
        _handle_pause_profile_cycle(state, 1)
        return screen, True
    if action == "save_bindings":
        _handle_pause_bindings_io(state, dimension, save=True)
        return screen, True
    if action == "load_bindings":
        _handle_pause_bindings_io(state, dimension, save=False)
        return screen, True
    if action == "help":
        screen = run_help_menu(
            screen, fonts, dimension=dimension, context_label="Pause Menu"
        )
        _set_pause_status(state, True, "Returned from help")
        return screen, True
    return screen, True


def _handle_pause_row(
    screen: pygame.Surface,
    fonts,
    state: _PauseState,
    *,
    dimension: int,
) -> tuple[pygame.Surface, bool]:
    safe_index = max(0, min(len(_PAUSE_ACTION_CODES) - 1, state.selected))
    action = _PAUSE_ACTION_CODES[safe_index]
    return _handle_pause_action(action, screen, fonts, state, dimension=dimension)


def _pause_action_dispatcher(
    action: str,
    *,
    state: _PauseState,
    dimension: int,
    fonts,
    screen_ref: list[pygame.Surface],
) -> bool:
    new_screen, keep_running = _handle_pause_action(
        action,
        screen_ref[0],
        fonts,
        state,
        dimension=dimension,
    )
    screen_ref[0] = new_screen
    if not keep_running:
        state.decision = "quit"
        state.running = False
        return True
    if not state.running:
        return True
    return False


def _pause_root_escape(state: _PauseState) -> bool:
    _set_pause_decision(state, "resume")
    return True


def _pause_quit_event(state: _PauseState) -> bool:
    _set_pause_decision(state, "quit")
    return True


def run_pause_menu(
    screen: pygame.Surface,
    fonts,
    *,
    dimension: int,
) -> tuple[PauseDecision, pygame.Surface]:
    state = _PauseState()
    screen_ref = [screen]

    registry = ActionRegistry()
    for action in _PAUSE_ACTION_CODES:
        registry.register(
            action,
            lambda action_id=action: _pause_action_dispatcher(
                action_id,
                state=state,
                dimension=dimension,
                fonts=fonts,
                screen_ref=screen_ref,
            ),
        )

    def _render_pause_menu(
        _menu_id: str,
        title: str,
        _items: tuple[dict[str, str], ...],
        selected: int,
        _depth: int,
    ) -> None:
        state.selected = selected
        _draw_pause_menu(
            screen_ref[0],
            fonts,
            state,
            dimension=dimension,
            title=title,
        )
        pygame.display.flip()

    runner = MenuRunner(
        menus={
            _PAUSE_MENU_ID: {
                "title": "Pause Menu",
                "items": _PAUSE_MENU_ITEMS,
            }
        },
        start_menu_id=_PAUSE_MENU_ID,
        action_registry=registry,
        render_menu=_render_pause_menu,
        on_root_escape=lambda: _pause_root_escape(state),
        on_quit_event=lambda: _pause_quit_event(state),
        initial_selected={_PAUSE_MENU_ID: 0},
    )
    runner.run()

    return state.decision, screen_ref[0]
