from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pygame

from .audio import set_audio_settings
from .bot_options_menu import run_bot_options_menu
from .display import DisplaySettings, apply_display_mode, normalize_display_settings
from .help_menu import run_help_menu
from .keybindings import (
    active_key_profile,
    cycle_key_profile,
    load_keybindings_file,
    save_keybindings_file,
)
from .keybindings_menu import run_keybindings_menu
from .menu_config import default_settings_payload, pause_menu_rows, pause_settings_rows
from .menu_model import cycle_index, is_confirm_key
from .menu_persistence import (
    load_audio_payload,
    load_display_payload,
    persist_audio_payload,
    persist_display_payload,
)
from .ui_utils import draw_vertical_gradient, fit_text


PauseDecision = Literal["resume", "restart", "menu", "quit"]

_TEXT_COLOR = (230, 230, 240)
_HIGHLIGHT_COLOR = (255, 224, 128)
_MUTED_COLOR = (192, 200, 228)
_BG_TOP = (14, 18, 44)
_BG_BOTTOM = (4, 7, 20)

_PAUSE_ROWS: tuple[str, ...] = pause_menu_rows()
_SETTINGS_ROWS: tuple[str, ...] = pause_settings_rows()


@dataclass
class _PauseState:
    selected: int = 0
    running: bool = True
    decision: PauseDecision = "resume"
    status: str = ""
    status_error: bool = False


