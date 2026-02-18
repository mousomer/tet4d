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
from tetris_nd.menu_gif_guides import draw_translation_rotation_guides
from tetris_nd.menu_persistence import load_menu_payload, save_menu_payload


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
        "Play modes plus Help, unified Settings, Keybindings, and Bot Options.",
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

    guide_h = 118
    guide_w = min(460, width - 40)
    guide_y = min(height - guide_h - 44, info_y + 6)
    if guide_y + guide_h < height - 20:
        guide_rect = pygame.Rect((width - guide_w) // 2, guide_y, guide_w, guide_h)
        draw_translation_rotation_guides(screen, fonts, rect=guide_rect, title="Translation / Rotation")
        info_y = guide_rect.bottom + 4

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
