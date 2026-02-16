import sys
from dataclasses import dataclass

import pygame

import front2d
from tetris_nd.audio import AudioSettings, initialize_audio, play_sfx, set_audio_settings
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
    initialize_keybinding_files,
    load_active_profile_bindings,
    set_active_key_profile,
)
from tetris_nd.keybindings_menu import run_keybindings_menu
from tetris_nd.menu_settings_state import (
    DEFAULT_WINDOWED_SIZE,
    get_audio_settings,
    get_display_settings,
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


def _capture_windowed_size(display_settings: DisplaySettings) -> DisplaySettings:
    if display_settings.fullscreen:
        return display_settings
    surface = pygame.display.get_surface()
    if surface is None:
        return display_settings
    width, height = surface.get_size()
    if width < 640 or height < 480:
        return display_settings
    updated = DisplaySettings(fullscreen=False, windowed_size=(width, height))
    save_display_settings(windowed_size=updated.windowed_size)
    return updated


def _audio_defaults() -> AudioSettings:
    return AudioSettings(master_volume=0.8, sfx_volume=0.7, mute=False)


def _display_defaults() -> DisplaySettings:
    return DisplaySettings(fullscreen=False, windowed_size=DEFAULT_WINDOWED_SIZE)


def _run_audio_settings_menu(screen: pygame.Surface, fonts, current: AudioSettings) -> AudioSettings:
    state = AudioSettings(
        master_volume=current.master_volume,
        sfx_volume=current.sfx_volume,
        mute=current.mute,
    )
    original = AudioSettings(
        master_volume=current.master_volume,
        sfx_volume=current.sfx_volume,
        mute=current.mute,
    )
    selected = 0
    status = ""
    status_error = False

    rows = ("Master volume", "SFX volume", "Mute", "Save", "Reset defaults", "Back")
    clock = pygame.time.Clock()
    running = True
    saved = False

    while running:
        _dt = clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return current
            if event.type != pygame.KEYDOWN:
                continue

            if event.key == pygame.K_ESCAPE:
                running = False
                break
            if event.key == pygame.K_UP:
                selected = (selected - 1) % len(rows)
                play_sfx("menu_move")
                continue
            if event.key == pygame.K_DOWN:
                selected = (selected + 1) % len(rows)
                play_sfx("menu_move")
                continue

            if selected == 0 and event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                delta = -0.05 if event.key == pygame.K_LEFT else 0.05
                state.master_volume = max(0.0, min(1.0, state.master_volume + delta))
                set_audio_settings(
                    master_volume=state.master_volume,
                    sfx_volume=state.sfx_volume,
                    mute=state.mute,
                )
                play_sfx("menu_move")
                continue
            if selected == 1 and event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                delta = -0.05 if event.key == pygame.K_LEFT else 0.05
                state.sfx_volume = max(0.0, min(1.0, state.sfx_volume + delta))
                set_audio_settings(
                    master_volume=state.master_volume,
                    sfx_volume=state.sfx_volume,
                    mute=state.mute,
                )
                play_sfx("menu_move")
                continue
            if selected == 2 and event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_RETURN, pygame.K_KP_ENTER):
                state.mute = not state.mute
                set_audio_settings(
                    master_volume=state.master_volume,
                    sfx_volume=state.sfx_volume,
                    mute=state.mute,
                )
                play_sfx("menu_move")
                continue

            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_F5):
                if selected == 3 or event.key == pygame.K_F5:
                    ok, msg = save_audio_settings(
                        master_volume=state.master_volume,
                        sfx_volume=state.sfx_volume,
                        mute=state.mute,
                    )
                    status = msg
                    status_error = not ok
                    saved = ok
                    if ok:
                        play_sfx("menu_confirm")
                    continue
                if selected == 4:
                    state = _audio_defaults()
                    set_audio_settings(
                        master_volume=state.master_volume,
                        sfx_volume=state.sfx_volume,
                        mute=state.mute,
                    )
                    status = "Audio reset to defaults (not saved yet)"
                    status_error = False
                    play_sfx("menu_move")
                    continue
                if selected == 5:
                    running = False
                    break

            if event.key == pygame.K_F8:
                state = _audio_defaults()
                set_audio_settings(
                    master_volume=state.master_volume,
                    sfx_volume=state.sfx_volume,
                    mute=state.mute,
                )
                status = "Audio reset to defaults (not saved yet)"
                status_error = False

        _draw_gradient(screen)
        width, height = screen.get_size()
        title = fonts.title_font.render("Audio Settings", True, TEXT_COLOR)
        screen.blit(title, ((width - title.get_width()) // 2, 40))

        values = (
            f"{int(state.master_volume * 100)}%",
            f"{int(state.sfx_volume * 100)}%",
            "ON" if state.mute else "OFF",
            "",
            "",
            "",
        )
        panel_w = min(560, width - 40)
        panel_h = 360
        panel_x = (width - panel_w) // 2
        panel_y = max(120, (height - panel_h) // 2)
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel, (0, 0, 0, 150), panel.get_rect(), border_radius=12)
        screen.blit(panel, (panel_x, panel_y))

        y = panel_y + 20
        for idx, row in enumerate(rows):
            selected_row = idx == selected
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

        hints = [
            "Left/Right adjust values   Enter activate row",
            "F5 save   F8 reset defaults   Esc back",
        ]
        hy = panel_y + panel_h + 12
        for line in hints:
            surf = fonts.hint_font.render(line, True, MUTED_COLOR)
            screen.blit(surf, ((width - surf.get_width()) // 2, hy))
            hy += surf.get_height() + 3

        if status:
            color = (255, 150, 150) if status_error else (170, 240, 170)
            surf = fonts.hint_font.render(status, True, color)
            screen.blit(surf, ((width - surf.get_width()) // 2, hy + 2))

        pygame.display.flip()

    if not saved:
        set_audio_settings(
            master_volume=original.master_volume,
            sfx_volume=original.sfx_volume,
            mute=original.mute,
        )
        return original
    return state


def _run_display_settings_menu(
    screen: pygame.Surface,
    fonts,
    current: DisplaySettings,
) -> tuple[pygame.Surface, DisplaySettings]:
    state = DisplaySettings(fullscreen=current.fullscreen, windowed_size=current.windowed_size)
    original = DisplaySettings(fullscreen=current.fullscreen, windowed_size=current.windowed_size)
    selected = 0
    status = ""
    status_error = False
    saved = False
    rows = ("Fullscreen", "Window width", "Window height", "Apply", "Save", "Reset defaults", "Back")
    clock = pygame.time.Clock()
    running = True

    while running:
        _dt = clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return screen, current
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
                running = False
                break
            if event.key == pygame.K_UP:
                selected = (selected - 1) % len(rows)
                play_sfx("menu_move")
                continue
            if event.key == pygame.K_DOWN:
                selected = (selected + 1) % len(rows)
                play_sfx("menu_move")
                continue
            if selected == 0 and event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_RETURN, pygame.K_KP_ENTER):
                state.fullscreen = not state.fullscreen
                play_sfx("menu_move")
                continue
            if selected in (1, 2) and event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                delta = -40 if event.key == pygame.K_LEFT else 40
                width, height = state.windowed_size
                if selected == 1:
                    width = max(640, width + delta)
                else:
                    height = max(480, height + delta)
                state = DisplaySettings(state.fullscreen, (width, height))
                play_sfx("menu_move")
                continue

            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_F5):
                if selected == 3:
                    screen = apply_display_mode(state, preferred_windowed_size=state.windowed_size)
                    status = "Applied display mode"
                    status_error = False
                    play_sfx("menu_confirm")
                    continue
                if selected == 4 or event.key == pygame.K_F5:
                    state = normalize_display_settings(state)
                    screen = apply_display_mode(state, preferred_windowed_size=state.windowed_size)
                    ok, msg = save_display_settings(
                        fullscreen=state.fullscreen,
                        windowed_size=state.windowed_size,
                    )
                    status = msg
                    status_error = not ok
                    saved = ok
                    if ok:
                        play_sfx("menu_confirm")
                    continue
                if selected == 5:
                    state = _display_defaults()
                    status = "Display reset to defaults (not saved yet)"
                    status_error = False
                    play_sfx("menu_move")
                    continue
                if selected == 6:
                    running = False
                    break

            if event.key == pygame.K_F8:
                state = _display_defaults()
                status = "Display reset to defaults (not saved yet)"
                status_error = False

        _draw_gradient(screen)
        width, height = screen.get_size()
        title = fonts.title_font.render("Display Settings", True, TEXT_COLOR)
        screen.blit(title, ((width - title.get_width()) // 2, 40))

        values = (
            "ON" if state.fullscreen else "OFF",
            str(state.windowed_size[0]),
            str(state.windowed_size[1]),
            "",
            "",
            "",
            "",
        )
        panel_w = min(560, width - 40)
        panel_h = 400
        panel_x = (width - panel_w) // 2
        panel_y = max(120, (height - panel_h) // 2)
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel, (0, 0, 0, 150), panel.get_rect(), border_radius=12)
        screen.blit(panel, (panel_x, panel_y))

        y = panel_y + 20
        for idx, row in enumerate(rows):
            selected_row = idx == selected
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

        hints = [
            "Apply to preview mode change; Save to persist",
            "F5 save   F8 reset defaults   Esc back",
        ]
        hy = panel_y + panel_h + 12
        for line in hints:
            surf = fonts.hint_font.render(line, True, MUTED_COLOR)
            screen.blit(surf, ((width - surf.get_width()) // 2, hy))
            hy += surf.get_height() + 3

        if status:
            color = (255, 150, 150) if status_error else (170, 240, 170)
            surf = fonts.hint_font.render(status, True, color)
            screen.blit(surf, ((width - surf.get_width()) // 2, hy + 2))

        pygame.display.flip()

    if not saved:
        restored = normalize_display_settings(original)
        screen = apply_display_mode(restored, preferred_windowed_size=restored.windowed_size)
        return screen, restored
    state = _capture_windowed_size(normalize_display_settings(state))
    return screen, state


def _launch_2d(
    screen: pygame.Surface,
    fonts2d,
    display_settings: DisplaySettings,
) -> tuple[pygame.Surface, DisplaySettings, bool]:
    pygame.display.set_caption("2D Tetris – Setup")
    screen = apply_display_mode(display_settings, preferred_windowed_size=display_settings.windowed_size)
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
    pygame.display.set_caption("2D Tetris")
    screen = apply_display_mode(display_settings, preferred_windowed_size=preferred_size)

    back_to_menu = front2d.run_game_loop(screen, cfg, fonts2d)
    if not back_to_menu:
        return screen, display_settings, False
    display_settings = _capture_windowed_size(display_settings)
    screen = apply_display_mode(display_settings, preferred_windowed_size=display_settings.windowed_size)
    return screen, display_settings, True


def _launch_3d(
    screen: pygame.Surface,
    fonts_nd,
    display_settings: DisplaySettings,
) -> tuple[pygame.Surface, DisplaySettings, bool]:
    pygame.display.set_caption("3D Tetris – Setup")
    screen = apply_display_mode(display_settings, preferred_windowed_size=display_settings.windowed_size)
    settings = run_menu_3d(screen, fonts_nd)
    if settings is None:
        return screen, display_settings, True

    cfg = build_config_3d(settings)
    suggested = suggested_window_size_3d(cfg)
    preferred_size = (
        max(display_settings.windowed_size[0], suggested[0]),
        max(display_settings.windowed_size[1], suggested[1]),
    )
    pygame.display.set_caption("3D Tetris")
    screen = apply_display_mode(display_settings, preferred_windowed_size=preferred_size)

    back_to_menu = run_game_loop_3d(screen, cfg, fonts_nd)
    if not back_to_menu:
        return screen, display_settings, False
    display_settings = _capture_windowed_size(display_settings)
    screen = apply_display_mode(display_settings, preferred_windowed_size=display_settings.windowed_size)
    return screen, display_settings, True


def _launch_4d(
    screen: pygame.Surface,
    fonts_nd,
    display_settings: DisplaySettings,
) -> tuple[pygame.Surface, DisplaySettings, bool]:
    pygame.display.set_caption("4D Tetris – Setup")
    screen = apply_display_mode(display_settings, preferred_windowed_size=display_settings.windowed_size)
    settings = run_menu_nd(screen, fonts_nd, 4)
    if settings is None:
        return screen, display_settings, True

    cfg = build_config_nd(settings, 4)
    suggested = suggested_window_size_4d(cfg)
    preferred_size = (
        max(display_settings.windowed_size[0], suggested[0]),
        max(display_settings.windowed_size[1], suggested[1]),
    )
    pygame.display.set_caption("4D Tetris")
    screen = apply_display_mode(display_settings, preferred_windowed_size=preferred_size)

    back_to_menu = run_game_loop_4d(screen, cfg, fonts_nd)
    if not back_to_menu:
        return screen, display_settings, False
    display_settings = _capture_windowed_size(display_settings)
    screen = apply_display_mode(display_settings, preferred_windowed_size=display_settings.windowed_size)
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


def run() -> None:
    pygame.init()
    initialize_keybinding_files()

    payload = load_app_settings_payload()
    saved_profile = payload.get("active_profile")
    if isinstance(saved_profile, str):
        ok, _ = set_active_key_profile(saved_profile)
        if ok:
            load_active_profile_bindings()
    else:
        load_active_profile_bindings()

    audio_payload = get_audio_settings()
    audio_settings = AudioSettings(
        master_volume=audio_payload["master_volume"],
        sfx_volume=audio_payload["sfx_volume"],
        mute=audio_payload["mute"],
    )
    initialize_audio(audio_settings)
    set_audio_settings(
        master_volume=audio_settings.master_volume,
        sfx_volume=audio_settings.sfx_volume,
        mute=audio_settings.mute,
    )

    display_payload = get_display_settings()
    display_settings = normalize_display_settings(
        DisplaySettings(
            fullscreen=display_payload["fullscreen"],
            windowed_size=tuple(display_payload["windowed_size"]),
        )
    )
    screen = apply_display_mode(display_settings, preferred_windowed_size=display_settings.windowed_size)

    fonts_nd = init_fonts()
    fonts_2d = front2d.init_fonts()

    state = MainMenuState(
        selected=_menu_index_for_mode(_mode_from_last_mode(payload.get("last_mode"))),
        last_mode=_mode_from_last_mode(payload.get("last_mode")),
    )
    clock = pygame.time.Clock()

    running = True
    while running:
        _dt = clock.tick(60)
        pygame.display.set_caption("ND Tetris – Main Menu")

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    break
                if event.key == pygame.K_UP:
                    state.selected = (state.selected - 1) % len(MENU_ITEMS)
                    play_sfx("menu_move")
                    continue
                if event.key == pygame.K_DOWN:
                    state.selected = (state.selected + 1) % len(MENU_ITEMS)
                    play_sfx("menu_move")
                    continue
                if event.key not in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    continue

                play_sfx("menu_confirm")
                action = MENU_ITEMS[state.selected][0]
                if action == "quit":
                    running = False
                    break
                if action == "play_2d":
                    state.last_mode = "2d"
                    screen, display_settings, keep_running = _launch_2d(screen, fonts_2d, display_settings)
                    if not keep_running:
                        running = False
                    _persist_global_state(
                        display_settings=display_settings,
                        audio_settings=audio_settings,
                        last_mode=state.last_mode,
                    )
                    break
                if action == "play_3d":
                    state.last_mode = "3d"
                    screen, display_settings, keep_running = _launch_3d(screen, fonts_nd, display_settings)
                    if not keep_running:
                        running = False
                    _persist_global_state(
                        display_settings=display_settings,
                        audio_settings=audio_settings,
                        last_mode=state.last_mode,
                    )
                    break
                if action == "play_4d":
                    state.last_mode = "4d"
                    screen, display_settings, keep_running = _launch_4d(screen, fonts_nd, display_settings)
                    if not keep_running:
                        running = False
                    _persist_global_state(
                        display_settings=display_settings,
                        audio_settings=audio_settings,
                        last_mode=state.last_mode,
                    )
                    break
                if action == "keybindings":
                    dimension = int(state.last_mode[0]) if state.last_mode in {"2d", "3d", "4d"} else 2
                    run_keybindings_menu(screen, fonts_nd, dimension=dimension)
                    load_active_profile_bindings()
                    ok, msg = _persist_global_state(
                        display_settings=display_settings,
                        audio_settings=audio_settings,
                        last_mode=state.last_mode,
                    )
                    state.status = msg
                    state.status_error = not ok
                    break
                if action == "audio":
                    audio_settings = _run_audio_settings_menu(screen, fonts_nd, audio_settings)
                    set_audio_settings(
                        master_volume=audio_settings.master_volume,
                        sfx_volume=audio_settings.sfx_volume,
                        mute=audio_settings.mute,
                    )
                    ok, msg = _persist_global_state(
                        display_settings=display_settings,
                        audio_settings=audio_settings,
                        last_mode=state.last_mode,
                    )
                    state.status = msg
                    state.status_error = not ok
                    break
                if action == "display":
                    screen, display_settings = _run_display_settings_menu(screen, fonts_nd, display_settings)
                    ok, msg = _persist_global_state(
                        display_settings=display_settings,
                        audio_settings=audio_settings,
                        last_mode=state.last_mode,
                    )
                    state.status = msg
                    state.status_error = not ok
                    break

        _draw_main_menu(screen, fonts_nd, state)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    run()
