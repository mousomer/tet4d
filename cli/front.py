# ruff: noqa: E402
import argparse
import sys
from pathlib import Path
from dataclasses import dataclass
from types import SimpleNamespace


def _parse_cli_args(argv=None):
    parser = argparse.ArgumentParser(
        prog=Path(__file__).name,
        description="tet4d unified launcher",
    )
    parser.add_argument(
        "--topology-playground",
        nargs="?",
        const="2",
        metavar="DIM",
        help="launch Topology Playground directly for dimension 2, 3, or 4",
    )
    return parser.parse_known_args(argv)[0]


_PREPARSED_ARGS = None
if __name__ == "__main__":
    _PREPARSED_ARGS = _parse_cli_args(sys.argv[1:])


import pygame

from tet4d.engine.tutorial.api import tutorial_lesson_ids_runtime
from tet4d.ui.pygame.runtime_ui.app_runtime import (
    capture_windowed_display_settings,
    initialize_runtime,
    open_display,
)
from tet4d.ui.pygame.runtime_ui.audio import AudioSettings, play_sfx
from tet4d.ui.pygame.launch.bot_options_menu import run_bot_options_menu
from tet4d.ui.pygame.launch.topology_lab_menu import run_explorer_playground
from tet4d.ui.pygame.topology_lab.entrypoint import (
    parse_topology_playground_dimension,
    run_direct_topology_playground,
)
from tet4d.ui.pygame.topology_lab.app import (
    build_explorer_playground_config,
    build_explorer_playground_launch,
    mode_settings_snapshot_for_dimension,
)
from tet4d.ui.pygame.launch.leaderboard_menu import run_leaderboard_menu
from tet4d.ui.pygame.runtime_ui.app_runtime import DisplaySettings
from tet4d.ui.pygame.render.font_profiles import init_fonts as init_fonts_for_profile
from tet4d.ui.pygame.runtime_ui.help_menu import run_help_menu
from tet4d.ui.pygame.keybindings import (
    active_key_profile,
    cycle_key_profile,
    load_active_profile_bindings,
    set_active_key_profile,
)
from tet4d.ui.pygame.menu.keybindings_menu import run_keybindings_menu
from tet4d.ui.pygame.launch.launcher_play import launch_2d, launch_3d, launch_4d
from tet4d.ui.pygame.launch.launcher_settings import run_settings_hub_menu
from tet4d.engine.runtime.menu_config import (
    branding_copy,
    launcher_menu_id,
    launcher_route_actions,
    launcher_subtitles,
    menu_graph,
    ui_copy_section,
)
from tet4d.engine.runtime.menu_settings_state import (
    load_app_settings_payload as load_menu_payload,
)
from tet4d.engine.runtime.menu_settings_state import (
    save_app_settings_payload as save_menu_payload,
)
from tet4d.engine.runtime.topology_explorer_runtime import (
    load_runtime_explorer_topology_profile,
)
from tet4d.ui.pygame.menu.menu_runner import ActionRegistry, MenuRunner
from tet4d.ui.pygame.ui_utils import draw_vertical_gradient, fit_text


BG_TOP = (14, 18, 44)
BG_BOTTOM = (4, 7, 20)
TEXT_COLOR = (232, 232, 240)
HIGHLIGHT_COLOR = (255, 224, 128)
MUTED_COLOR = (192, 200, 228)

