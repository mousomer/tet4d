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
from .menu_config import default_settings_payload
from .menu_gif_guides import draw_translation_rotation_guides
from .menu_model import cycle_index, is_confirm_key
from .menu_persistence import (
    load_audio_payload,
    load_display_payload,
    persist_audio_payload,
    persist_display_payload,
)


PauseDecision = Literal["resume", "restart", "menu", "quit"]

_TEXT_COLOR = (230, 230, 240)
_HIGHLIGHT_COLOR = (255, 224, 128)
_MUTED_COLOR = (192, 200, 228)
_BG_TOP = (14, 18, 44)
_BG_BOTTOM = (4, 7, 20)

_PAUSE_ROWS: tuple[str, ...] = (
    "Resume",
    "Restart Run",
    "Settings",
    "Bot Options",
    "Keybindings Setup",
    "Profile Previous",
    "Profile Next",
    "Save Keybindings",
    "Load Keybindings",
    "Help",
    "Back To Main Menu",
    "Quit",
)

_SETTINGS_ROWS: tuple[str, ...] = (
    "Master volume",
    "SFX volume",
    "Mute",
    "Fullscreen",
    "Window width",
    "Window height",
    "Apply display",
    "Save settings",
    "Reset defaults",
    "Back",
)


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


def _draw_gradient(surface: pygame.Surface) -> None:
    width, height = surface.get_size()
    for y in range(height):
        t = y / max(1, height - 1)
        color = (
            int(_BG_TOP[0] * (1 - t) + _BG_BOTTOM[0] * t),
            int(_BG_TOP[1] * (1 - t) + _BG_BOTTOM[1] * t),
            int(_BG_TOP[2] * (1 - t) + _BG_BOTTOM[2] * t),
        )
        pygame.draw.line(surface, color, (0, y), (width, y))


