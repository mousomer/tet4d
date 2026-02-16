import sys
from collections.abc import Callable
from dataclasses import dataclass

import pygame

import front2d
from tetris_nd.app_runtime import (
    capture_windowed_display_settings,
    initialize_runtime,
    open_display,
)
from tetris_nd.audio import AudioSettings, play_sfx, set_audio_settings
from tetris_nd.display import DisplaySettings, apply_display_mode, normalize_display_settings
from tetris_nd.front3d_game import (
    build_config as build_config_3d,
    run_game_loop as run_game_loop_3d,
    run_menu as run_menu_3d,
    suggested_window_size as suggested_window_size_3d,
)
from tetris_nd.front4d_game import run_game_loop as run_game_loop_4d, suggested_window_size as suggested_window_size_4d
from tetris_nd.frontend_nd import build_config as build_config_nd, init_fonts, run_menu as run_menu_nd
from tetris_nd.keybindings import (
    active_key_profile,
    load_active_profile_bindings,
    set_active_key_profile,
)
from tetris_nd.keybindings_menu import run_keybindings_menu
from tetris_nd.menu_settings_state import (
    DEFAULT_WINDOWED_SIZE,
    load_app_settings_payload,
    save_app_settings_payload,
    save_audio_settings,
    save_display_settings,
)


BG_TOP = (14, 18, 44)
BG_BOTTOM = (4, 7, 20)
TEXT_COLOR = (232, 232, 240)
HIGHLIGHT_COLOR = (255, 224, 128)
MUTED_COLOR = (192, 200, 228)


MENU_ITEMS = (
    ("play_2d", "Play 2D"),
    ("play_3d", "Play 3D"),
    ("play_4d", "Play 4D"),
    ("keybindings", "Keybindings Setup"),
    ("audio", "Audio Settings"),
    ("display", "Display Settings"),
    ("quit", "Quit"),
)


@dataclass
class MainMenuState:
    selected: int = 0
    status: str = ""
    status_error: bool = False
    last_mode: str = "2d"


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