_MENU_GRAPH = menu_graph()
_LAUNCHER_ROOT_MENU_ID = launcher_menu_id()
_LAUNCHER_SUBTITLES = launcher_subtitles()
_LAUNCHER_ROUTE_ACTIONS = launcher_route_actions()
_BRANDING = branding_copy()
_GAME_TITLE = _BRANDING["game_title"]
_SIGNATURE_AUTHOR = _BRANDING["signature_author"]
_SIGNATURE_MESSAGE = _BRANDING["signature_message"]
_LAUNCHER_COPY = ui_copy_section("launcher")
_TUTORIAL_LESSON_BY_MODE = {
    "2d": "tutorial_2d_core",
    "3d": "tutorial_3d_core",
    "4d": "tutorial_4d_core",
}
_SETTINGS_HUB_ROUTE = {
    "settings": ("game_seed", "gameplay"),
    "settings_display": ("display_fullscreen", "display"),
    "settings_audio": ("audio_master", "audio"),
}
_HELP_TOPIC_BY_ACTION = {
    "tutorial_how_to_play": "overview",
    "tutorial_controls_reference": "key_reference",
}


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
        subtitle_key = "launcher_root"
    elif menu_id == _play_menu_id():
        subtitle_key = "launcher_play"
    else:
        subtitle_key = f"launcher_{menu_id.removeprefix('launcher_')}"
    subtitle = str(_LAUNCHER_SUBTITLES.get(subtitle_key, "")).strip()
    if subtitle:
        return subtitle
    return _LAUNCHER_SUBTITLES["default"]


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
    row_step = min(
        52, max(fonts.menu_font.get_height() + 8, (max_panel_h - 48) // row_count)
    )
    panel_h = min(max_panel_h, 48 + row_count * row_step)
    panel_x = (width - panel_w) // 2
    panel_y = max(
        top_reserved,
        min((height - panel_h) // 2, height - bottom_reserved - panel_h - 8),
    )

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
        label_text = fit_text(
            fonts.menu_font, label, row_right - (panel_x + row_margin)
        )
        text = fonts.menu_font.render(label_text, True, color)
        row_rect = text.get_rect(topleft=(panel_x + row_margin, y))
        if selected:
            hi = pygame.Surface((panel_w - 32, row_rect.height + 10), pygame.SRCALPHA)
            pygame.draw.rect(hi, (255, 255, 255, 38), hi.get_rect(), border_radius=9)
            screen.blit(hi, (panel_x + 16, y - 4))
        screen.blit(text, row_rect.topleft)
        y += row_step

    escape_hint = (
        _LAUNCHER_COPY["escape_hint_back"]
        if stack_depth > 1
        else _LAUNCHER_COPY["escape_hint_quit"]
    )
    info_lines = [
        _LAUNCHER_COPY["info_active_profile_template"].format(
            profile=active_key_profile()
        ),
        _LAUNCHER_COPY["info_continue_mode_template"].format(
            mode=state.last_mode.upper()
        ),
        _LAUNCHER_COPY[
            "controls_hint_template_tiny"
            if active_key_profile() == "tiny"
            else "controls_hint_template"
        ].format(escape_hint=escape_hint),
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
        screen.blit(
            status, ((width - status.get_width()) // 2, min(height - 34, info_y + 2))
        )
        info_y = min(height - 34, info_y + 2) + status.get_height() + 2

    signature_lines = (_SIGNATURE_AUTHOR, _SIGNATURE_MESSAGE)
    for signature_line in signature_lines:
        if info_y + hint_line_h > height - 6:
            break
        line_draw = fit_text(fonts.hint_font, signature_line, width - 24)
        text = fonts.hint_font.render(line_draw, True, MUTED_COLOR)
        screen.blit(text, ((width - text.get_width()) // 2, info_y))
        info_y += text.get_height() + 2


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
        "windowed_size": [
            int(display_settings.windowed_size[0]),
            int(display_settings.windowed_size[1]),
        ],
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
    *,
    tutorial_lesson_id: str | None = None,
) -> None:
    launchers = {
        "2d": lambda: launch_2d(
            session.screen,
            fonts_2d,
            session.display_settings,
            tutorial_lesson_id=tutorial_lesson_id,
        ),
        "3d": lambda: launch_3d(
            session.screen,
            fonts_nd,
            session.display_settings,
            tutorial_lesson_id=tutorial_lesson_id,
        ),
        "4d": lambda: launch_4d(
            session.screen,
            fonts_nd,
            session.display_settings,
            tutorial_lesson_id=tutorial_lesson_id,
        ),
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


def _menu_action_tutorial_dimension(
    mode: str,
    state: MainMenuState,
    session: _LauncherSession,
    fonts_nd,
    fonts_2d,
) -> bool:
    lesson_id = _TUTORIAL_LESSON_BY_MODE.get(mode)
    if not lesson_id:
        state.status = f"Unsupported tutorial mode: {mode}"
        state.status_error = True
        return False
    available_lessons = set(tutorial_lesson_ids_runtime())
    if lesson_id not in available_lessons:
        state.status = f"Lesson unavailable: {lesson_id}"
        state.status_error = True
        return False
    _launch_mode(
        mode,
        state,
        session,
        fonts_nd,
        fonts_2d,
        tutorial_lesson_id=lesson_id,
    )
    if session.running:
        state.status = f"Tutorial launched: {mode.upper()}"
        state.status_error = False
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
    *,
    initial_row_key: str | None = None,
    category_id: str | None = None,
) -> bool:
    result = run_settings_hub_menu(
        session.screen,
        fonts_nd,
        audio_settings=session.audio_settings,
        display_settings=session.display_settings,
        initial_row_key=initial_row_key,
        category_id=category_id,
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
    *,
    initial_topic_id: str | None = None,
) -> bool:
    dimension = int(state.last_mode[0]) if state.last_mode in {"2d", "3d", "4d"} else 2
    session.screen = run_help_menu(
        session.screen,
        fonts_nd,
        dimension=dimension,
        context_label="Launcher",
        initial_topic_id=initial_topic_id,
    )
    return False


def _menu_action_leaderboard(
    state: MainMenuState,
    session: _LauncherSession,
    fonts_nd,
) -> bool:
    _ = state
    session.screen = run_leaderboard_menu(session.screen, fonts_nd)
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
    start_dimension = (
        int(state.last_mode[0]) if state.last_mode in {"2d", "3d", "4d"} else 2
    )
    ok, msg = run_bot_options_menu(
        session.screen, fonts_nd, start_dimension=start_dimension
    )
    _persist_session_status(state, session)
    state.status = msg
    state.status_error = not ok
    return not session.running


def _menu_action_topology_lab(
    state: MainMenuState,
    session: _LauncherSession,
    fonts_nd,
    fonts_2d=None,
) -> bool:
    mode = state.last_mode if state.last_mode in {"2d", "3d", "4d"} else "2d"
    launch = build_explorer_playground_launch(
        dimension=int(mode[0]),
        explorer_profile=load_runtime_explorer_topology_profile(int(mode[0])),
        display_settings=session.display_settings,
        fonts_2d=fonts_2d,
        gameplay_mode="explorer",
        entry_source="launcher",
        source_settings=_mode_settings_snapshot(mode),
    )
    ok, msg = run_explorer_playground(session.screen, fonts_nd, launch=launch)
    _persist_session_status(state, session)
    state.status = msg
    state.status_error = not ok
    return not session.running

def _menu_action_legacy_topology_editor(
    state: MainMenuState,
    session: _LauncherSession,
    fonts_nd,
) -> bool:
    mode = state.last_mode if state.last_mode in {"2d", "3d", "4d"} else "2d"
    launch = build_explorer_playground_launch(
        dimension=int(mode[0]),
        gameplay_mode="normal",
        entry_source="launcher",
    )
    ok, msg = run_explorer_playground(session.screen, fonts_nd, launch=launch)
    _persist_session_status(state, session)
    state.status = msg
    state.status_error = not ok
    return not session.running

def _mode_settings_snapshot(mode: str) -> SimpleNamespace:
    return mode_settings_snapshot_for_dimension(int((mode if mode in {"2d", "3d", "4d"} else "2d")[0]))


def _menu_action_play_last_custom_topology(
    state: MainMenuState,
    session: _LauncherSession,
    fonts_nd,
    fonts_2d,
) -> bool:
    mode = state.last_mode if state.last_mode in {"2d", "3d", "4d"} else "2d"
    dimension = int(mode[0])
    launch = build_explorer_playground_launch(
        dimension=dimension,
        explorer_profile=load_runtime_explorer_topology_profile(dimension),
        display_settings=session.display_settings,
        fonts_2d=fonts_2d,
        gameplay_mode="explorer",
        entry_source="explorer",
        source_settings=_mode_settings_snapshot(mode),
    )
    from tet4d.ui.pygame import front2d_game, front3d_game, front4d_game

    try:
        cfg = build_explorer_playground_config(
            dimension=launch.dimension,
            explorer_profile=launch.explorer_profile,
            settings_snapshot=launch.settings_snapshot,
        )
        session.screen = open_display(
            session.display_settings,
            caption=f"{launch.dimension}D Explorer",
        )
        if launch.dimension == 2:
            back_to_menu = front2d_game.run_game_loop(
                session.screen,
                cfg,
                fonts_2d,
                session.display_settings,
            )
        elif launch.dimension == 3:
            back_to_menu = front3d_game.run_game_loop(session.screen, cfg, fonts_nd)
        else:
            back_to_menu = front4d_game.run_game_loop(session.screen, cfg, fonts_nd)
    except Exception as exc:
        state.status = f"Play last custom topology failed: {exc}"
        state.status_error = True
        return False

    if not back_to_menu:
        session.running = False
        return True

    state.last_mode = mode
    session.display_settings = capture_windowed_display_settings(
        session.display_settings
    )
    session.screen = open_display(session.display_settings)
    _persist_session_status(state, session)
    state.status = (
        launch.startup_notice
        or f"Returned from {launch.dimension}D custom topology play"
    )
    state.status_error = False
    return False


def _build_action_registry(
    state: MainMenuState,
    session: _LauncherSession,
    fonts_nd,
    fonts_2d,
) -> ActionRegistry:
    registry = ActionRegistry()
    register = registry.register
    register("play", lambda: _menu_action_continue(state, session, fonts_nd, fonts_2d))
    for action_id, mode in (
        ("play_2d", "2d"),
        ("play_3d", "3d"),
        ("play_4d", "4d"),
    ):
        register(
            action_id,
            lambda mode=mode: _menu_action_play_dimension(
                mode, state, session, fonts_nd, fonts_2d
            ),
        )
    register(
        "play_last_custom_topology",
        lambda: _menu_action_play_last_custom_topology(
            state,
            session,
            fonts_nd,
            fonts_2d,
        ),
    )
    register("continue", lambda: _menu_action_continue(state, session, fonts_nd, fonts_2d))
    register("help", lambda: _menu_action_help(state, session, fonts_nd))
    register("leaderboard", lambda: _menu_action_leaderboard(state, session, fonts_nd))
    for action_id, (initial_row_key, category_id) in _SETTINGS_HUB_ROUTE.items():
        register(
            action_id,
            lambda initial_row_key=initial_row_key, category_id=category_id: _menu_action_settings(
                state,
                session,
                fonts_nd,
                initial_row_key=initial_row_key,
                category_id=category_id,
            ),
        )
    for action_id in ("keybindings", "settings_profiles"):
        register(action_id, lambda: _menu_action_keybindings(state, session, fonts_nd))
    register("bot_options", lambda: _menu_action_bot_options(state, session, fonts_nd))
    register(
        "topology_lab",
        lambda: _menu_action_topology_lab(state, session, fonts_nd, fonts_2d),
    )
    register(
        "settings_legacy_topology_editor",
        lambda: _menu_action_legacy_topology_editor(state, session, fonts_nd),
    )
    for action_id, mode in (
        ("tutorial_2d", "2d"),
        ("tutorial_3d", "3d"),
        ("tutorial_4d", "4d"),
    ):
        register(
            action_id,
            lambda mode=mode: _menu_action_tutorial_dimension(
                mode, state, session, fonts_nd, fonts_2d
            ),
        )
    register(
        "tutorial_how_to_play",
        lambda: _menu_action_help(
            state,
            session,
            fonts_nd,
            initial_topic_id=_HELP_TOPIC_BY_ACTION["tutorial_how_to_play"],
        ),
    )
    register(
        "tutorial_controls_reference",
        lambda: _menu_action_help(
            state,
            session,
            fonts_nd,
            initial_topic_id=_HELP_TOPIC_BY_ACTION["tutorial_controls_reference"],
        ),
    )
    register("quit", lambda: _menu_action_quit(state, session))
    return registry


def _handle_launcher_route(
    route_id: str,
    state: MainMenuState,
    action_registry: ActionRegistry,
    session: _LauncherSession,
    fonts_nd,
    fonts_2d,
) -> bool:
    clean_route_id = route_id.strip().lower()
    action_id = _LAUNCHER_ROUTE_ACTIONS.get(clean_route_id)
    if not action_id:
        state.status = f"No action mapped for route '{clean_route_id}'"
        state.status_error = True
        return False
    try:
        return action_registry.dispatch(action_id)
    except KeyError:
        state.status = f"No handler registered for routed action '{action_id}'"
        state.status_error = True
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


def _is_profile_prev_key(key: int) -> bool:
    return key in (
        pygame.K_LEFTBRACKET,
        pygame.K_MINUS,
        pygame.K_PAGEUP,
    )


def _is_profile_next_key(key: int) -> bool:
    return key in (
        pygame.K_RIGHTBRACKET,
        pygame.K_EQUALS,
        pygame.K_PAGEDOWN,
    )


def _handle_launcher_keydown(
    menu_id: str,
    key: int,
    _stack_depth: int,
    state: MainMenuState,
    session: _LauncherSession,
) -> bool:
    if menu_id not in _MENU_GRAPH:
        return False
    if not (_is_profile_prev_key(key) or _is_profile_next_key(key)):
        return False

    step = -1 if _is_profile_prev_key(key) else 1
    ok, msg, profile = cycle_key_profile(step)
    if not ok:
        state.status = msg
        state.status_error = True
        return True

    _persist_session_status(state, session)
    state.status = f"Active key profile: {profile}"
    state.status_error = False
    play_sfx("menu_move")
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
            caption=_GAME_TITLE,
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
        pygame.display.set_caption(_GAME_TITLE)
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
        handle_route=lambda route_id: _handle_launcher_route(
            route_id,
            state,
            registry,
            session,
            fonts_nd,
            fonts_2d,
        ),
        handle_missing_action=lambda action_id: _handle_missing_action(
            action_id, state
        ),
        on_root_escape=lambda: _menu_action_quit(state, session),
        on_quit_event=lambda: _menu_action_quit(state, session),
        on_move=_play_move_sfx,
        on_confirm=_play_confirm_sfx,
        on_keydown=lambda menu_id, key, stack_depth: _handle_launcher_keydown(
            menu_id,
            key,
            stack_depth,
            state,
            session,
        ),
        initial_selected=initial_selected,
    )
    runner.run()

    pygame.quit()
    sys.exit()


def main(argv=None):
    parsed_args = _parse_cli_args(sys.argv[1:] if argv is None else argv)
    direct_dimension = parse_topology_playground_dimension(
        parsed_args.topology_playground
    )
    if direct_dimension is not None:
        run_direct_topology_playground(direct_dimension)
        return
    if argv is None:
        if _PREPARSED_ARGS is None:
            _parse_cli_args(sys.argv[1:])
    else:
        _parse_cli_args(argv)
    run()


if __name__ == "__main__":
    main()
