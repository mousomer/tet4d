import sys
from collections.abc import Callable
from dataclasses import dataclass

import pygame

import front2d
from tetris_nd.app_runtime import initialize_runtime, open_display
from tetris_nd.audio import AudioSettings, play_sfx
from tetris_nd.bot_options_menu import run_bot_options_menu
from tetris_nd.display import DisplaySettings
from tetris_nd.frontend_nd import init_fonts
from tetris_nd.help_menu import run_help_menu
from tetris_nd.keybindings import active_key_profile, load_active_profile_bindings, set_active_key_profile
from tetris_nd.keybindings_menu import run_keybindings_menu
from tetris_nd.launcher_play import launch_2d, launch_3d, launch_4d
from tetris_nd.launcher_settings import run_settings_hub_menu
from tetris_nd.menu_config import launcher_menu_items
from tetris_nd.menu_persistence import load_menu_payload, save_menu_payload
from tetris_nd.ui_utils import draw_vertical_gradient, fit_text


BG_TOP = (14, 18, 44)
BG_BOTTOM = (4, 7, 20)
TEXT_COLOR = (232, 232, 240)
HIGHLIGHT_COLOR = (255, 224, 128)
MUTED_COLOR = (192, 200, 228)

MENU_ITEMS = (*launcher_menu_items(),)


@dataclass
class MainMenuState:
    selected: int = 0
    status: str = ""
    status_error: bool = False
    last_mode: str = "2d"


@dataclass
class _LauncherSession:
    screen: pygame.Surface
    display_settings: DisplaySettings
    audio_settings: AudioSettings
    running: bool = True