@dataclass
class _SettingsState:
    master_volume: float
    sfx_volume: float
    mute: bool
    fullscreen: bool
    windowed_size: tuple[int, int]
    selected: int = 0
    running: bool = True
    status: str = ""
    status_error: bool = False
    pending_reset_confirm: bool = False


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
    subtitle_surf = fonts.hint_font.render(fit_text(fonts.hint_font, subtitle, width - 24), True, _MUTED_COLOR)
    title_y = 40
    subtitle_y = title_y + title_surf.get_height() + 8
    screen.blit(title_surf, ((width - title_surf.get_width()) // 2, title_y))
    screen.blit(subtitle_surf, ((width - subtitle_surf.get_width()) // 2, subtitle_y))

    panel_w = min(panel_w, max(320, width - 40))
    line_h = fonts.hint_font.get_height() + 3
    panel_top = subtitle_y + subtitle_surf.get_height() + 10
    bottom_lines = len(hints) + (1 if status else 0)
    panel_max_h = max(150, height - panel_top - (bottom_lines * line_h) - 10)
    row_h = min(42, max(fonts.menu_font.get_height() + 8, (panel_max_h - 36) // max(1, len(rows))))
    panel_h = min(panel_max_h, 36 + len(rows) * row_h)
    panel_x = (width - panel_w) // 2
    panel_y = max(panel_top, min((height - panel_h) // 2, height - panel_h - (bottom_lines * line_h) - 8))
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
            hi = pygame.Surface((panel_w - 28, fonts.menu_font.get_height() + 10), pygame.SRCALPHA)
            pygame.draw.rect(hi, (255, 255, 255, 38), hi.get_rect(), border_radius=8)
            screen.blit(hi, (panel_x + 14, y - 3))
        value_text = values[idx] if idx < len(values) else ""
        value_width = int(panel_w * 0.34) if value_text else 0
        value_draw = fit_text(fonts.menu_font, value_text, value_width)
        value_surf = fonts.menu_font.render(value_draw, True, color) if value_draw else None
        value_x = label_right - (value_surf.get_width() if value_surf is not None else 0)
        label_width = max(64, value_x - label_left - 10 if value_surf is not None else panel_w - 52)
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
    return (
        "",
        "",
        "Audio + Display",
        f"{dimension}D planner/options",
        f"{dimension}D profile editor",
        profile,
        profile,
        profile,
        profile,
        f"{dimension}D controls",
        "",
        "",
    )


def _draw_pause_menu(screen: pygame.Surface, fonts, state: _PauseState, *, dimension: int) -> None:
    _draw_list_menu_panel(
        screen,
        fonts,
        title="Pause Menu",
        subtitle=f"{dimension}D in-game controls and settings",
        rows=_PAUSE_ROWS,
        selected_index=state.selected,
        values=_pause_menu_values(dimension),
        hints=("Up/Down select   Enter apply", "Esc resume"),
        status=state.status,
        status_error=state.status_error,
    )


def _load_settings_state() -> _SettingsState:
    audio = load_audio_payload()
    display = load_display_payload()
    return _SettingsState(
        master_volume=max(0.0, min(1.0, float(audio["master_volume"]))),
        sfx_volume=max(0.0, min(1.0, float(audio["sfx_volume"]))),
        mute=bool(audio["mute"]),
        fullscreen=bool(display["fullscreen"]),
        windowed_size=(int(display["windowed_size"][0]), int(display["windowed_size"][1])),
    )


def _settings_defaults() -> _SettingsState:
    defaults = default_settings_payload()
    audio = defaults.get("audio", {})
    display = defaults.get("display", {})
    return _SettingsState(
        master_volume=max(0.0, min(1.0, float(audio.get("master_volume", 0.8)))),
        sfx_volume=max(0.0, min(1.0, float(audio.get("sfx_volume", 0.7)))),
        mute=bool(audio.get("mute", False)),
        fullscreen=bool(display.get("fullscreen", False)),
        windowed_size=(
            int(display.get("windowed_size", [1200, 760])[0]),
            int(display.get("windowed_size", [1200, 760])[1]),
        ),
    )


def _settings_values(state: _SettingsState) -> tuple[str, ...]:
    width, height = state.windowed_size
    return (
        f"{int(state.master_volume * 100)}%",
        f"{int(state.sfx_volume * 100)}%",
        "ON" if state.mute else "OFF",
        "ON" if state.fullscreen else "OFF",
        str(width),
        str(height),
        "",
        "",
        "",
        "",
    )


def _draw_settings_menu(screen: pygame.Surface, fonts, state: _SettingsState) -> None:
    _draw_list_menu_panel(
        screen,
        fonts,
        title="Pause Settings",
        subtitle="Audio + Display",
        rows=_SETTINGS_ROWS,
        selected_index=state.selected,
        values=_settings_values(state),
        hints=("Left/Right adjust values   Enter apply", "Esc back"),
        status=state.status,
        status_error=state.status_error,
    )


def _apply_audio_preview(state: _SettingsState) -> None:
    set_audio_settings(
        master_volume=state.master_volume,
        sfx_volume=state.sfx_volume,
        mute=state.mute,
    )


def _apply_display_preview(_screen: pygame.Surface, state: _SettingsState) -> pygame.Surface:
    settings = normalize_display_settings(
        DisplaySettings(
            fullscreen=state.fullscreen,
            windowed_size=state.windowed_size,
        )
    )
    state.windowed_size = settings.windowed_size
    return apply_display_mode(settings, preferred_windowed_size=settings.windowed_size)


def _adjust_settings_value(state: _SettingsState, key: int) -> bool:
    if key not in (pygame.K_LEFT, pygame.K_RIGHT):
        return False
    delta = -1 if key == pygame.K_LEFT else 1
    if state.selected == 0:
        state.master_volume = max(0.0, min(1.0, state.master_volume + delta * 0.02))
        return True
    if state.selected == 1:
        state.sfx_volume = max(0.0, min(1.0, state.sfx_volume + delta * 0.02))
        return True
    if state.selected == 3:
        state.fullscreen = not state.fullscreen
        return True
    if state.selected == 4:
        width, height = state.windowed_size
        state.windowed_size = (max(640, width + delta * 40), height)
        return True
    if state.selected == 5:
        width, height = state.windowed_size
        state.windowed_size = (width, max(480, height + delta * 40))
        return True
    return False


def _save_settings_state(state: _SettingsState) -> tuple[bool, str]:
    ok_audio, msg_audio = persist_audio_payload(
        master_volume=state.master_volume,
        sfx_volume=state.sfx_volume,
        mute=state.mute,
    )
    ok_display, msg_display = persist_display_payload(
        fullscreen=state.fullscreen,
        windowed_size=state.windowed_size,
    )
    if not ok_audio:
        return False, msg_audio
    if not ok_display:
        return False, msg_display
    return True, "Saved audio/display settings"


def _set_settings_status(state: _SettingsState, message: str, *, is_error: bool = False) -> None:
    state.status = message
    state.status_error = is_error


def _handle_settings_navigation(state: _SettingsState, key: int) -> bool:
    if key == pygame.K_ESCAPE:
        state.pending_reset_confirm = False
        state.running = False
        return True
    if key == pygame.K_UP:
        state.pending_reset_confirm = False
        state.selected = cycle_index(state.selected, len(_SETTINGS_ROWS), -1)
        return True
    if key == pygame.K_DOWN:
        state.pending_reset_confirm = False
        state.selected = cycle_index(state.selected, len(_SETTINGS_ROWS), 1)
        return True
    return False


def _handle_settings_adjustment(
    screen: pygame.Surface,
    state: _SettingsState,
    key: int,
) -> tuple[pygame.Surface, bool]:
    if not _adjust_settings_value(state, key):
        return screen, False
    state.pending_reset_confirm = False
    _apply_audio_preview(state)
    if state.selected in (3, 4, 5):
        screen = _apply_display_preview(screen, state)
    return screen, True


def _reset_settings_to_defaults(
    screen: pygame.Surface,
    state: _SettingsState,
) -> pygame.Surface:
    defaults = _settings_defaults()
    state.master_volume = defaults.master_volume
    state.sfx_volume = defaults.sfx_volume
    state.mute = defaults.mute
    state.fullscreen = defaults.fullscreen
    state.windowed_size = defaults.windowed_size
    state.pending_reset_confirm = False
    _apply_audio_preview(state)
    screen = _apply_display_preview(screen, state)
    _set_settings_status(state, "Reset settings to defaults (not saved yet)")
    return screen


def _handle_settings_confirm(
    screen: pygame.Surface,
    state: _SettingsState,
    key: int,
) -> tuple[pygame.Surface, bool]:
    if not is_confirm_key(key):
        return screen, False
    if state.selected == 2:
        state.pending_reset_confirm = False
        state.mute = not state.mute
        _apply_audio_preview(state)
        return screen, True
    if state.selected == 6:
        state.pending_reset_confirm = False
        return _apply_display_preview(screen, state), True
    if state.selected == 7:
        state.pending_reset_confirm = False
        ok, msg = _save_settings_state(state)
        _set_settings_status(state, msg, is_error=not ok)
        return screen, True
    if state.selected == 8:
        if not state.pending_reset_confirm:
            state.pending_reset_confirm = True
            _set_settings_status(state, "Press Enter on Reset defaults again to confirm")
            return screen, True
        return _reset_settings_to_defaults(screen, state), True
    if state.selected == 9:
        state.pending_reset_confirm = False
        state.running = False
        return screen, True
    return screen, False


def run_pause_settings_menu(screen: pygame.Surface, fonts) -> tuple[pygame.Surface, bool]:
    state = _load_settings_state()
    _apply_audio_preview(state)
    clock = pygame.time.Clock()

    while state.running:
        _dt = clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return screen, False
            if event.type != pygame.KEYDOWN:
                continue
            key = event.key
            if _handle_settings_navigation(state, key):
                break
            screen, handled = _handle_settings_adjustment(screen, state, key)
            if handled:
                break
            screen, handled = _handle_settings_confirm(screen, state, key)
            if handled:
                break

        if not state.running:
            break
        _draw_settings_menu(screen, fonts, state)
        pygame.display.flip()

    return screen, True


_PAUSE_ACTION_CODES: tuple[str, ...] = (
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
)

if len(_PAUSE_ROWS) != len(_PAUSE_ACTION_CODES):
    raise RuntimeError(
        f"pause_menu_rows length ({len(_PAUSE_ROWS)}) must match pause action count ({len(_PAUSE_ACTION_CODES)})"
    )


def _set_pause_decision(state: _PauseState, decision: PauseDecision) -> None:
    state.decision = decision
    state.running = False


def _set_pause_status(state: _PauseState, ok: bool, message: str) -> None:
    state.status = message
    state.status_error = not ok


def _handle_pause_profile_cycle(state: _PauseState, step: int) -> None:
    ok, msg, _profile = cycle_key_profile(step)
    _set_pause_status(state, ok, msg)


def _handle_pause_bindings_io(state: _PauseState, dimension: int, *, save: bool) -> None:
    if save:
        ok, msg = save_keybindings_file(dimension)
    else:
        ok, msg = load_keybindings_file(dimension)
    _set_pause_status(state, ok, msg)


def _handle_pause_row(
    screen: pygame.Surface,
    fonts,
    state: _PauseState,
    *,
    dimension: int,
) -> tuple[pygame.Surface, bool]:
    safe_index = max(0, min(len(_PAUSE_ACTION_CODES) - 1, state.selected))
    action = _PAUSE_ACTION_CODES[safe_index]

    if action in {"resume", "restart", "menu", "quit"}:
        _set_pause_decision(state, action)
        return screen, True
    if action == "settings":
        return run_pause_settings_menu(screen, fonts)
    if action == "bot_options":
        ok, msg = run_bot_options_menu(screen, fonts, start_dimension=dimension)
        _set_pause_status(state, ok, msg)
        return screen, True
    if action == "keybindings":
        run_keybindings_menu(screen, fonts, dimension=dimension, scope=f"{dimension}d")
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
        screen = run_help_menu(screen, fonts, dimension=dimension, context_label="Pause Menu")
        _set_pause_status(state, True, "Returned from help")
        return screen, True
    return screen, True


def _handle_pause_key(
    screen: pygame.Surface,
    fonts,
    state: _PauseState,
    *,
    dimension: int,
    key: int,
) -> tuple[pygame.Surface, bool]:
    if key == pygame.K_ESCAPE:
        state.decision = "resume"
        state.running = False
        return screen, True
    if key == pygame.K_UP:
        state.selected = cycle_index(state.selected, len(_PAUSE_ROWS), -1)
        return screen, False
    if key == pygame.K_DOWN:
        state.selected = cycle_index(state.selected, len(_PAUSE_ROWS), 1)
        return screen, False
    if not is_confirm_key(key):
        return screen, False
    screen, keep_running = _handle_pause_row(
        screen,
        fonts,
        state,
        dimension=dimension,
    )
    if not keep_running:
        state.decision = "quit"
        state.running = False
        return screen, True
    return screen, False


def run_pause_menu(
    screen: pygame.Surface,
    fonts,
    *,
    dimension: int,
) -> tuple[PauseDecision, pygame.Surface]:
    state = _PauseState()
    clock = pygame.time.Clock()

    while state.running:
        _dt = clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit", screen
            if event.type != pygame.KEYDOWN:
                continue
            screen, done = _handle_pause_key(
                screen,
                fonts,
                state,
                dimension=dimension,
                key=event.key,
            )
            if done:
                return state.decision, screen
            if not state.running:
                break

        if not state.running:
            break
        _draw_pause_menu(screen, fonts, state, dimension=dimension)
        pygame.display.flip()

    return state.decision, screen
