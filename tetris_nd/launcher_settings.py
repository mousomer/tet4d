from __future__ import annotations

from dataclasses import dataclass

import pygame

from .app_runtime import capture_windowed_display_settings
from .audio import AudioSettings, play_sfx, set_audio_settings
from .display import DisplaySettings, apply_display_mode, normalize_display_settings
from .menu_config import default_settings_payload, settings_hub_rows
from .menu_gif_guides import draw_translation_rotation_guides
from .menu_persistence import persist_audio_payload, persist_display_payload
from .menu_settings_state import DEFAULT_WINDOWED_SIZE


BG_TOP = (14, 18, 44)
BG_BOTTOM = (4, 7, 20)
TEXT_COLOR = (232, 232, 240)
HIGHLIGHT_COLOR = (255, 224, 128)
MUTED_COLOR = (192, 200, 228)

_SETTINGS_HUB_ROWS = settings_hub_rows()
_AUDIO_MENU_ROWS = ("Master volume", "SFX volume", "Mute", "Save", "Reset defaults", "Back")
_AUDIO_MENU_HINTS = (
    "Left/Right adjust values   Enter activate row",
    "F5 save   F8 reset defaults   Esc back",
)
_DISPLAY_MENU_ROWS = ("Fullscreen", "Window width", "Window height", "Apply", "Save", "Reset defaults", "Back")
_DISPLAY_MENU_HINTS = (
    "Apply to preview mode change; Save to persist",
    "F5 save   F8 reset defaults   Esc back",
)


@dataclass
class SettingsHubResult:
    screen: pygame.Surface
    audio_settings: AudioSettings
    display_settings: DisplaySettings
    keep_running: bool


@dataclass
class _AudioMenuState:
    settings: AudioSettings
    original: AudioSettings
    selected: int = 0
    status: str = ""
    status_error: bool = False
    pending_reset_confirm: bool = False
    saved: bool = False
    running: bool = True


@dataclass
class _DisplayMenuState:
    settings: DisplaySettings
    original: DisplaySettings
    selected: int = 0
    status: str = ""
    status_error: bool = False
    pending_reset_confirm: bool = False
    saved: bool = False
    running: bool = True


@dataclass
class _SettingsHubState:
    selected: int = 0
    running: bool = True


@dataclass
class _UnifiedSettingsState:
    audio_settings: AudioSettings
    display_settings: DisplaySettings
    original_audio: AudioSettings
    original_display: DisplaySettings
    selected: int = 0
    status: str = ""
    status_error: bool = False
    pending_reset_confirm: bool = False
    saved: bool = False
    running: bool = True


_UNIFIED_SETTINGS_ROWS: tuple[tuple[str, str, str], ...] = (
    ("header", "Audio", ""),
    ("item", "Master volume", "audio_master"),
    ("item", "SFX volume", "audio_sfx"),
    ("item", "Mute", "audio_mute"),
    ("header", "Display", ""),
    ("item", "Fullscreen", "display_fullscreen"),
    ("item", "Window width", "display_width"),
    ("item", "Window height", "display_height"),
    ("item", "Apply display", "display_apply"),
    ("item", "Save", "save"),
    ("item", "Reset defaults", "reset"),
    ("item", "Back", "back"),
)
_UNIFIED_SELECTABLE = tuple(idx for idx, row in enumerate(_UNIFIED_SETTINGS_ROWS) if row[0] == "item")


def _draw_gradient(surface: pygame.Surface) -> None:
    width, height = surface.get_size()
    for y in range(height):
        t = y / max(1, height - 1)
        color = (
            int(BG_TOP[0] * (1 - t) + BG_BOTTOM[0] * t),
            int(BG_TOP[1] * (1 - t) + BG_BOTTOM[1] * t),
            int(BG_TOP[2] * (1 - t) + BG_BOTTOM[2] * t),
        )
        pygame.draw.line(surface, color, (0, y), (width, y))


def _audio_defaults() -> AudioSettings:
    defaults = default_settings_payload().get("audio", {})
    master = 0.8
    sfx = 0.7
    mute = False
    if isinstance(defaults, dict):
        raw_master = defaults.get("master_volume")
        raw_sfx = defaults.get("sfx_volume")
        if isinstance(raw_master, (int, float)) and not isinstance(raw_master, bool):
            master = float(raw_master)
        if isinstance(raw_sfx, (int, float)) and not isinstance(raw_sfx, bool):
            sfx = float(raw_sfx)
        mute = bool(defaults.get("mute", False))
    return AudioSettings(master_volume=master, sfx_volume=sfx, mute=mute)