def _draw_main_menu(screen: pygame.Surface, fonts, state: MainMenuState) -> None:
    draw_vertical_gradient(screen, BG_TOP, BG_BOTTOM)
    width, height = screen.get_size()
    title = fonts.title_font.render("ND Tetris Launcher", True, TEXT_COLOR)
    subtitle_text = fit_text(
        fonts.hint_font,
        "Play modes plus Help, unified Settings, Keybindings, and Bot Options.",
        width - 32,
    )
    subtitle = fonts.hint_font.render(subtitle_text, True, MUTED_COLOR)
    title_y = 40
    subtitle_y = title_y + title.get_height() + 8
    screen.blit(title, ((width - title.get_width()) // 2, title_y))
    screen.blit(subtitle, ((width - subtitle.get_width()) // 2, subtitle_y))

    hint_line_h = fonts.hint_font.get_height() + 3
    bottom_lines = 3 + (1 if state.status else 0)
    bottom_reserved = bottom_lines * hint_line_h + 14
    top_reserved = subtitle_y + subtitle.get_height() + 14
    panel_w = min(620, max(320, width - 40))
    max_panel_h = max(120, height - top_reserved - bottom_reserved - 10)
    row_step = min(52, max(fonts.menu_font.get_height() + 8, (max_panel_h - 48) // max(1, len(MENU_ITEMS))))
    panel_h = min(max_panel_h, 48 + len(MENU_ITEMS) * row_step)
    panel_x = (width - panel_w) // 2
    panel_y = max(top_reserved, min((height - panel_h) // 2, height - bottom_reserved - panel_h - 8))

    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (0, 0, 0, 152), panel.get_rect(), border_radius=14)
    screen.blit(panel, (panel_x, panel_y))

    y = panel_y + 20
    row_margin = 28
    row_right = panel_x + panel_w - row_margin
    for idx, (_, label) in enumerate(MENU_ITEMS):
        selected = idx == state.selected
        color = HIGHLIGHT_COLOR if selected else TEXT_COLOR
        label_text = fit_text(fonts.menu_font, label, row_right - (panel_x + row_margin))
        text = fonts.menu_font.render(label_text, True, color)
        row_rect = text.get_rect(topleft=(panel_x + row_margin, y))
        if selected:
            hi = pygame.Surface((panel_w - 32, row_rect.height + 10), pygame.SRCALPHA)
            pygame.draw.rect(hi, (255, 255, 255, 38), hi.get_rect(), border_radius=9)
            screen.blit(hi, (panel_x + 16, y - 4))
        screen.blit(text, row_rect.topleft)
        y += row_step

    info_lines = [
        f"Active key profile: {active_key_profile()}",
        f"Last mode: {state.last_mode.upper()}",
        "Up/Down select   Enter open   Esc quit",
    ]
    info_y = panel_y + panel_h + 10
    max_bottom_lines = max(1, (height - info_y - 8) // max(1, hint_line_h))
    info_budget = max(1, max_bottom_lines - (1 if state.status else 0))
    for line in info_lines[:info_budget]:
        line_draw = fit_text(fonts.hint_font, line, width - 24)
        text = fonts.hint_font.render(line_draw, True, MUTED_COLOR)
        screen.blit(text, ((width - text.get_width()) // 2, info_y))
        info_y += text.get_height() + 3

    if state.status and info_y + hint_line_h <= height - 6:
        status_color = (255, 150, 150) if state.status_error else (170, 240, 170)
        status_text = fit_text(fonts.hint_font, state.status, width - 24)
        status = fonts.hint_font.render(status_text, True, status_color)
        screen.blit(status, ((width - status.get_width()) // 2, min(height - 34, info_y + 2)))


def _persist_global_state(
    *,
    display_settings: DisplaySettings,
    audio_settings: AudioSettings,
    last_mode: str,
) -> tuple[bool, str]:
    payload = load_menu_payload()
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
    return save_menu_payload(payload)


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
    if ok:
        state.status = "Autosaved"
        state.status_error = False
    else:
        state.status = f"Autosave failed: {msg}"
        state.status_error = True


def _menu_action_play_2d(
    state: MainMenuState,
    session: _LauncherSession,
    _fonts_nd,
    fonts_2d,
) -> None:
    state.last_mode = "2d"
    result = launch_2d(session.screen, fonts_2d, session.display_settings)
    session.screen = result.screen
    session.display_settings = result.display_settings
    if not result.keep_running:
        session.running = False
    _persist_session_status(state, session)


def _menu_action_play_3d(
    state: MainMenuState,
    session: _LauncherSession,
    fonts_nd,
    _fonts_2d,
) -> None:
    state.last_mode = "3d"
    result = launch_3d(session.screen, fonts_nd, session.display_settings)
    session.screen = result.screen
    session.display_settings = result.display_settings
    if not result.keep_running:
        session.running = False
    _persist_session_status(state, session)


def _menu_action_play_4d(
    state: MainMenuState,
    session: _LauncherSession,
    fonts_nd,
    _fonts_2d,
) -> None:
    state.last_mode = "4d"
    result = launch_4d(session.screen, fonts_nd, session.display_settings)
    session.screen = result.screen
    session.display_settings = result.display_settings
    if not result.keep_running:
        session.running = False
    _persist_session_status(state, session)


def _menu_action_keybindings(
    state: MainMenuState,
    session: _LauncherSession,
    fonts_nd,
    _fonts_2d,
) -> None:
    dimension = int(state.last_mode[0]) if state.last_mode in {"2d", "3d", "4d"} else 2
    run_keybindings_menu(session.screen, fonts_nd, dimension=dimension, scope="all")
    load_active_profile_bindings()
    _persist_session_status(state, session)


def _menu_action_settings(
    state: MainMenuState,
    session: _LauncherSession,
    fonts_nd,
    _fonts_2d,
) -> None:
    result = run_settings_hub_menu(
        session.screen,
        fonts_nd,
        audio_settings=session.audio_settings,
        display_settings=session.display_settings,
    )
    session.screen = result.screen
    session.audio_settings = result.audio_settings
    session.display_settings = result.display_settings
    if not result.keep_running:
        session.running = False
        return
    _persist_session_status(state, session)


def _menu_action_help(
    state: MainMenuState,
    session: _LauncherSession,
    fonts_nd,
    _fonts_2d,
) -> None:
    dimension = int(state.last_mode[0]) if state.last_mode in {"2d", "3d", "4d"} else 2
    session.screen = run_help_menu(
        session.screen,
        fonts_nd,
        dimension=dimension,
        context_label="Launcher",
    )
    play_sfx("menu_confirm")


def _menu_action_quit(
    _state: MainMenuState,
    session: _LauncherSession,
    _fonts_nd,
    _fonts_2d,
) -> None:
    session.running = False


def _menu_action_bot_options(
    state: MainMenuState,
    session: _LauncherSession,
    fonts_nd,
    _fonts_2d,
) -> None:
    start_dimension = int(state.last_mode[0]) if state.last_mode in {"2d", "3d", "4d"} else 2
    ok, msg = run_bot_options_menu(session.screen, fonts_nd, start_dimension=start_dimension)
    _persist_session_status(state, session)
    state.status = msg
    state.status_error = not ok


_MENU_ACTION_HANDLERS: dict[str, Callable[[MainMenuState, _LauncherSession, object, object], None]] = {
    "play_2d": _menu_action_play_2d,
    "play_3d": _menu_action_play_3d,
    "play_4d": _menu_action_play_4d,
    "help": _menu_action_help,
    "settings": _menu_action_settings,
    "keybindings": _menu_action_keybindings,
    "bot_options": _menu_action_bot_options,
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

    payload = load_menu_payload()
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
