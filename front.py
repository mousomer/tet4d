import sys
from dataclasses import dataclass

import pygame

from tetris_nd.app_runtime import initialize_runtime, open_display
from tetris_nd.audio import AudioSettings, play_sfx
from tetris_nd.bot_options_menu import run_bot_options_menu
from tetris_nd.display import DisplaySettings
from tetris_nd.font_profiles import init_fonts as init_fonts_for_profile
from tetris_nd.help_menu import run_help_menu
from tetris_nd.keybindings import active_key_profile, load_active_profile_bindings, set_active_key_profile
from tetris_nd.keybindings_menu import run_keybindings_menu
from tetris_nd.launcher_play import launch_2d, launch_3d, launch_4d
from tetris_nd.launcher_settings import run_settings_hub_menu
from tetris_nd.menu_config import launcher_menu_id, menu_graph
from tetris_nd.menu_persistence import load_menu_payload, save_menu_payload
from tetris_nd.menu_runner import ActionRegistry, MenuRunner
from tetris_nd.ui_utils import draw_vertical_gradient, fit_text


BG_TOP = (14, 18, 44)
BG_BOTTOM = (4, 7, 20)
TEXT_COLOR = (232, 232, 240)
HIGHLIGHT_COLOR = (255, 224, 128)
MUTED_COLOR = (192, 200, 228)

_MENU_GRAPH = menu_graph()
_LAUNCHER_ROOT_MENU_ID = launcher_menu_id()


@dataclass
class MainMenuState:
    status: str = ""
    status_error: bool = False
    last_mode: str = "2d"


@dataclass
class _LauncherSession:
    screen: pygame.Surface
    display_settings: DisplaySettings
    audio_settings: AudioSettings
    running: bool = True


def _menu_items(menu_id: str) -> tuple[dict[str, str], ...]:
    menu = _MENU_GRAPH.get(menu_id)
    if menu is None:
        return tuple()
    raw_items = menu.get("items")
    if not isinstance(raw_items, tuple):
        return tuple()
    return raw_items


def _play_menu_id() -> str | None:
    for item in _menu_items(_LAUNCHER_ROOT_MENU_ID):
        if item.get("type") != "submenu":
            continue
        label = str(item.get("label", "")).strip().lower()
        if label == "play":
            return str(item.get("menu_id", "")).strip().lower() or None
    return None


def _menu_subtitle(menu_id: str) -> str:
    if menu_id == _LAUNCHER_ROOT_MENU_ID:
        return "Play or continue, then adjust Settings, Controls, Help, and Bot options."
    if menu_id == _play_menu_id():
        return "Select a dimension; Tutorials and Topology Lab are routed here without top-level growth."
    return "Up/Down select and Enter open actions."