def _display_defaults() -> DisplaySettings:
    defaults = default_settings_payload().get("display", {})
    fullscreen = False
    windowed_size = DEFAULT_WINDOWED_SIZE
    if isinstance(defaults, dict):
        fullscreen = bool(defaults.get("fullscreen", False))
        raw_size = defaults.get("windowed_size")
        if (
            isinstance(raw_size, list)
            and len(raw_size) == 2
            and all(isinstance(v, int) and not isinstance(v, bool) for v in raw_size)
        ):
            windowed_size = (raw_size[0], raw_size[1])
    return DisplaySettings(fullscreen=fullscreen, windowed_size=windowed_size)


def _clone_audio_settings(settings: AudioSettings) -> AudioSettings:
    return AudioSettings(
        master_volume=settings.master_volume,
        sfx_volume=settings.sfx_volume,
        mute=settings.mute,
    )


def _clone_display_settings(settings: DisplaySettings) -> DisplaySettings:
    return DisplaySettings(fullscreen=settings.fullscreen, windowed_size=settings.windowed_size)


def _sync_audio_preview(settings: AudioSettings) -> None:
    set_audio_settings(
        master_volume=settings.master_volume,
        sfx_volume=settings.sfx_volume,
        mute=settings.mute,
    )


def _audio_values(settings: AudioSettings) -> tuple[str, ...]:
    return (
        f"{int(settings.master_volume * 100)}%",
        f"{int(settings.sfx_volume * 100)}%",
        "ON" if settings.mute else "OFF",
        "",
        "",
        "",
    )


def _display_values(settings: DisplaySettings) -> tuple[str, ...]:
    return (
        "ON" if settings.fullscreen else "OFF",
        str(settings.windowed_size[0]),
        str(settings.windowed_size[1]),
        "",
        "",
        "",
        "",
    )