def _draw_guide_panel(surface: pygame.Surface, fonts, *, start_y: int) -> int:
    width, height = surface.get_size()
    guide_h = 112
    if start_y + guide_h + 20 >= height:
        return start_y
    guide_w = min(450, width - 40)
    guide_rect = pygame.Rect((width - guide_w) // 2, start_y + 4, guide_w, guide_h)
    draw_translation_rotation_guides(surface, fonts, rect=guide_rect, title="Translation / Rotation")
    return guide_rect.bottom + 4


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
    _draw_gradient(screen)
    width, height = screen.get_size()
    title = fonts.title_font.render("Pause Menu", True, _TEXT_COLOR)
    subtitle = fonts.hint_font.render(
        f"{dimension}D in-game controls and settings",
        True,
        _MUTED_COLOR,
    )
    screen.blit(title, ((width - title.get_width()) // 2, 40))
    screen.blit(subtitle, ((width - subtitle.get_width()) // 2, 86))

    panel_w = min(660, width - 40)
    panel_h = 88 + len(_PAUSE_ROWS) * 42
    panel_x = (width - panel_w) // 2
    panel_y = max(130, (height - panel_h) // 2)
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (0, 0, 0, 150), panel.get_rect(), border_radius=12)
    screen.blit(panel, (panel_x, panel_y))

    values = _pause_menu_values(dimension)
    y = panel_y + 20
    for idx, row in enumerate(_PAUSE_ROWS):
        selected = idx == state.selected
        color = _HIGHLIGHT_COLOR if selected else _TEXT_COLOR
        if selected:
            hi = pygame.Surface((panel_w - 28, fonts.menu_font.get_height() + 8), pygame.SRCALPHA)
            pygame.draw.rect(hi, (255, 255, 255, 38), hi.get_rect(), border_radius=8)
            screen.blit(hi, (panel_x + 14, y - 3))
        label = fonts.menu_font.render(row, True, color)
        screen.blit(label, (panel_x + 20, y))
        if values[idx]:
            value = fonts.menu_font.render(values[idx], True, color)
            screen.blit(value, (panel_x + panel_w - value.get_width() - 20, y))
        y += 42

    hints = (
        "Up/Down select   Enter apply",
        "Esc resume",
    )
    hy = panel_y + panel_h + 10
    for line in hints:
        surf = fonts.hint_font.render(line, True, _MUTED_COLOR)
        screen.blit(surf, ((width - surf.get_width()) // 2, hy))
        hy += surf.get_height() + 3
    hy = _draw_guide_panel(screen, fonts, start_y=hy)

    if state.status:
        color = (255, 150, 150) if state.status_error else (170, 240, 170)
        surf = fonts.hint_font.render(state.status, True, color)
        screen.blit(surf, ((width - surf.get_width()) // 2, hy + 2))


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
    _draw_gradient(screen)
    width, height = screen.get_size()
    title = fonts.title_font.render("Pause Settings", True, _TEXT_COLOR)
    subtitle = fonts.hint_font.render("Audio + Display", True, _MUTED_COLOR)
    screen.blit(title, ((width - title.get_width()) // 2, 40))
    screen.blit(subtitle, ((width - subtitle.get_width()) // 2, 86))

    panel_w = min(660, width - 40)
    panel_h = 88 + len(_SETTINGS_ROWS) * 42
    panel_x = (width - panel_w) // 2
    panel_y = max(130, (height - panel_h) // 2)
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (0, 0, 0, 150), panel.get_rect(), border_radius=12)
    screen.blit(panel, (panel_x, panel_y))

    values = _settings_values(state)
    y = panel_y + 20
    for idx, row in enumerate(_SETTINGS_ROWS):
        selected = idx == state.selected
        color = _HIGHLIGHT_COLOR if selected else _TEXT_COLOR
        if selected:
            hi = pygame.Surface((panel_w - 28, fonts.menu_font.get_height() + 8), pygame.SRCALPHA)
            pygame.draw.rect(hi, (255, 255, 255, 38), hi.get_rect(), border_radius=8)
            screen.blit(hi, (panel_x + 14, y - 3))
        label = fonts.menu_font.render(row, True, color)
        screen.blit(label, (panel_x + 20, y))
        if values[idx]:
            value = fonts.menu_font.render(values[idx], True, color)
            screen.blit(value, (panel_x + panel_w - value.get_width() - 20, y))
        y += 42

    hints = (
        "Left/Right adjust values   Enter apply",
        "Esc back",
    )
    hy = panel_y + panel_h + 10
    for line in hints:
        surf = fonts.hint_font.render(line, True, _MUTED_COLOR)
        screen.blit(surf, ((width - surf.get_width()) // 2, hy))
        hy += surf.get_height() + 3
    hy = _draw_guide_panel(screen, fonts, start_y=hy)

    if state.status:
        color = (255, 150, 150) if state.status_error else (170, 240, 170)
        surf = fonts.hint_font.render(state.status, True, color)
        screen.blit(surf, ((width - surf.get_width()) // 2, hy + 2))


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


def _pause_action_resume(
    screen: pygame.Surface,
    _fonts,
    state: _PauseState,
    *,
    dimension: int,
) -> tuple[pygame.Surface, bool]:
    del dimension
    state.decision = "resume"
    state.running = False
    return screen, True


def _pause_action_restart(
    screen: pygame.Surface,
    _fonts,
    state: _PauseState,
    *,
    dimension: int,
) -> tuple[pygame.Surface, bool]:
    del dimension
    state.decision = "restart"
    state.running = False
    return screen, True


def _pause_action_settings(
    screen: pygame.Surface,
    fonts,
    _state: _PauseState,
    *,
    dimension: int,
) -> tuple[pygame.Surface, bool]:
    del dimension
    return run_pause_settings_menu(screen, fonts)


def _pause_action_bot_options(
    screen: pygame.Surface,
    fonts,
    state: _PauseState,
    *,
    dimension: int,
) -> tuple[pygame.Surface, bool]:
    ok, msg = run_bot_options_menu(screen, fonts, start_dimension=dimension)
    state.status = msg
    state.status_error = not ok
    return screen, True


def _pause_action_keybindings(
    screen: pygame.Surface,
    fonts,
    state: _PauseState,
    *,
    dimension: int,
) -> tuple[pygame.Surface, bool]:
    run_keybindings_menu(screen, fonts, dimension=dimension, scope=f"{dimension}d")
    state.status = "Returned from keybindings setup"
    state.status_error = False
    return screen, True


def _pause_action_profile_prev(
    screen: pygame.Surface,
    _fonts,
    state: _PauseState,
    *,
    dimension: int,
) -> tuple[pygame.Surface, bool]:
    del dimension
    ok, msg, _profile = cycle_key_profile(-1)
    state.status = msg
    state.status_error = not ok
    return screen, True


def _pause_action_profile_next(
    screen: pygame.Surface,
    _fonts,
    state: _PauseState,
    *,
    dimension: int,
) -> tuple[pygame.Surface, bool]:
    del dimension
    ok, msg, _profile = cycle_key_profile(1)
    state.status = msg
    state.status_error = not ok
    return screen, True


def _pause_action_save_bindings(
    screen: pygame.Surface,
    _fonts,
    state: _PauseState,
    *,
    dimension: int,
) -> tuple[pygame.Surface, bool]:
    ok, msg = save_keybindings_file(dimension)
    state.status = msg
    state.status_error = not ok
    return screen, True


def _pause_action_load_bindings(
    screen: pygame.Surface,
    _fonts,
    state: _PauseState,
    *,
    dimension: int,
) -> tuple[pygame.Surface, bool]:
    ok, msg = load_keybindings_file(dimension)
    state.status = msg
    state.status_error = not ok
    return screen, True


def _pause_action_help(
    screen: pygame.Surface,
    fonts,
    state: _PauseState,
    *,
    dimension: int,
) -> tuple[pygame.Surface, bool]:
    screen = run_help_menu(screen, fonts, dimension=dimension, context_label="Pause Menu")
    state.status = "Returned from help"
    state.status_error = False
    return screen, True


def _pause_action_menu(
    screen: pygame.Surface,
    _fonts,
    state: _PauseState,
    *,
    dimension: int,
) -> tuple[pygame.Surface, bool]:
    del dimension
    state.decision = "menu"
    state.running = False
    return screen, True


def _pause_action_quit(
    screen: pygame.Surface,
    _fonts,
    state: _PauseState,
    *,
    dimension: int,
) -> tuple[pygame.Surface, bool]:
    del dimension
    state.decision = "quit"
    state.running = False
    return screen, True


_PAUSE_ACTIONS = (
    _pause_action_resume,
    _pause_action_restart,
    _pause_action_settings,
    _pause_action_bot_options,
    _pause_action_keybindings,
    _pause_action_profile_prev,
    _pause_action_profile_next,
    _pause_action_save_bindings,
    _pause_action_load_bindings,
    _pause_action_help,
    _pause_action_menu,
    _pause_action_quit,
)


def _handle_pause_row(
    screen: pygame.Surface,
    fonts,
    state: _PauseState,
    *,
    dimension: int,
) -> tuple[pygame.Surface, bool]:
    safe_index = max(0, min(len(_PAUSE_ACTIONS) - 1, state.selected))
    handler = _PAUSE_ACTIONS[safe_index]
    return handler(screen, fonts, state, dimension=dimension)


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