def _draw_main_menu(
    screen: pygame.Surface,
    fonts,
    state: MainMenuState,
    *,
    menu_title: str,
    menu_id: str,
    items: tuple[dict[str, str], ...],
    selected_index: int,
    stack_depth: int,
) -> None:
    draw_vertical_gradient(screen, BG_TOP, BG_BOTTOM)
    width, height = screen.get_size()
    title = fonts.title_font.render(menu_title, True, TEXT_COLOR)
    subtitle_text = fit_text(
        fonts.hint_font,
        _menu_subtitle(menu_id),
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
    row_count = max(1, len(items))
    max_panel_h = max(120, height - top_reserved - bottom_reserved - 10)
    row_step = min(52, max(fonts.menu_font.get_height() + 8, (max_panel_h - 48) // row_count))
    panel_h = min(max_panel_h, 48 + row_count * row_step)
    panel_x = (width - panel_w) // 2
    panel_y = max(top_reserved, min((height - panel_h) // 2, height - bottom_reserved - panel_h - 8))

    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (0, 0, 0, 152), panel.get_rect(), border_radius=14)
    screen.blit(panel, (panel_x, panel_y))

    y = panel_y + 20
    row_margin = 28
    row_right = panel_x + panel_w - row_margin
    for idx, item in enumerate(items):
        label = str(item.get("label", ""))
        selected = idx == selected_index
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

    escape_hint = "Esc back" if stack_depth > 1 else "Esc quit"
    info_lines = [
        f"Active key profile: {active_key_profile()}",
        f"Continue mode: {state.last_mode.upper()}",
        f"Up/Down select   Enter open   {escape_hint}",
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


def _menu_index_for_root_action(action: str, fallback: int = 0) -> int:
    for idx, item in enumerate(_menu_items(_LAUNCHER_ROOT_MENU_ID)):
        if item.get("type") != "action":
            continue
        if str(item.get("action_id", "")).strip().lower() == action:
            return idx
    return fallback


def _menu_index_for_root_play_submenu(fallback: int = 0) -> int:
    for idx, item in enumerate(_menu_items(_LAUNCHER_ROOT_MENU_ID)):
        if item.get("type") != "submenu":
            continue
        label = str(item.get("label", "")).strip().lower()
        if label == "play":
            return idx
    return fallback


def _menu_index_for_mode(mode: str) -> int:
    continue_index = _menu_index_for_root_action("continue", -1)
    if continue_index >= 0:
        return continue_index
    play_index = _menu_index_for_root_play_submenu(-1)
    if play_index >= 0:
        return play_index
    return _menu_index_for_root_action(f"play_{mode}", 0)


def _menu_index_for_play_mode(mode: str, fallback: int = 0) -> int:
    play_menu_id = _play_menu_id()
    if not play_menu_id:
        return fallback
    target = f"play_{mode}"
    for idx, item in enumerate(_menu_items(play_menu_id)):
        if item.get("type") != "action":
            continue
        if str(item.get("action_id", "")).strip().lower() == target:
            return idx
    return fallback


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


def _launch_mode(
    mode: str,
    state: MainMenuState,
    session: _LauncherSession,
    fonts_nd,
    fonts_2d,
) -> None:
    launchers = {
        "2d": lambda: launch_2d(session.screen, fonts_2d, session.display_settings),
        "3d": lambda: launch_3d(session.screen, fonts_nd, session.display_settings),
        "4d": lambda: launch_4d(session.screen, fonts_nd, session.display_settings),
    }
    launcher = launchers.get(mode)
    if launcher is None:
        state.status = f"Unsupported mode: {mode}"
        state.status_error = True
        return
    state.last_mode = mode
    result = launcher()
    session.screen = result.screen
    session.display_settings = result.display_settings
    if not result.keep_running:
        session.running = False
        return
    _persist_session_status(state, session)


def _menu_action_continue(
    state: MainMenuState,
    session: _LauncherSession,
    fonts_nd,
    fonts_2d,
) -> bool:
    _launch_mode(state.last_mode, state, session, fonts_nd, fonts_2d)
    return not session.running


def _menu_action_play_dimension(
    mode: str,
    state: MainMenuState,
    session: _LauncherSession,
    fonts_nd,
    fonts_2d,
) -> bool:
    _launch_mode(mode, state, session, fonts_nd, fonts_2d)
    return not session.running


def _menu_action_keybindings(
    state: MainMenuState,
    session: _LauncherSession,
    fonts_nd,
) -> bool:
    dimension = int(state.last_mode[0]) if state.last_mode in {"2d", "3d", "4d"} else 2
    run_keybindings_menu(session.screen, fonts_nd, dimension=dimension, scope="general")
    load_active_profile_bindings()
    _persist_session_status(state, session)
    return not session.running


def _menu_action_settings(
    state: MainMenuState,
    session: _LauncherSession,
    fonts_nd,
) -> bool:
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
        return True
    _persist_session_status(state, session)
    return False


def _menu_action_help(
    state: MainMenuState,
    session: _LauncherSession,
    fonts_nd,
) -> bool:
    dimension = int(state.last_mode[0]) if state.last_mode in {"2d", "3d", "4d"} else 2
    session.screen = run_help_menu(
        session.screen,
        fonts_nd,
        dimension=dimension,
        context_label="Launcher",
    )
    return False


def _menu_action_quit(
    _state: MainMenuState,
    session: _LauncherSession,
) -> bool:
    session.running = False
    return True


def _menu_action_bot_options(
    state: MainMenuState,
    session: _LauncherSession,
    fonts_nd,
) -> bool:
    start_dimension = int(state.last_mode[0]) if state.last_mode in {"2d", "3d", "4d"} else 2
    ok, msg = run_bot_options_menu(session.screen, fonts_nd, start_dimension=start_dimension)
    _persist_session_status(state, session)
    state.status = msg
    state.status_error = not ok
    return not session.running


def _build_action_registry(
    state: MainMenuState,
    session: _LauncherSession,
    fonts_nd,
    fonts_2d,
) -> ActionRegistry:
    registry = ActionRegistry()
    registry.register("play", lambda: _menu_action_continue(state, session, fonts_nd, fonts_2d))
    registry.register("play_2d", lambda: _menu_action_play_dimension("2d", state, session, fonts_nd, fonts_2d))
    registry.register("play_3d", lambda: _menu_action_play_dimension("3d", state, session, fonts_nd, fonts_2d))
    registry.register("play_4d", lambda: _menu_action_play_dimension("4d", state, session, fonts_nd, fonts_2d))
    registry.register("continue", lambda: _menu_action_continue(state, session, fonts_nd, fonts_2d))
    registry.register("help", lambda: _menu_action_help(state, session, fonts_nd))
    registry.register("settings", lambda: _menu_action_settings(state, session, fonts_nd))
    registry.register("keybindings", lambda: _menu_action_keybindings(state, session, fonts_nd))
    registry.register("bot_options", lambda: _menu_action_bot_options(state, session, fonts_nd))
    registry.register("quit", lambda: _menu_action_quit(state, session))
    return registry


def _handle_launcher_route(route_id: str, state: MainMenuState) -> bool:
    route_labels = {
        "tutorials": "Tutorials",
        "topology_lab": "Topology Lab",
    }
    label = route_labels.get(route_id, route_id)
    state.status = f"{label} route is not implemented yet"
    state.status_error = False
    return False


def _handle_missing_action(action_id: str, state: MainMenuState) -> bool:
    state.status = f"No handler registered for action '{action_id}'"
    state.status_error = True
    return False


def _play_move_sfx() -> bool:
    play_sfx("menu_move")
    return False


def _play_confirm_sfx() -> bool:
    play_sfx("menu_confirm")
    return False


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

    fonts_nd = init_fonts_for_profile("nd")
    fonts_2d = init_fonts_for_profile("2d")

    state = MainMenuState(
        last_mode=_mode_from_last_mode(payload.get("last_mode")),
    )
    registry = _build_action_registry(state, session, fonts_nd, fonts_2d)

    initial_selected = {
        _LAUNCHER_ROOT_MENU_ID: _menu_index_for_mode(state.last_mode),
    }
    play_menu_id = _play_menu_id()
    if play_menu_id:
        initial_selected[play_menu_id] = _menu_index_for_play_mode(state.last_mode)

    def _render_launcher_menu(
        menu_id: str,
        title: str,
        items: tuple[dict[str, str], ...],
        selected: int,
        depth: int,
    ) -> None:
        pygame.display.set_caption("ND Tetris – Main Menu")
        _draw_main_menu(
            session.screen,
            fonts_nd,
            state,
            menu_title=title,
            menu_id=menu_id,
            items=items,
            selected_index=selected,
            stack_depth=depth,
        )
        pygame.display.flip()

    runner = MenuRunner(
        menus=_MENU_GRAPH,
        start_menu_id=_LAUNCHER_ROOT_MENU_ID,
        action_registry=registry,
        render_menu=_render_launcher_menu,
        handle_route=lambda route_id: _handle_launcher_route(route_id, state),
        handle_missing_action=lambda action_id: _handle_missing_action(action_id, state),
        on_root_escape=lambda: _menu_action_quit(state, session),
        on_quit_event=lambda: _menu_action_quit(state, session),
        on_move=_play_move_sfx,
        on_confirm=_play_confirm_sfx,
        initial_selected=initial_selected,
    )
    runner.run()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    run()
