# ruff: noqa: E402
import argparse
import sys
from pathlib import Path
from dataclasses import dataclass


def _parse_cli_args(argv=None):
    parser = argparse.ArgumentParser(
        prog=Path(__file__).name,
        description="tet4d unified launcher",
    )
    parser.add_argument(
        "--runtime-smoke-check",
        action="store_true",
        help="initialize packaged runtime services and exit",
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
from tet4d.ui.pygame.runtime_ui.audio import AudioSettings
from tet4d.ui.pygame.launch.bot_options_menu import run_bot_options_menu
from tet4d.ui.pygame.launch.topology_lab_menu import run_explorer_playground
from tet4d.ui.pygame.locked_cell_explosion.launcher import (
    run_standalone_explosion_launcher_action,
)
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
from tet4d.ui.pygame.launch.launcher_profile_menu import (
    expand_settings_profile_rows,
    profile_action_id,
    SETTINGS_PROFILES_MENU_ID,
)
from tet4d.ui.pygame.launch.launcher_menu_view import draw_main_menu
from tet4d.ui.pygame.launch.launcher_runtime_helpers import (
    handle_launcher_profile_cycle_key,
    handle_launcher_route,
    handle_missing_action,
    play_confirm_sfx,
    play_move_sfx,
)
from tet4d.ui.pygame.runtime_ui.app_runtime import DisplaySettings
from tet4d.ui.pygame.render.font_profiles import init_fonts as init_fonts_for_profile
from tet4d.ui.pygame.runtime_ui.help_menu import run_help_menu
from tet4d.ui.pygame.keybindings import (
    active_key_profile,
    list_key_profiles,
    load_active_profile_bindings,
    set_active_key_profile,
)
from tet4d.ui.pygame.menu.keybindings_menu import run_keybindings_menu
from tet4d.ui.pygame.launch.launcher_play import launch_2d, launch_3d, launch_4d
from tet4d.ui.pygame.launch.launcher_settings import run_settings_hub_menu
from tet4d.engine.runtime.menu_config import (
    branding_copy,
    settings_menu_id,
    launcher_menu_id,
    launcher_route_actions,
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
from tet4d.ui.pygame.menu.menu_runner import MenuPointerTarget


BG_TOP = (14, 18, 44)
BG_BOTTOM = (4, 7, 20)
TEXT_COLOR = (232, 232, 240)
HIGHLIGHT_COLOR = (255, 224, 128)
MUTED_COLOR = (192, 200, 228)

_MENU_GRAPH = menu_graph()
_LAUNCHER_ROOT_MENU_ID = launcher_menu_id()
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
_HELP_TOPIC_BY_ACTION = {
    "tutorial_how_to_play": "overview",
    "tutorial_controls_reference": "key_reference",
}
_LAUNCHER_SETTINGS_PROFILES_MENU_ID = SETTINGS_PROFILES_MENU_ID


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

def _sync_launcher_settings_profile_rows() -> None:
    menu = _MENU_GRAPH.get(_LAUNCHER_SETTINGS_PROFILES_MENU_ID)
    if menu is None:
        return
    raw_items = menu.get("items")
    if not isinstance(raw_items, tuple):
        return
    menu["items"] = expand_settings_profile_rows(raw_items)


def _sync_launcher_profile_actions(
    registry: ActionRegistry,
    state: MainMenuState,
    session: _LauncherSession,
) -> None:
    for profile in list_key_profiles():
        registry.register(
            profile_action_id(profile),
            lambda profile=profile: _menu_action_activate_profile(
                profile,
                state,
                session,
                registry=registry,
            ),
        )


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


def _menu_index_for_root_mode_row(mode: str, fallback: int = 0) -> int:
    target_action_id = f"play_{mode}"
    for idx, item in enumerate(_menu_items(_LAUNCHER_ROOT_MENU_ID)):
        if str(item.get("type", "")).strip().lower() != "action_group":
            continue
        for action in item.get("actions", ()):
            action_id = str(action.get("action_id", "")).strip().lower()
            if action_id == target_action_id:
                return idx
    return fallback


def _menu_index_for_mode(mode: str) -> int:
    return _menu_index_for_root_mode_row(mode, fallback=0)


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
    use_persisted_settings: bool = False,
) -> None:
    launchers = {
        "2d": lambda: launch_2d(
            session.screen,
            fonts_2d,
            session.display_settings,
            tutorial_lesson_id=tutorial_lesson_id,
            use_persisted_settings=use_persisted_settings,
        ),
        "3d": lambda: launch_3d(
            session.screen,
            fonts_nd,
            session.display_settings,
            tutorial_lesson_id=tutorial_lesson_id,
            use_persisted_settings=use_persisted_settings,
        ),
        "4d": lambda: launch_4d(
            session.screen,
            fonts_nd,
            session.display_settings,
            tutorial_lesson_id=tutorial_lesson_id,
            use_persisted_settings=use_persisted_settings,
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
    _launch_mode(
        state.last_mode,
        state,
        session,
        fonts_nd,
        fonts_2d,
        use_persisted_settings=True,
    )
    return not session.running


def _menu_action_play_dimension(
    mode: str,
    state: MainMenuState,
    session: _LauncherSession,
    fonts_nd,
    fonts_2d,
) -> bool:
    _launch_mode(
        mode,
        state,
        session,
        fonts_nd,
        fonts_2d,
        use_persisted_settings=True,
    )
    return not session.running


def _menu_action_setup_dimension(
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
    *,
    registry: ActionRegistry | None = None,
) -> bool:
    dimension = int(state.last_mode[0]) if state.last_mode in {"2d", "3d", "4d"} else 2
    run_keybindings_menu(session.screen, fonts_nd, dimension=dimension, scope="general")
    load_active_profile_bindings()
    _sync_launcher_settings_profile_rows()
    if registry is not None:
        _sync_launcher_profile_actions(registry, state, session)
    _persist_session_status(state, session)
    return not session.running


def _menu_action_activate_profile(
    profile: str,
    state: MainMenuState,
    session: _LauncherSession,
    *,
    registry: ActionRegistry | None = None,
) -> bool:
    ok, msg = set_active_key_profile(profile)
    if ok:
        ok, msg = load_active_profile_bindings()
    _sync_launcher_settings_profile_rows()
    if registry is not None:
        _sync_launcher_profile_actions(registry, state, session)
    _persist_session_status(state, session)
    state.status = msg
    state.status_error = not ok
    return not session.running


def _menu_action_settings(
    state: MainMenuState,
    session: _LauncherSession,
    fonts_nd,
    *,
    initial_page_id: str | None = None,
    initial_item_id: str | None = None,
) -> bool:
    result = run_settings_hub_menu(
        session.screen,
        fonts_nd,
        audio_settings=session.audio_settings,
        display_settings=session.display_settings,
        initial_page_id=initial_page_id or settings_menu_id(),
        initial_item_id=initial_item_id,
    )
    session.screen = result.screen
    session.audio_settings = result.audio_settings
    session.display_settings = result.display_settings
    if not result.keep_running:
        session.running = False
        return True
    if result.dispatched_action_id == "settings_legacy_topology_editor":
        return _menu_action_legacy_topology_editor(state, session, fonts_nd)
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
        source_settings=mode_settings_snapshot_for_dimension(int(mode[0])),
    )
    ok, msg = run_explorer_playground(session.screen, fonts_nd, launch=launch)
    _persist_session_status(state, session)
    state.status = msg
    state.status_error = not ok
    return not session.running


def _menu_action_locked_cell_explosion(
    state: MainMenuState,
    session: _LauncherSession,
    fonts_nd,
) -> bool:
    return run_standalone_explosion_launcher_action(
        state,
        session,
        fonts_nd,
        persist_session_status=_persist_session_status,
    )


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
        source_settings=mode_settings_snapshot_for_dimension(int(mode[0])),
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
    for action_id, mode in (
        ("setup_2d", "2d"),
        ("setup_3d", "3d"),
        ("setup_4d", "4d"),
    ):
        register(
            action_id,
            lambda mode=mode: _menu_action_setup_dimension(
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
    register(
        "settings",
        lambda: _menu_action_settings(
            state,
            session,
            fonts_nd,
            initial_page_id=settings_menu_id(),
        ),
    )
    for action_id in ("keybindings",):
        register(
            action_id,
            lambda: _menu_action_keybindings(
                state,
                session,
                fonts_nd,
                registry=registry,
            ),
        )
    _sync_launcher_profile_actions(registry, state, session)
    register("bot_options", lambda: _menu_action_bot_options(state, session, fonts_nd))
    register(
        "topology_lab",
        lambda: _menu_action_topology_lab(state, session, fonts_nd, fonts_2d),
    )
    register(
        "locked_cell_explosion",
        lambda: _menu_action_locked_cell_explosion(state, session, fonts_nd),
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
    _session: _LauncherSession,
    fonts_nd=None,
    fonts_2d=None,
) -> bool:
    del fonts_nd, fonts_2d
    return handle_launcher_route(
        route_id,
        route_actions=_LAUNCHER_ROUTE_ACTIONS,
        state=state,
        action_registry=action_registry,
    )


def _handle_launcher_keydown(
    menu_id: str,
    key: int,
    _stack_depth: int,
    state: MainMenuState,
    session: _LauncherSession,
) -> bool:
    return handle_launcher_profile_cycle_key(
        menu_id,
        key,
        menu_ids=set(_MENU_GRAPH),
        state=state,
        session=session,
        sync_profile_rows=_sync_launcher_settings_profile_rows,
        persist_session_status=_persist_session_status,
    )


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
    _sync_launcher_settings_profile_rows()
    registry = _build_action_registry(state, session, fonts_nd, fonts_2d)

    initial_selected = {
        _LAUNCHER_ROOT_MENU_ID: _menu_index_for_mode(state.last_mode),
    }
    def _render_launcher_menu(
        menu_id: str,
        title: str,
        items: tuple[dict[str, object], ...],
        selected: int,
        depth: int,
        selected_action_indexes: dict[str, int],
        hovered_target: MenuPointerTarget | None,
        pressed_target: MenuPointerTarget | None,
    ) -> tuple[MenuPointerTarget, ...]:
        pygame.display.set_caption(_GAME_TITLE)
        targets = draw_main_menu(
            session.screen,
            fonts_nd,
            menu_title=title,
            items=items,
            selected_index=selected,
            selected_action_indexes=selected_action_indexes,
            stack_depth=depth,
            status=state.status,
            status_error=state.status_error,
            last_mode=state.last_mode,
            launcher_copy=_LAUNCHER_COPY,
            signature_author=_SIGNATURE_AUTHOR,
            signature_message=_SIGNATURE_MESSAGE,
            bg_top=BG_TOP,
            bg_bottom=BG_BOTTOM,
            text_color=TEXT_COLOR,
            highlight_color=HIGHLIGHT_COLOR,
            muted_color=MUTED_COLOR,
            hovered_target=hovered_target,
            pressed_target=pressed_target,
        )
        pygame.display.flip()
        return targets

    runner = MenuRunner(
        menus=_MENU_GRAPH,
        start_menu_id=_LAUNCHER_ROOT_MENU_ID,
        action_registry=registry,
        render_menu=_render_launcher_menu,
        handle_route=lambda route_id: handle_launcher_route(
            route_id,
            route_actions=_LAUNCHER_ROUTE_ACTIONS,
            state=state,
            action_registry=registry,
        ),
        handle_missing_action=lambda action_id: handle_missing_action(
            action_id, state=state
        ),
        on_root_escape=lambda: _menu_action_quit(state, session),
        on_quit_event=lambda: _menu_action_quit(state, session),
        on_move=play_move_sfx,
        on_confirm=play_confirm_sfx,
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


def _run_runtime_smoke_check() -> None:
    initialize_runtime(sync_audio_state=False)
    pygame.quit()
    print("runtime smoke check: OK")


def main(argv=None):
    parsed_args = _parse_cli_args(sys.argv[1:] if argv is None else argv)
    if parsed_args.runtime_smoke_check:
        _run_runtime_smoke_check()
        return
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