def _draw_main_menu(screen: pygame.Surface, fonts, state: MainMenuState) -> None:
    _draw_gradient(screen)
    width, height = screen.get_size()
    title = fonts.title_font.render("ND Tetris Launcher", True, TEXT_COLOR)
    subtitle = fonts.hint_font.render(
        "Unified launcher for 2D / 3D / 4D, keybindings, audio, and display settings",
        True,
        MUTED_COLOR,
    )
    screen.blit(title, ((width - title.get_width()) // 2, 44))
    screen.blit(subtitle, ((width - subtitle.get_width()) // 2, 90))

    panel_w = min(620, width - 40)
    panel_h = 72 + len(MENU_ITEMS) * 52
    panel_x = (width - panel_w) // 2
    panel_y = max(146, (height - panel_h) // 2)

    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (0, 0, 0, 152), panel.get_rect(), border_radius=14)
    screen.blit(panel, (panel_x, panel_y))

    y = panel_y + 24
    for idx, (_, label) in enumerate(MENU_ITEMS):
        selected = idx == state.selected
        color = HIGHLIGHT_COLOR if selected else TEXT_COLOR
        text = fonts.menu_font.render(label, True, color)
        row_rect = text.get_rect(topleft=(panel_x + 28, y))
        if selected:
            hi = pygame.Surface((panel_w - 32, row_rect.height + 10), pygame.SRCALPHA)
            pygame.draw.rect(hi, (255, 255, 255, 38), hi.get_rect(), border_radius=9)
            screen.blit(hi, (panel_x + 16, y - 4))
        screen.blit(text, row_rect.topleft)
        y += 52

    info_lines = [
        f"Active key profile: {active_key_profile()}",
        f"Last mode: {state.last_mode.upper()}",
        "Up/Down select   Enter open   Esc quit",
    ]
    info_y = panel_y + panel_h + 14
    for line in info_lines:
        text = fonts.hint_font.render(line, True, MUTED_COLOR)
        screen.blit(text, ((width - text.get_width()) // 2, info_y))
        info_y += text.get_height() + 3

    if state.status:
        status_color = (255, 150, 150) if state.status_error else (170, 240, 170)
        status = fonts.hint_font.render(state.status, True, status_color)
        screen.blit(status, ((width - status.get_width()) // 2, min(height - 34, info_y + 8)))


def _persist_global_state(
    *,
    display_settings: DisplaySettings,
    audio_settings: AudioSettings,
    last_mode: str,
) -> tuple[bool, str]:
    payload = load_app_settings_payload()
    payload["last_mode"] = last_mode
    payload["active_profile"] = active_key_profile()
    payload["display"] = {
        "fullscreen": bool(display_settings.fullscreen),
        "windowed_size": [int(display_settings.windowed_size[0]), int(display_settings.windowed_size[1])],
    }
    payload["audio"] = {
        "master_volume": float(audio_settings.master_volume),
        "sfx_volume": float(audio_settings.sfx_volume),
        "mute": bool(audio_settings.mute),
    }
    return save_app_settings_payload(payload)


def _audio_defaults() -> AudioSettings:
    return AudioSettings(master_volume=0.8, sfx_volume=0.7, mute=False)


def _display_defaults() -> DisplaySettings:
    return DisplaySettings(fullscreen=False, windowed_size=DEFAULT_WINDOWED_SIZE)


_AUDIO_MENU_ROWS = ("Master volume", "SFX volume", "Mute", "Save", "Reset defaults", "Back")
_AUDIO_MENU_HINTS = (
    "Left/Right adjust values   Enter activate row",
    "F5 save   F8 reset defaults   Esc back",
)


@dataclass
class _AudioMenuState:
    settings: AudioSettings
    original: AudioSettings
    selected: int = 0
    status: str = ""
    status_error: bool = False
    saved: bool = False
    running: bool = True


def _clone_audio_settings(settings: AudioSettings) -> AudioSettings:
    return AudioSettings(
        master_volume=settings.master_volume,
        sfx_volume=settings.sfx_volume,
        mute=settings.mute,
    )


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


def _set_audio_status(loop: _AudioMenuState, message: str, *, is_error: bool = False) -> None:
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
    ok, msg = save_audio_settings(
        master_volume=loop.settings.master_volume,
        sfx_volume=loop.settings.sfx_volume,
        mute=loop.settings.mute,
    )
    _set_audio_status(loop, msg, is_error=not ok)
    loop.saved = ok
    if ok:
        play_sfx("menu_confirm")


def _reset_audio_settings_from_menu(loop: _AudioMenuState) -> None:
    loop.settings = _audio_defaults()
    _sync_audio_preview(loop.settings)
    _set_audio_status(loop, "Audio reset to defaults (not saved yet)")
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


def _handle_audio_commit_key(loop: _AudioMenuState, key: int) -> bool:
    if key == pygame.K_F8:
        _reset_audio_settings_from_menu(loop)
        return True
    if key == pygame.K_F5:
        _save_audio_settings_from_menu(loop)
        return True
    if key not in (pygame.K_RETURN, pygame.K_KP_ENTER):
        return False
    if loop.selected == 3:
        _save_audio_settings_from_menu(loop)
        return True
    if loop.selected == 4:
        _reset_audio_settings_from_menu(loop)
        return True
    if loop.selected == 5:
        loop.running = False
        return True
    return False


def _handle_audio_menu_key(loop: _AudioMenuState, key: int) -> None:
    if _handle_audio_navigation_key(loop, key):
        return
    if _adjust_audio_slider(loop, key):
        return
    if loop.selected == 2 and key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_RETURN, pygame.K_KP_ENTER):
        _toggle_audio_mute(loop)
        return
    _handle_audio_commit_key(loop, key)


def _run_audio_settings_menu(screen: pygame.Surface, fonts, current: AudioSettings) -> AudioSettings:
    loop = _AudioMenuState(
        settings=_clone_audio_settings(current),
        original=_clone_audio_settings(current),
    )
    clock = pygame.time.Clock()

    while loop.running:
        _dt = clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return current
            if event.type != pygame.KEYDOWN:
                continue
            _handle_audio_menu_key(loop, event.key)
            if not loop.running:
                break

        _draw_audio_settings_menu(screen, fonts, loop)
        pygame.display.flip()

    if not loop.saved:
        _sync_audio_preview(loop.original)
        return loop.original
    return loop.settings


_DISPLAY_MENU_ROWS = ("Fullscreen", "Window width", "Window height", "Apply", "Save", "Reset defaults", "Back")
_DISPLAY_MENU_HINTS = (
    "Apply to preview mode change; Save to persist",
    "F5 save   F8 reset defaults   Esc back",
)


@dataclass
class _DisplayMenuState:
    settings: DisplaySettings
    original: DisplaySettings
    selected: int = 0
    status: str = ""
    status_error: bool = False
    saved: bool = False
    running: bool = True


def _clone_display_settings(settings: DisplaySettings) -> DisplaySettings:
    return DisplaySettings(fullscreen=settings.fullscreen, windowed_size=settings.windowed_size)


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


def _set_display_status(loop: _DisplayMenuState, message: str, *, is_error: bool = False) -> None:
    loop.status = message
    loop.status_error = is_error


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


def _apply_display_settings_preview(screen: pygame.Surface, loop: _DisplayMenuState) -> pygame.Surface:
    return apply_display_mode(loop.settings, preferred_windowed_size=loop.settings.windowed_size)


def _save_display_settings_from_menu(screen: pygame.Surface, loop: _DisplayMenuState) -> pygame.Surface:
    loop.settings = normalize_display_settings(loop.settings)
    screen = _apply_display_settings_preview(screen, loop)
    ok, msg = save_display_settings(
        fullscreen=loop.settings.fullscreen,
        windowed_size=loop.settings.windowed_size,
    )
    _set_display_status(loop, msg, is_error=not ok)
    loop.saved = ok
    if ok:
        play_sfx("menu_confirm")
    return screen


def _reset_display_settings_from_menu(loop: _DisplayMenuState) -> None:
    loop.settings = _display_defaults()
    _set_display_status(loop, "Display reset to defaults (not saved yet)")
    play_sfx("menu_move")


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


def _handle_display_commit_key(
    screen: pygame.Surface,
    loop: _DisplayMenuState,
    key: int,
) -> tuple[pygame.Surface, bool]:
    if key == pygame.K_F8:
        _reset_display_settings_from_menu(loop)
        return screen, True
    if key == pygame.K_F5:
        return _save_display_settings_from_menu(screen, loop), True
    if key not in (pygame.K_RETURN, pygame.K_KP_ENTER):
        return screen, False
    if loop.selected == 3:
        screen = _apply_display_settings_preview(screen, loop)
        _set_display_status(loop, "Applied display mode")
        play_sfx("menu_confirm")
        return screen, True
    if loop.selected == 4:
        return _save_display_settings_from_menu(screen, loop), True
    if loop.selected == 5:
        _reset_display_settings_from_menu(loop)
        return screen, True
    if loop.selected == 6:
        loop.running = False
        return screen, True
    return screen, False


def _handle_display_menu_key(
    screen: pygame.Surface,
    loop: _DisplayMenuState,
    key: int,
) -> pygame.Surface:
    if _handle_display_navigation_key(loop, key):
        return screen
    if loop.selected == 0 and key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_RETURN, pygame.K_KP_ENTER):
        loop.settings = DisplaySettings(not loop.settings.fullscreen, loop.settings.windowed_size)
        play_sfx("menu_move")
        return screen
    if _adjust_display_window_size(loop, key):
        return screen
    screen, _handled = _handle_display_commit_key(screen, loop, key)
    return screen


def _run_display_settings_menu(
    screen: pygame.Surface,
    fonts,
    current: DisplaySettings,
) -> tuple[pygame.Surface, DisplaySettings]:
    loop = _DisplayMenuState(
        settings=_clone_display_settings(current),
        original=_clone_display_settings(current),
    )
    clock = pygame.time.Clock()

    while loop.running:
        _dt = clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return screen, current
            if event.type != pygame.KEYDOWN:
                continue
            screen = _handle_display_menu_key(screen, loop, event.key)
            if not loop.running:
                break

        _draw_display_settings_menu(screen, fonts, loop)
        pygame.display.flip()

    if not loop.saved:
        restored = normalize_display_settings(loop.original)
        screen = apply_display_mode(restored, preferred_windowed_size=restored.windowed_size)
        return screen, restored
    state = capture_windowed_display_settings(normalize_display_settings(loop.settings))
    return screen, state


def _launch_2d(
    screen: pygame.Surface,
    fonts2d,
    display_settings: DisplaySettings,
) -> tuple[pygame.Surface, DisplaySettings, bool]:
    screen = open_display(display_settings, caption="2D Tetris – Setup")
    settings = front2d.run_menu(screen, fonts2d)
    if settings is None:
        return screen, display_settings, True

    cfg = front2d.GameConfig(
        width=settings.width,
        height=settings.height,
        gravity_axis=1,
        speed_level=settings.speed_level,
        piece_set=front2d._piece_set_index_to_id(settings.piece_set_index),
    )
    board_px_w = cfg.width * 30
    board_px_h = cfg.height * 30
    suggested = (board_px_w + 200 + 60, board_px_h + 40)
    preferred_size = (
        max(display_settings.windowed_size[0], suggested[0]),
        max(display_settings.windowed_size[1], suggested[1]),
    )
    screen = open_display(
        display_settings,
        caption="2D Tetris",
        preferred_windowed_size=preferred_size,
    )

    back_to_menu = front2d.run_game_loop(screen, cfg, fonts2d)
    if not back_to_menu:
        return screen, display_settings, False
    display_settings = capture_windowed_display_settings(display_settings)
    screen = open_display(display_settings)
    return screen, display_settings, True


def _launch_3d(
    screen: pygame.Surface,
    fonts_nd,
    display_settings: DisplaySettings,
) -> tuple[pygame.Surface, DisplaySettings, bool]:
    screen = open_display(display_settings, caption="3D Tetris – Setup")
    settings = run_menu_3d(screen, fonts_nd)
    if settings is None:
        return screen, display_settings, True

    cfg = build_config_3d(settings)
    suggested = suggested_window_size_3d(cfg)
    preferred_size = (
        max(display_settings.windowed_size[0], suggested[0]),
        max(display_settings.windowed_size[1], suggested[1]),
    )
    screen = open_display(
        display_settings,
        caption="3D Tetris",
        preferred_windowed_size=preferred_size,
    )

    back_to_menu = run_game_loop_3d(screen, cfg, fonts_nd)
    if not back_to_menu:
        return screen, display_settings, False
    display_settings = capture_windowed_display_settings(display_settings)
    screen = open_display(display_settings)
    return screen, display_settings, True


def _launch_4d(
    screen: pygame.Surface,
    fonts_nd,
    display_settings: DisplaySettings,
) -> tuple[pygame.Surface, DisplaySettings, bool]:
    screen = open_display(display_settings, caption="4D Tetris – Setup")
    settings = run_menu_nd(screen, fonts_nd, 4)
    if settings is None:
        return screen, display_settings, True

    cfg = build_config_nd(settings, 4)
    suggested = suggested_window_size_4d(cfg)
    preferred_size = (
        max(display_settings.windowed_size[0], suggested[0]),
        max(display_settings.windowed_size[1], suggested[1]),
    )
    screen = open_display(
        display_settings,
        caption="4D Tetris",
        preferred_windowed_size=preferred_size,
    )

    back_to_menu = run_game_loop_4d(screen, cfg, fonts_nd)
    if not back_to_menu:
        return screen, display_settings, False
    display_settings = capture_windowed_display_settings(display_settings)
    screen = open_display(display_settings)
    return screen, display_settings, True


def _mode_from_last_mode(raw_last_mode: object) -> str:
    if not isinstance(raw_last_mode, str):
        return "2d"
    lowered = raw_last_mode.strip().lower()
    if lowered in {"2d", "3d", "4d"}:
        return lowered
    return "2d"


def _menu_index_for_mode(mode: str) -> int:
    mapping = {"2d": 0, "3d": 1, "4d": 2}
    return mapping.get(mode, 0)


@dataclass
class _LauncherSession:
    screen: pygame.Surface
    display_settings: DisplaySettings
    audio_settings: AudioSettings
    running: bool = True


def _restore_active_profile(payload: dict[str, object]) -> None:
    saved_profile = payload.get("active_profile")
    if isinstance(saved_profile, str):
        ok, _ = set_active_key_profile(saved_profile)
        if ok:
            load_active_profile_bindings()
            return
    load_active_profile_bindings()


def _persist_session_status(state: MainMenuState, session: _LauncherSession) -> None:
    ok, msg = _persist_global_state(
        display_settings=session.display_settings,
        audio_settings=session.audio_settings,
        last_mode=state.last_mode,
    )
    state.status = msg
    state.status_error = not ok


def _menu_action_play_2d(
    state: MainMenuState,
    session: _LauncherSession,
    _fonts_nd,
    fonts_2d,
) -> None:
    state.last_mode = "2d"
    session.screen, session.display_settings, keep_running = _launch_2d(
        session.screen,
        fonts_2d,
        session.display_settings,
    )
    if not keep_running:
        session.running = False
    _persist_session_status(state, session)


def _menu_action_play_3d(
    state: MainMenuState,
    session: _LauncherSession,
    fonts_nd,
    _fonts_2d,
) -> None:
    state.last_mode = "3d"
    session.screen, session.display_settings, keep_running = _launch_3d(
        session.screen,
        fonts_nd,
        session.display_settings,
    )
    if not keep_running:
        session.running = False
    _persist_session_status(state, session)


def _menu_action_play_4d(
    state: MainMenuState,
    session: _LauncherSession,
    fonts_nd,
    _fonts_2d,
) -> None:
    state.last_mode = "4d"
    session.screen, session.display_settings, keep_running = _launch_4d(
        session.screen,
        fonts_nd,
        session.display_settings,
    )
    if not keep_running:
        session.running = False
    _persist_session_status(state, session)


def _menu_action_keybindings(
    state: MainMenuState,
    session: _LauncherSession,
    fonts_nd,
    _fonts_2d,
) -> None:
    dimension = int(state.last_mode[0]) if state.last_mode in {"2d", "3d", "4d"} else 2
    run_keybindings_menu(session.screen, fonts_nd, dimension=dimension)
    load_active_profile_bindings()
    _persist_session_status(state, session)


def _menu_action_audio(
    state: MainMenuState,
    session: _LauncherSession,
    fonts_nd,
    _fonts_2d,
) -> None:
    session.audio_settings = _run_audio_settings_menu(session.screen, fonts_nd, session.audio_settings)
    set_audio_settings(
        master_volume=session.audio_settings.master_volume,
        sfx_volume=session.audio_settings.sfx_volume,
        mute=session.audio_settings.mute,
    )
    _persist_session_status(state, session)


def _menu_action_display(
    state: MainMenuState,
    session: _LauncherSession,
    fonts_nd,
    _fonts_2d,
) -> None:
    session.screen, session.display_settings = _run_display_settings_menu(
        session.screen,
        fonts_nd,
        session.display_settings,
    )
    _persist_session_status(state, session)


def _menu_action_quit(
    _state: MainMenuState,
    session: _LauncherSession,
    _fonts_nd,
    _fonts_2d,
) -> None:
    session.running = False


_MENU_ACTION_HANDLERS: dict[str, Callable[[MainMenuState, _LauncherSession, object, object], None]] = {
    "play_2d": _menu_action_play_2d,
    "play_3d": _menu_action_play_3d,
    "play_4d": _menu_action_play_4d,
    "keybindings": _menu_action_keybindings,
    "audio": _menu_action_audio,
    "display": _menu_action_display,
    "quit": _menu_action_quit,
}


def _run_menu_action(
    action: str,
    state: MainMenuState,
    session: _LauncherSession,
    fonts_nd,
    fonts_2d,
) -> None:
    handler = _MENU_ACTION_HANDLERS.get(action)
    if handler is not None:
        handler(state, session, fonts_nd, fonts_2d)


def _handle_main_menu_keydown(
    key: int,
    state: MainMenuState,
    session: _LauncherSession,
    fonts_nd,
    fonts_2d,
) -> bool:
    if key == pygame.K_ESCAPE:
        session.running = False
        return True
    if key == pygame.K_UP:
        state.selected = (state.selected - 1) % len(MENU_ITEMS)
        play_sfx("menu_move")
        return False
    if key == pygame.K_DOWN:
        state.selected = (state.selected + 1) % len(MENU_ITEMS)
        play_sfx("menu_move")
        return False
    if key not in (pygame.K_RETURN, pygame.K_KP_ENTER):
        return False

    play_sfx("menu_confirm")
    action = MENU_ITEMS[state.selected][0]
    _run_menu_action(action, state, session, fonts_nd, fonts_2d)
    return True


def run() -> None:
    runtime = initialize_runtime(sync_audio_state=True)

    payload = load_app_settings_payload()
    _restore_active_profile(payload)

    session = _LauncherSession(
        screen=open_display(
            DisplaySettings(
                fullscreen=runtime.display_settings.fullscreen,
                windowed_size=runtime.display_settings.windowed_size,
            ),
            caption="ND Tetris – Main Menu",
        ),
        display_settings=DisplaySettings(
            fullscreen=runtime.display_settings.fullscreen,
            windowed_size=runtime.display_settings.windowed_size,
        ),
        audio_settings=AudioSettings(
            master_volume=runtime.audio_settings.master_volume,
            sfx_volume=runtime.audio_settings.sfx_volume,
            mute=runtime.audio_settings.mute,
        ),
    )

    fonts_nd = init_fonts()
    fonts_2d = front2d.init_fonts()

    state = MainMenuState(
        selected=_menu_index_for_mode(_mode_from_last_mode(payload.get("last_mode"))),
        last_mode=_mode_from_last_mode(payload.get("last_mode")),
    )
    clock = pygame.time.Clock()

    while session.running:
        _dt = clock.tick(60)
        pygame.display.set_caption("ND Tetris – Main Menu")

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                session.running = False
                break
            if event.type != pygame.KEYDOWN:
                continue
            if _handle_main_menu_keydown(event.key, state, session, fonts_nd, fonts_2d):
                break

        _draw_main_menu(session.screen, fonts_nd, state)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    run()