def _draw_audio_settings_menu(screen: pygame.Surface, fonts, loop: _AudioMenuState) -> None:
    _draw_gradient(screen)
    width, height = screen.get_size()
    title = fonts.title_font.render("Audio Settings", True, TEXT_COLOR)
    screen.blit(title, ((width - title.get_width()) // 2, 40))

    values = _audio_values(loop.settings)
    panel_w = min(560, width - 40)
    panel_h = 360
    panel_x = (width - panel_w) // 2
    panel_y = max(120, (height - panel_h) // 2)
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (0, 0, 0, 150), panel.get_rect(), border_radius=12)
    screen.blit(panel, (panel_x, panel_y))

    y = panel_y + 20
    for idx, row in enumerate(_AUDIO_MENU_ROWS):
        selected_row = idx == loop.selected
        color = HIGHLIGHT_COLOR if selected_row else TEXT_COLOR
        if selected_row:
            hi = pygame.Surface((panel_w - 28, fonts.menu_font.get_height() + 8), pygame.SRCALPHA)
            pygame.draw.rect(hi, (255, 255, 255, 38), hi.get_rect(), border_radius=8)
            screen.blit(hi, (panel_x + 14, y - 3))
        label = fonts.menu_font.render(row, True, color)
        screen.blit(label, (panel_x + 20, y))
        if values[idx]:
            value = fonts.menu_font.render(values[idx], True, color)
            screen.blit(value, (panel_x + panel_w - value.get_width() - 20, y))
        y += 50

    hy = panel_y + panel_h + 12
    for line in _AUDIO_MENU_HINTS:
        surf = fonts.hint_font.render(line, True, MUTED_COLOR)
        screen.blit(surf, ((width - surf.get_width()) // 2, hy))
        hy += surf.get_height() + 3

    if loop.status:
        color = (255, 150, 150) if loop.status_error else (170, 240, 170)
        surf = fonts.hint_font.render(loop.status, True, color)
        screen.blit(surf, ((width - surf.get_width()) // 2, hy + 2))


def _draw_display_settings_menu(screen: pygame.Surface, fonts, loop: _DisplayMenuState) -> None:
    _draw_gradient(screen)
    width, height = screen.get_size()
    title = fonts.title_font.render("Display Settings", True, TEXT_COLOR)
    screen.blit(title, ((width - title.get_width()) // 2, 40))

    values = _display_values(loop.settings)
    panel_w = min(560, width - 40)
    panel_h = 400
    panel_x = (width - panel_w) // 2
    panel_y = max(120, (height - panel_h) // 2)
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (0, 0, 0, 150), panel.get_rect(), border_radius=12)
    screen.blit(panel, (panel_x, panel_y))

    y = panel_y + 20
    for idx, row in enumerate(_DISPLAY_MENU_ROWS):
        selected_row = idx == loop.selected
        color = HIGHLIGHT_COLOR if selected_row else TEXT_COLOR
        if selected_row:
            hi = pygame.Surface((panel_w - 28, fonts.menu_font.get_height() + 8), pygame.SRCALPHA)
            pygame.draw.rect(hi, (255, 255, 255, 38), hi.get_rect(), border_radius=8)
            screen.blit(hi, (panel_x + 14, y - 3))
        label = fonts.menu_font.render(row, True, color)
        screen.blit(label, (panel_x + 20, y))
        if values[idx]:
            value = fonts.menu_font.render(values[idx], True, color)
            screen.blit(value, (panel_x + panel_w - value.get_width() - 20, y))
        y += 50

    hy = panel_y + panel_h + 12
    for line in _DISPLAY_MENU_HINTS:
        surf = fonts.hint_font.render(line, True, MUTED_COLOR)
        screen.blit(surf, ((width - surf.get_width()) // 2, hy))
        hy += surf.get_height() + 3

    if loop.status:
        color = (255, 150, 150) if loop.status_error else (170, 240, 170)
        surf = fonts.hint_font.render(loop.status, True, color)
        screen.blit(surf, ((width - surf.get_width()) // 2, hy + 2))


def _set_audio_status(loop: _AudioMenuState, message: str, *, is_error: bool = False) -> None:
    loop.status = message
    loop.status_error = is_error


def _set_display_status(loop: _DisplayMenuState, message: str, *, is_error: bool = False) -> None:
    loop.status = message
    loop.status_error = is_error


def _adjust_audio_slider(loop: _AudioMenuState, key: int) -> bool:
    if key not in (pygame.K_LEFT, pygame.K_RIGHT):
        return False
    delta = -0.05 if key == pygame.K_LEFT else 0.05
    if loop.selected == 0:
        loop.settings.master_volume = max(0.0, min(1.0, loop.settings.master_volume + delta))
    elif loop.selected == 1:
        loop.settings.sfx_volume = max(0.0, min(1.0, loop.settings.sfx_volume + delta))
    else:
        return False
    _sync_audio_preview(loop.settings)
    play_sfx("menu_move")
    return True


def _toggle_audio_mute(loop: _AudioMenuState) -> None:
    loop.settings.mute = not loop.settings.mute
    _sync_audio_preview(loop.settings)
    play_sfx("menu_move")


def _save_audio_settings_from_menu(loop: _AudioMenuState) -> None:
    ok, msg = persist_audio_payload(
        master_volume=loop.settings.master_volume,
        sfx_volume=loop.settings.sfx_volume,
        mute=loop.settings.mute,
    )
    if ok:
        _set_audio_status(loop, "Saved audio settings")
    else:
        _set_audio_status(loop, msg, is_error=True)
    loop.saved = ok
    if ok:
        play_sfx("menu_confirm")


def _reset_audio_settings_from_menu(loop: _AudioMenuState) -> None:
    loop.settings = _audio_defaults()
    _sync_audio_preview(loop.settings)
    loop.pending_reset_confirm = False
    _set_audio_status(loop, "Audio reset to defaults (not saved yet)")
    play_sfx("menu_move")


def _apply_display_settings_preview(_screen: pygame.Surface, loop: _DisplayMenuState) -> pygame.Surface:
    return apply_display_mode(loop.settings, preferred_windowed_size=loop.settings.windowed_size)


def _save_display_settings_from_menu(screen: pygame.Surface, loop: _DisplayMenuState) -> pygame.Surface:
    loop.settings = normalize_display_settings(loop.settings)
    screen = _apply_display_settings_preview(screen, loop)
    ok, msg = persist_display_payload(
        fullscreen=loop.settings.fullscreen,
        windowed_size=loop.settings.windowed_size,
    )
    if ok:
        _set_display_status(loop, "Saved display settings")
    else:
        _set_display_status(loop, msg, is_error=True)
    loop.saved = ok
    if ok:
        play_sfx("menu_confirm")
    return screen


def _reset_display_settings_from_menu(loop: _DisplayMenuState) -> None:
    loop.settings = _display_defaults()
    loop.pending_reset_confirm = False
    _set_display_status(loop, "Display reset to defaults (not saved yet)")
    play_sfx("menu_move")


def _handle_audio_navigation_key(loop: _AudioMenuState, key: int) -> bool:
    if key == pygame.K_ESCAPE:
        loop.running = False
        return True
    if key == pygame.K_UP:
        loop.selected = (loop.selected - 1) % len(_AUDIO_MENU_ROWS)
        play_sfx("menu_move")
        return True
    if key == pygame.K_DOWN:
        loop.selected = (loop.selected + 1) % len(_AUDIO_MENU_ROWS)
        play_sfx("menu_move")
        return True
    return False


def _handle_audio_reset_or_save(loop: _AudioMenuState, key: int) -> bool:
    if key == pygame.K_F8:
        if not loop.pending_reset_confirm:
            loop.pending_reset_confirm = True
            _set_audio_status(loop, "Press F8 again to confirm audio reset")
        else:
            _reset_audio_settings_from_menu(loop)
        return True
    if key == pygame.K_F5:
        _save_audio_settings_from_menu(loop)
        return True
    return False


def _handle_audio_enter(loop: _AudioMenuState) -> bool:
    if loop.selected == 3:
        _save_audio_settings_from_menu(loop)
        return True
    if loop.selected == 4:
        if not loop.pending_reset_confirm:
            loop.pending_reset_confirm = True
            _set_audio_status(loop, "Press Enter on Reset defaults again to confirm")
        else:
            _reset_audio_settings_from_menu(loop)
        return True
    if loop.selected == 5:
        loop.running = False
        return True
    return False


def _dispatch_audio_key(loop: _AudioMenuState, key: int) -> None:
    reset_trigger = key == pygame.K_F8 or (key in (pygame.K_RETURN, pygame.K_KP_ENTER) and loop.selected == 4)
    if not reset_trigger:
        loop.pending_reset_confirm = False
    if _handle_audio_navigation_key(loop, key):
        return
    if _adjust_audio_slider(loop, key):
        return
    if loop.selected == 2 and key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_RETURN, pygame.K_KP_ENTER):
        _toggle_audio_mute(loop)
        return
    if _handle_audio_reset_or_save(loop, key):
        return
    if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        _handle_audio_enter(loop)


def _handle_display_navigation_key(loop: _DisplayMenuState, key: int) -> bool:
    if key == pygame.K_ESCAPE:
        loop.running = False
        return True
    if key == pygame.K_UP:
        loop.selected = (loop.selected - 1) % len(_DISPLAY_MENU_ROWS)
        play_sfx("menu_move")
        return True
    if key == pygame.K_DOWN:
        loop.selected = (loop.selected + 1) % len(_DISPLAY_MENU_ROWS)
        play_sfx("menu_move")
        return True
    return False


def _toggle_display_fullscreen(loop: _DisplayMenuState, key: int) -> bool:
    if loop.selected != 0:
        return False
    if key not in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_RETURN, pygame.K_KP_ENTER):
        return False
    loop.settings = DisplaySettings(not loop.settings.fullscreen, loop.settings.windowed_size)
    play_sfx("menu_move")
    return True


def _adjust_display_window_size(loop: _DisplayMenuState, key: int) -> bool:
    if key not in (pygame.K_LEFT, pygame.K_RIGHT):
        return False
    if loop.selected not in (1, 2):
        return False
    delta = -40 if key == pygame.K_LEFT else 40
    width, height = loop.settings.windowed_size
    if loop.selected == 1:
        width = max(640, width + delta)
    else:
        height = max(480, height + delta)
    loop.settings = DisplaySettings(loop.settings.fullscreen, (width, height))
    play_sfx("menu_move")
    return True


def _handle_display_reset_or_save(screen: pygame.Surface, loop: _DisplayMenuState, key: int) -> tuple[pygame.Surface, bool]:
    if key == pygame.K_F8:
        if not loop.pending_reset_confirm:
            loop.pending_reset_confirm = True
            _set_display_status(loop, "Press F8 again to confirm display reset")
        else:
            _reset_display_settings_from_menu(loop)
        return screen, True
    if key == pygame.K_F5:
        return _save_display_settings_from_menu(screen, loop), True
    return screen, False


def _handle_display_enter(screen: pygame.Surface, loop: _DisplayMenuState) -> tuple[pygame.Surface, bool]:
    if loop.selected == 3:
        screen = _apply_display_settings_preview(screen, loop)
        _set_display_status(loop, "Applied display mode")
        play_sfx("menu_confirm")
        return screen, True
    if loop.selected == 4:
        return _save_display_settings_from_menu(screen, loop), True
    if loop.selected == 5:
        if not loop.pending_reset_confirm:
            loop.pending_reset_confirm = True
            _set_display_status(loop, "Press Enter on Reset defaults again to confirm")
        else:
            _reset_display_settings_from_menu(loop)
        return screen, True
    if loop.selected == 6:
        loop.running = False
        return screen, True
    return screen, False


def _dispatch_display_key(screen: pygame.Surface, loop: _DisplayMenuState, key: int) -> pygame.Surface:
    reset_trigger = key == pygame.K_F8 or (key in (pygame.K_RETURN, pygame.K_KP_ENTER) and loop.selected == 5)
    if not reset_trigger:
        loop.pending_reset_confirm = False
    if _handle_display_navigation_key(loop, key):
        return screen
    if _toggle_display_fullscreen(loop, key):
        return screen
    if _adjust_display_window_size(loop, key):
        return screen
    screen, handled = _handle_display_reset_or_save(screen, loop, key)
    if handled:
        return screen
    if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        screen, _handled = _handle_display_enter(screen, loop)
    return screen


def _run_audio_settings_menu(screen: pygame.Surface, fonts, current: AudioSettings) -> tuple[AudioSettings, bool]:
    loop = _AudioMenuState(
        settings=_clone_audio_settings(current),
        original=_clone_audio_settings(current),
    )
    clock = pygame.time.Clock()
    keep_running = True

    while loop.running:
        _dt = clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                keep_running = False
                loop.running = False
                break
            if event.type != pygame.KEYDOWN:
                continue
            _dispatch_audio_key(loop, event.key)
            if not loop.running:
                break

        if not keep_running:
            break
        _draw_audio_settings_menu(screen, fonts, loop)
        pygame.display.flip()

    if not loop.saved:
        _sync_audio_preview(loop.original)
        return loop.original, keep_running
    return loop.settings, keep_running


def _run_display_settings_menu(
    screen: pygame.Surface,
    fonts,
    current: DisplaySettings,
) -> tuple[pygame.Surface, DisplaySettings, bool]:
    loop = _DisplayMenuState(
        settings=_clone_display_settings(current),
        original=_clone_display_settings(current),
    )
    clock = pygame.time.Clock()
    keep_running = True

    while loop.running:
        _dt = clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                keep_running = False
                loop.running = False
                break
            if event.type != pygame.KEYDOWN:
                continue
            screen = _dispatch_display_key(screen, loop, event.key)
            if not loop.running:
                break

        if not keep_running:
            break
        _draw_display_settings_menu(screen, fonts, loop)
        pygame.display.flip()

    if not loop.saved:
        restored = normalize_display_settings(loop.original)
        screen = apply_display_mode(restored, preferred_windowed_size=restored.windowed_size)
        return screen, restored, keep_running
    state = capture_windowed_display_settings(normalize_display_settings(loop.settings))
    return screen, state, keep_running


def _draw_settings_hub_menu(screen: pygame.Surface, fonts, loop: _SettingsHubState) -> None:
    _draw_gradient(screen)
    width, height = screen.get_size()
    title = fonts.title_font.render("Settings", True, TEXT_COLOR)
    subtitle = fonts.hint_font.render("Unified audio and display configuration", True, MUTED_COLOR)
    screen.blit(title, ((width - title.get_width()) // 2, 48))
    screen.blit(subtitle, ((width - subtitle.get_width()) // 2, 92))

    panel_w = min(520, width - 40)
    panel_h = 96 + len(_SETTINGS_HUB_ROWS) * 54
    panel_x = (width - panel_w) // 2
    panel_y = max(156, (height - panel_h) // 2)
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (0, 0, 0, 150), panel.get_rect(), border_radius=12)
    screen.blit(panel, (panel_x, panel_y))

    y = panel_y + 28
    for idx, label in enumerate(_SETTINGS_HUB_ROWS):
        selected = idx == loop.selected
        color = HIGHLIGHT_COLOR if selected else TEXT_COLOR
        if selected:
            hi = pygame.Surface((panel_w - 30, fonts.menu_font.get_height() + 10), pygame.SRCALPHA)
            pygame.draw.rect(hi, (255, 255, 255, 38), hi.get_rect(), border_radius=8)
            screen.blit(hi, (panel_x + 15, y - 4))
        surf = fonts.menu_font.render(label, True, color)
        screen.blit(surf, (panel_x + 24, y))
        y += 54

    hints = ("Up/Down select   Enter open", "Esc back")
    hy = panel_y + panel_h + 14
    for line in hints:
        surf = fonts.hint_font.render(line, True, MUTED_COLOR)
        screen.blit(surf, ((width - surf.get_width()) // 2, hy))
        hy += surf.get_height() + 3


def _dispatch_settings_hub_key(
    event: pygame.event.Event,
    *,
    screen: pygame.Surface,
    fonts,
    loop: _SettingsHubState,
    audio_settings: AudioSettings,
    display_settings: DisplaySettings,
) -> tuple[pygame.Surface, AudioSettings, DisplaySettings, bool]:
    keep_running = True
    if event.key == pygame.K_ESCAPE:
        loop.running = False
        return screen, audio_settings, display_settings, keep_running
    if event.key == pygame.K_UP:
        loop.selected = (loop.selected - 1) % len(_SETTINGS_HUB_ROWS)
        play_sfx("menu_move")
        return screen, audio_settings, display_settings, keep_running
    if event.key == pygame.K_DOWN:
        loop.selected = (loop.selected + 1) % len(_SETTINGS_HUB_ROWS)
        play_sfx("menu_move")
        return screen, audio_settings, display_settings, keep_running
    if event.key not in (pygame.K_RETURN, pygame.K_KP_ENTER):
        return screen, audio_settings, display_settings, keep_running
    if loop.selected == 0:
        audio_settings, keep_running = _run_audio_settings_menu(screen, fonts, audio_settings)
        if keep_running:
            set_audio_settings(
                master_volume=audio_settings.master_volume,
                sfx_volume=audio_settings.sfx_volume,
                mute=audio_settings.mute,
            )
            play_sfx("menu_confirm")
        else:
            loop.running = False
        return screen, audio_settings, display_settings, keep_running
    if loop.selected == 1:
        screen, display_settings, keep_running = _run_display_settings_menu(screen, fonts, display_settings)
        if keep_running:
            play_sfx("menu_confirm")
        else:
            loop.running = False
        return screen, audio_settings, display_settings, keep_running
    loop.running = False
    return screen, audio_settings, display_settings, keep_running


def _unified_row_key(state: _UnifiedSettingsState) -> str:
    row_idx = _UNIFIED_SELECTABLE[state.selected]
    return _UNIFIED_SETTINGS_ROWS[row_idx][2]


def _set_unified_status(state: _UnifiedSettingsState, message: str, *, is_error: bool = False) -> None:
    state.status = message
    state.status_error = is_error


def _mark_unified_dirty(state: _UnifiedSettingsState) -> None:
    state.saved = False


def _save_unified_settings(screen: pygame.Surface, state: _UnifiedSettingsState) -> pygame.Surface:
    state.display_settings = normalize_display_settings(state.display_settings)
    screen = apply_display_mode(
        state.display_settings,
        preferred_windowed_size=state.display_settings.windowed_size,
    )
    ok_audio, msg_audio = persist_audio_payload(
        master_volume=state.audio_settings.master_volume,
        sfx_volume=state.audio_settings.sfx_volume,
        mute=state.audio_settings.mute,
    )
    ok_display, msg_display = persist_display_payload(
        fullscreen=state.display_settings.fullscreen,
        windowed_size=state.display_settings.windowed_size,
    )
    if ok_audio and ok_display:
        state.original_audio = _clone_audio_settings(state.audio_settings)
        state.original_display = _clone_display_settings(state.display_settings)
        state.saved = True
        _set_unified_status(state, "Saved audio/display settings")
        play_sfx("menu_confirm")
        return screen

    error = msg_audio if not ok_audio else msg_display
    _set_unified_status(state, error, is_error=True)
    return screen


def _reset_unified_settings(screen: pygame.Surface, state: _UnifiedSettingsState) -> pygame.Surface:
    state.audio_settings = _audio_defaults()
    state.display_settings = _display_defaults()
    state.pending_reset_confirm = False
    _mark_unified_dirty(state)
    _sync_audio_preview(state.audio_settings)
    screen = apply_display_mode(
        state.display_settings,
        preferred_windowed_size=state.display_settings.windowed_size,
    )
    _set_unified_status(state, "Reset to defaults (not saved yet)")
    play_sfx("menu_move")
    return screen


def _adjust_unified_with_arrows(state: _UnifiedSettingsState, key: int) -> bool:
    if key not in (pygame.K_LEFT, pygame.K_RIGHT):
        return False
    delta_sign = -1 if key == pygame.K_LEFT else 1
    row_key = _unified_row_key(state)
    if row_key == "audio_master":
        state.audio_settings.master_volume = max(0.0, min(1.0, state.audio_settings.master_volume + delta_sign * 0.05))
        _sync_audio_preview(state.audio_settings)
    elif row_key == "audio_sfx":
        state.audio_settings.sfx_volume = max(0.0, min(1.0, state.audio_settings.sfx_volume + delta_sign * 0.05))
        _sync_audio_preview(state.audio_settings)
    elif row_key == "audio_mute":
        state.audio_settings.mute = not state.audio_settings.mute
        _sync_audio_preview(state.audio_settings)
    elif row_key == "display_fullscreen":
        state.display_settings = DisplaySettings(not state.display_settings.fullscreen, state.display_settings.windowed_size)
    elif row_key == "display_width":
        width, height = state.display_settings.windowed_size
        state.display_settings = DisplaySettings(state.display_settings.fullscreen, (max(640, width + delta_sign * 40), height))
    elif row_key == "display_height":
        width, height = state.display_settings.windowed_size
        state.display_settings = DisplaySettings(state.display_settings.fullscreen, (width, max(480, height + delta_sign * 40)))
    else:
        return False
    _mark_unified_dirty(state)
    state.pending_reset_confirm = False
    play_sfx("menu_move")
    return True


def _handle_unified_enter(screen: pygame.Surface, state: _UnifiedSettingsState) -> pygame.Surface:
    row_key = _unified_row_key(state)
    if row_key in {"audio_mute", "display_fullscreen"}:
        state.pending_reset_confirm = False
        _adjust_unified_with_arrows(state, pygame.K_RIGHT)
        return screen
    if row_key == "display_apply":
        state.display_settings = normalize_display_settings(state.display_settings)
        screen = apply_display_mode(
            state.display_settings,
            preferred_windowed_size=state.display_settings.windowed_size,
        )
        _mark_unified_dirty(state)
        state.pending_reset_confirm = False
        _set_unified_status(state, "Applied display mode")
        play_sfx("menu_confirm")
        return screen
    if row_key == "save":
        state.pending_reset_confirm = False
        return _save_unified_settings(screen, state)
    if row_key == "reset":
        if not state.pending_reset_confirm:
            state.pending_reset_confirm = True
            _set_unified_status(state, "Press Enter on Reset defaults again to confirm")
            return screen
        return _reset_unified_settings(screen, state)
    if row_key == "back":
        state.pending_reset_confirm = False
        state.running = False
    return screen


def _unified_value_text(state: _UnifiedSettingsState, row_key: str) -> str:
    if row_key == "audio_master":
        return f"{int(state.audio_settings.master_volume * 100)}%"
    if row_key == "audio_sfx":
        return f"{int(state.audio_settings.sfx_volume * 100)}%"
    if row_key == "audio_mute":
        return "ON" if state.audio_settings.mute else "OFF"
    if row_key == "display_fullscreen":
        return "ON" if state.display_settings.fullscreen else "OFF"
    if row_key == "display_width":
        return str(state.display_settings.windowed_size[0])
    if row_key == "display_height":
        return str(state.display_settings.windowed_size[1])
    return ""


def _draw_unified_settings_menu(screen: pygame.Surface, fonts, state: _UnifiedSettingsState) -> None:
    _draw_gradient(screen)
    width, height = screen.get_size()
    title = fonts.title_font.render("Settings", True, TEXT_COLOR)
    subtitle = fonts.hint_font.render("Unified Audio + Display (grouped categories)", True, MUTED_COLOR)
    screen.blit(title, ((width - title.get_width()) // 2, 44))
    screen.blit(subtitle, ((width - subtitle.get_width()) // 2, 90))

    panel_w = min(700, width - 40)
    panel_h = min(560, height - 220)
    panel_x = (width - panel_w) // 2
    panel_y = max(132, (height - panel_h) // 2)
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (0, 0, 0, 150), panel.get_rect(), border_radius=12)
    screen.blit(panel, (panel_x, panel_y))

    selected_row_idx = _UNIFIED_SELECTABLE[state.selected]
    y = panel_y + 18
    for idx, (row_kind, label, row_key) in enumerate(_UNIFIED_SETTINGS_ROWS):
        if row_kind == "header":
            header = fonts.hint_font.render(label, True, (182, 206, 255))
            screen.blit(header, (panel_x + 22, y + 3))
            y += header.get_height() + 10
            continue

        selected = idx == selected_row_idx
        color = HIGHLIGHT_COLOR if selected else TEXT_COLOR
        if selected:
            hi = pygame.Surface((panel_w - 28, fonts.menu_font.get_height() + 10), pygame.SRCALPHA)
            pygame.draw.rect(hi, (255, 255, 255, 38), hi.get_rect(), border_radius=8)
            screen.blit(hi, (panel_x + 14, y - 4))
        label_surf = fonts.menu_font.render(label, True, color)
        screen.blit(label_surf, (panel_x + 22, y))
        value = _unified_value_text(state, row_key)
        if value:
            value_surf = fonts.menu_font.render(value, True, color)
            screen.blit(value_surf, (panel_x + panel_w - value_surf.get_width() - 22, y))
        y += 46

    hints = (
        "Up/Down select   Left/Right adjust   Enter activate",
        "F5 save   F8 reset defaults   Esc back",
    )
    hy = panel_y + panel_h + 12
    for line in hints:
        surf = fonts.hint_font.render(line, True, MUTED_COLOR)
        screen.blit(surf, ((width - surf.get_width()) // 2, hy))
        hy += surf.get_height() + 3
    hy = _draw_unified_guides(screen, fonts, hy)

    if state.status:
        color = (255, 150, 150) if state.status_error else (170, 240, 170)
        surf = fonts.hint_font.render(state.status, True, color)
        screen.blit(surf, ((width - surf.get_width()) // 2, hy + 2))


def _draw_unified_guides(screen: pygame.Surface, fonts, start_y: int) -> int:
    width, height = screen.get_size()
    guide_h = 112
    if start_y + guide_h + 22 >= height:
        return start_y
    guide_w = min(460, width - 40)
    rect = pygame.Rect((width - guide_w) // 2, start_y + 4, guide_w, guide_h)
    draw_translation_rotation_guides(screen, fonts, rect=rect, title="Translation / Rotation")
    return rect.bottom + 4


def _dispatch_unified_key(
    screen: pygame.Surface,
    state: _UnifiedSettingsState,
    key: int,
) -> pygame.Surface:
    if key == pygame.K_ESCAPE:
        state.running = False
        return screen
    if key == pygame.K_UP:
        state.pending_reset_confirm = False
        state.selected = (state.selected - 1) % len(_UNIFIED_SELECTABLE)
        play_sfx("menu_move")
        return screen
    if key == pygame.K_DOWN:
        state.pending_reset_confirm = False
        state.selected = (state.selected + 1) % len(_UNIFIED_SELECTABLE)
        play_sfx("menu_move")
        return screen
    if key == pygame.K_F5:
        state.pending_reset_confirm = False
        return _save_unified_settings(screen, state)
    if key == pygame.K_F8:
        if not state.pending_reset_confirm:
            state.pending_reset_confirm = True
            _set_unified_status(state, "Press F8 again to confirm reset defaults")
            return screen
        return _reset_unified_settings(screen, state)
    if _adjust_unified_with_arrows(state, key):
        return screen
    if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        return _handle_unified_enter(screen, state)
    return screen


def _process_unified_events(
    screen: pygame.Surface,
    state: _UnifiedSettingsState,
) -> tuple[pygame.Surface, bool]:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            state.running = False
            return screen, False
        if event.type != pygame.KEYDOWN:
            continue
        screen = _dispatch_unified_key(screen, state, event.key)
        if not state.running:
            break
    return screen, True


def run_settings_hub_menu(
    screen: pygame.Surface,
    fonts,
    *,
    audio_settings: AudioSettings,
    display_settings: DisplaySettings,
) -> SettingsHubResult:
    state = _UnifiedSettingsState(
        audio_settings=_clone_audio_settings(audio_settings),
        display_settings=_clone_display_settings(display_settings),
        original_audio=_clone_audio_settings(audio_settings),
        original_display=_clone_display_settings(display_settings),
    )
    _sync_audio_preview(state.audio_settings)

    clock = pygame.time.Clock()
    keep_running = True
    while state.running:
        _dt = clock.tick(60)
        screen, keep_running = _process_unified_events(screen, state)
        if not keep_running or not state.running:
            break
        _draw_unified_settings_menu(screen, fonts, state)
        pygame.display.flip()

    if not state.saved:
        _sync_audio_preview(state.original_audio)
        restored_display = normalize_display_settings(state.original_display)
        screen = apply_display_mode(restored_display, preferred_windowed_size=restored_display.windowed_size)
        return SettingsHubResult(
            screen=screen,
            audio_settings=state.original_audio,
            display_settings=restored_display,
            keep_running=keep_running,
        )

    final_display = capture_windowed_display_settings(normalize_display_settings(state.display_settings))
    return SettingsHubResult(
        screen=screen,
        audio_settings=state.audio_settings,
        display_settings=final_display,
        keep_running=keep_running,
    )
