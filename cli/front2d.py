# ruff: noqa: E402

import argparse
import sys
import random
from pathlib import Path
from dataclasses import dataclass, field
from typing import Callable, Optional


def _parse_cli_args(argv=None):
    parser = argparse.ArgumentParser(
        prog=Path(__file__).name,
        description="tet4d 2D launcher",
    )
    return parser.parse_known_args(argv)[0]


_PREPARSED_ARGS = None
if __name__ == "__main__":
    _PREPARSED_ARGS = _parse_cli_args(sys.argv[1:])

import pygame

from tet4d.ui.pygame.runtime_ui.app_runtime import (
    capture_windowed_display_settings_from_event,
    capture_windowed_display_settings,
    initialize_runtime,
    open_display,
)
from tet4d.ui.pygame.runtime_ui.audio import play_sfx
from tet4d.engine.api import Action, BoardND, GameConfig, GameState
from tet4d.engine.core.rng import RNG_MODE_FIXED_SEED, RNG_MODE_TRUE_RANDOM
from tet4d.engine.gameplay.challenge_mode import apply_challenge_prefill_2d
from tet4d.ui.pygame.runtime_ui.app_runtime import DisplaySettings
from tet4d.ui.pygame.runtime_ui.loop_runner_nd import process_game_events
from tet4d.ui.pygame.render.gfx_game import (
    CELL_SIZE,
    ClearEffect2D,
    GfxFonts,
    compute_game_layout,
    init_fonts,
    draw_menu,
    draw_game_frame,
    gravity_interval_ms_from_config,
)
from tet4d.ui.pygame.keybindings import (
    CAMERA_KEYS_3D,
    DISABLED_KEYS_2D,
    KEYS_2D,
    SYSTEM_KEYS,
    active_key_profile,
    load_active_profile_bindings,
)
from tet4d.ui.pygame.input.key_dispatch import (
    match_bound_action,
)
from tet4d.ui.pygame.menu.menu_controls import (
    FieldSpec,
    MenuAction,
    apply_menu_actions,
    gather_menu_actions,
)
from tet4d.engine.runtime.menu_config import (
    default_settings_payload,
    settings_option_labels,
    setup_fields_for_dimension,
    setup_hints_for_dimension,
)
from tet4d.engine.runtime.menu_settings_state import (
    load_menu_settings,
    save_menu_settings,
)
from tet4d.engine.runtime.project_config import (
    project_constant_float,
    project_constant_int,
)
from tet4d.engine.api import (
    PlayBotController,
    run_dry_run_2d,
    BotMode,
    bot_planner_algorithm_from_index,
    bot_mode_from_index,
    bot_planner_profile_from_index,
    clamp_lines_per_level_runtime,
    clamp_toggle_index_runtime,
    compute_speed_level_runtime,
    gameplay_default_mode_shared_settings_runtime,
    gameplay_kick_level_names_runtime,
    gameplay_mode_speedup_settings_runtime,
    get_display_settings_runtime,
    clamp_overlay_transparency_runtime,
    default_overlay_transparency_runtime,
    overlay_transparency_step_runtime,
    runtime_assist_combined_score_multiplier,
    tutorial_runtime_action_allowed_runtime,
    tutorial_runtime_create_session_runtime,
    tutorial_runtime_is_running_runtime,
    tutorial_runtime_observe_action_runtime,
    tutorial_runtime_consume_pending_setup_runtime,
    tutorial_runtime_allowed_actions_runtime,
    tutorial_runtime_required_action_runtime,
    tutorial_apply_step_setup_2d_runtime,
    tutorial_ensure_piece_visibility_2d_runtime,
    tutorial_runtime_restart_runtime,
    tutorial_runtime_redo_stage_runtime,
    tutorial_runtime_previous_stage_runtime,
    tutorial_runtime_next_stage_runtime,
    tutorial_runtime_skip_runtime,
    tutorial_runtime_sync_and_advance_runtime,
    tutorial_runtime_overlay_payload_runtime,
)
from tet4d.engine.gameplay.pieces2d import piece_set_2d_label, PIECE_SET_2D_OPTIONS
from tet4d.engine.gameplay.exploration_mode import minimal_exploration_dims_2d
from tet4d.engine.gameplay.rotation_anim import PieceRotationAnimator2D

combined_score_multiplier = runtime_assist_combined_score_multiplier
from tet4d.engine.gameplay.topology import topology_mode_from_index, topology_mode_label
from tet4d.engine.gameplay.topology_designer import (
    designer_profile_label_for_index,
    designer_profiles_for_dimension,
    export_resolved_topology_profile,
    resolve_topology_designer_selection,
)
from tet4d.engine.ui_logic.view_modes import GridMode, cycle_grid_mode
from tet4d.ui.pygame.launch.leaderboard_menu import maybe_record_leaderboard_session
from tet4d.ui.pygame.runtime_ui.pause_menu import run_pause_menu
from tet4d.ui.pygame.runtime_ui.help_menu import run_help_menu
from tet4d.ui.pygame.runtime_ui.tutorial_overlay import draw_tutorial_overlay

RANDOM_MODE_FIXED_INDEX = 0
RANDOM_MODE_TRUE_RANDOM_INDEX = 1
_RANDOM_MODE_CHOICES = (
    RNG_MODE_FIXED_SEED,
    RNG_MODE_TRUE_RANDOM,
)
_RANDOM_MODE_LABELS = tuple(settings_option_labels()["game_random_mode"])
_DEFAULT_MODE_2D = default_settings_payload()["settings"]["2d"]
_MODE_GAMEPLAY_DEFAULTS = gameplay_default_mode_shared_settings_runtime("2d")
_KICK_LEVEL_NAMES = gameplay_kick_level_names_runtime()
_AUTO_SPEEDUP_ENABLED_DEFAULT = int(_MODE_GAMEPLAY_DEFAULTS["auto_speedup_enabled"])
_LINES_PER_LEVEL_DEFAULT = int(_MODE_GAMEPLAY_DEFAULTS["lines_per_level"])
_KICK_LEVEL_INDEX_DEFAULT = int(_MODE_GAMEPLAY_DEFAULTS["kick_level_index"])
_TUTORIAL_MOVE_DELAY_MS = project_constant_int(
    ("tutorial", "action_delay_ms", "movement"),
    170,
    min_value=0,
    max_value=2000,
)
_TUTORIAL_ROTATE_DELAY_MS = project_constant_int(
    ("tutorial", "action_delay_ms", "rotation"),
    190,
    min_value=0,
    max_value=2000,
)
_TUTORIAL_DROP_DELAY_MS = project_constant_int(
    ("tutorial", "action_delay_ms", "drop"),
    260,
    min_value=0,
    max_value=2000,
)
_TUTORIAL_SOFT_DROP_DELAY_MS = project_constant_int(
    ("tutorial", "action_delay_ms", "soft_drop"),
    min(200, int(_TUTORIAL_DROP_DELAY_MS)),
    min_value=0,
    max_value=2000,
)
_TUTORIAL_HARD_DROP_DELAY_MS = project_constant_int(
    ("tutorial", "action_delay_ms", "hard_drop"),
    int(_TUTORIAL_DROP_DELAY_MS),
    min_value=0,
    max_value=2000,
)
_TUTORIAL_DELAYED_ACTIONS_2D = {
    "move_x_neg",
    "move_x_pos",
    "move_y_neg",
    "move_y_pos",
    "rotate_xy_pos",
    "rotate_xy_neg",
    "soft_drop",
    "hard_drop",
}
_TUTORIAL_ALWAYS_LEGAL_ACTIONS_2D = {"menu", "help", "restart", "menu_back"}
_TUTORIAL_MOVE_DELTAS_2D = {
    "move_x_neg": (-1, 0),
    "move_x_pos": (1, 0),
    "move_y_neg": (0, -1),
    "move_y_pos": (0, 1),
}
_TUTORIAL_ROTATIONS_2D = {
    "rotate_xy_pos": 1,
    "rotate_xy_neg": -1,
}
_TUTORIAL_GRID_OFF_STEPS_2D = frozenset({"toggle_grid"})
_TUTORIAL_GRID_HELPER_STEPS_2D = frozenset({"line_fill", "full_clear_bonus"})
_TUTORIAL_GAMEPLAY_ACTIONS_2D = (
    "soft_drop",
    "hard_drop",
    "move_x_neg",
    "move_x_pos",
    "move_y_neg",
    "move_y_pos",
    "rotate_xy_pos",
    "rotate_xy_neg",
)
_TUTORIAL_MIN_VISIBLE_LAYER = project_constant_int(
    ("tutorial", "min_visible_layer"),
    2,
    min_value=0,
    max_value=10,
)
_TUTORIAL_MIN_WIDTH_2D = project_constant_int(
    ("tutorial", "min_board_dims", "2d", "width"),
    10,
    min_value=4,
    max_value=40,
)
_TUTORIAL_MIN_HEIGHT_2D = project_constant_int(
    ("tutorial", "min_board_dims", "2d", "height"),
    20,
    min_value=8,
    max_value=80,
)
_TUTORIAL_TARGET_FILL_RGBA = (255, 214, 80, 72)
_TUTORIAL_TARGET_BORDER_RGBA = (255, 242, 168, 220)


# ---------- Menu state & actions (logic, not drawing) ----------


@dataclass
class GameSettings:
    width: int = _DEFAULT_MODE_2D["width"]
    height: int = _DEFAULT_MODE_2D["height"]
    random_mode_index: int = _DEFAULT_MODE_2D["random_mode_index"]
    game_seed: int = _DEFAULT_MODE_2D["game_seed"]
    piece_set_index: int = _DEFAULT_MODE_2D["piece_set_index"]
    topology_mode: int = _DEFAULT_MODE_2D["topology_mode"]
    topology_advanced: int = _DEFAULT_MODE_2D["topology_advanced"]
    topology_profile_index: int = _DEFAULT_MODE_2D["topology_profile_index"]
    kick_level_index: int = _DEFAULT_MODE_2D["kick_level_index"]
    bot_mode_index: int = _DEFAULT_MODE_2D["bot_mode_index"]
    bot_algorithm_index: int = _DEFAULT_MODE_2D["bot_algorithm_index"]
    bot_profile_index: int = _DEFAULT_MODE_2D["bot_profile_index"]
    bot_speed_level: int = _DEFAULT_MODE_2D["bot_speed_level"]
    bot_budget_ms: int = _DEFAULT_MODE_2D["bot_budget_ms"]
    challenge_layers: int = _DEFAULT_MODE_2D["challenge_layers"]
    exploration_mode: int = _DEFAULT_MODE_2D["exploration_mode"]
    speed_level: int = _DEFAULT_MODE_2D[
        "speed_level"
    ]  # 1..10, mapped to gravity interval


@dataclass
class MenuState:
    settings: GameSettings = field(default_factory=GameSettings)
    selected_index: int = 0  # 0=width, 1=height, 2=speed
    running: bool = True
    start_game: bool = False
    bindings_status: str = ""
    bindings_status_error: bool = False
    active_profile: str = field(default_factory=active_key_profile)
    rebind_mode: bool = False
    rebind_index: int = 0
    rebind_targets: list[tuple[str, str]] = field(default_factory=list)
    rebind_conflict_mode: str = "replace"
    run_dry_run: bool = False


_TOPOLOGY_PROFILE_LABELS_2D = tuple(
    profile.label for profile in designer_profiles_for_dimension(2)
)


def _menu_fields(settings: GameSettings) -> list[FieldSpec]:
    fields = setup_fields_for_dimension(
        2,
        piece_set_max=len(PIECE_SET_2D_OPTIONS) - 1,
        topology_profile_max=max(0, len(_TOPOLOGY_PROFILE_LABELS_2D) - 1),
    )
    if int(settings.topology_advanced):
        return fields
    return [field for field in fields if field[1] != "topology_profile_index"]


_SETUP_BLOCKED_ACTIONS = {
    MenuAction.LOAD_BINDINGS,
    MenuAction.SAVE_BINDINGS,
    MenuAction.LOAD_SETTINGS,
    MenuAction.SAVE_SETTINGS,
    MenuAction.RESET_SETTINGS,
    MenuAction.PROFILE_PREV,
    MenuAction.PROFILE_NEXT,
    MenuAction.PROFILE_NEW,
    MenuAction.PROFILE_DELETE,
    MenuAction.REBIND_TOGGLE,
    MenuAction.REBIND_TARGET_NEXT,
    MenuAction.REBIND_TARGET_PREV,
    MenuAction.REBIND_CONFLICT_NEXT,
    MenuAction.RESET_BINDINGS,
}


def _piece_set_index_to_id(index: int) -> str:
    safe_index = max(0, min(len(PIECE_SET_2D_OPTIONS) - 1, int(index)))
    return PIECE_SET_2D_OPTIONS[safe_index]


def _random_mode_index_to_id(index: int) -> str:
    safe_index = max(0, min(len(_RANDOM_MODE_CHOICES) - 1, int(index)))
    return _RANDOM_MODE_CHOICES[safe_index]


def _random_mode_label(index: int) -> str:
    safe_index = max(0, min(len(_RANDOM_MODE_LABELS) - 1, int(index)))
    return _RANDOM_MODE_LABELS[safe_index]


def _load_speedup_settings_for_mode(mode_key: str) -> tuple[int, int]:
    return gameplay_mode_speedup_settings_runtime(mode_key)


def _kick_level_name(index: int) -> str:
    safe_index = max(0, min(len(_KICK_LEVEL_NAMES) - 1, int(index)))
    return _KICK_LEVEL_NAMES[safe_index]


def _load_overlay_transparency_for_runtime_2d() -> float:
    display_payload = get_display_settings_runtime()
    overlay_transparency = default_overlay_transparency_runtime()
    if not isinstance(display_payload, dict):
        return overlay_transparency
    return clamp_overlay_transparency_runtime(
        display_payload.get("overlay_transparency"),
        default=overlay_transparency,
    )


def _menu_value_formatter(attr_name: str, value: object) -> str:
    if attr_name == "piece_set_index":
        return piece_set_2d_label(_piece_set_index_to_id(int(value)))
    if attr_name == "random_mode_index":
        return _random_mode_label(int(value))
    if attr_name == "game_seed":
        return str(max(0, int(value)))
    if attr_name == "topology_mode":
        return topology_mode_label(topology_mode_from_index(int(value)))
    if attr_name == "topology_advanced":
        return "ON" if int(value) else "OFF"
    if attr_name == "topology_profile_index":
        return designer_profile_label_for_index(2, int(value))
    if attr_name == "challenge_layers":
        return str(value)
    if attr_name == "exploration_mode":
        return "ON" if int(value) else "OFF"
    if attr_name == "speed_level":
        return f"{value}   (1 = slow, 10 = fast)"
    return str(value)


def _config_from_settings(settings: GameSettings) -> GameConfig:
    piece_set_id = _piece_set_index_to_id(settings.piece_set_index)
    topology_mode = topology_mode_from_index(settings.topology_mode)
    resolved_mode, topology_edge_rules, _profile = resolve_topology_designer_selection(
        dimension=2,
        gravity_axis=1,
        topology_mode=topology_mode,
        topology_advanced=bool(settings.topology_advanced),
        profile_index=settings.topology_profile_index,
    )
    exploration_enabled = bool(settings.exploration_mode)
    width = settings.width
    height = settings.height
    if exploration_enabled:
        width, height = minimal_exploration_dims_2d(
            piece_set_id,
            random_cell_count=4,
        )
    return GameConfig(
        width=width,
        height=height,
        gravity_axis=1,
        speed_level=settings.speed_level,
        topology_mode=resolved_mode,
        topology_edge_rules=topology_edge_rules,
        piece_set=piece_set_id,
        kick_level=_kick_level_name(settings.kick_level_index),
        rng_mode=_random_mode_index_to_id(settings.random_mode_index),
        rng_seed=max(0, int(settings.game_seed)),
        challenge_layers=0 if exploration_enabled else settings.challenge_layers,
        exploration_mode=exploration_enabled,
    )


# ---------- Menu loop ----------


def run_menu(screen: pygame.Surface, fonts: GfxFonts) -> Optional[GameSettings]:
    """
    Intro screen where width, height, and speed_level can be set.
    Returns GameSettings if user starts the game, or None if user quits.
    """
    clock = pygame.time.Clock()
    load_active_profile_bindings()
    state = MenuState()
    ok, msg = load_menu_settings(state, 2, include_profile=True)
    if not ok:
        state.bindings_status = msg
        state.bindings_status_error = True

    while state.running and not state.start_game:
        _dt = clock.tick(60)
        actions = gather_menu_actions(state, 2)
        fields = _menu_fields(state.settings)
        if state.selected_index >= len(fields):
            state.selected_index = max(0, len(fields) - 1)
        apply_menu_actions(
            state,
            actions,
            fields,
            2,
            blocked_actions=_SETUP_BLOCKED_ACTIONS,
        )
        if state.run_dry_run:
            if bool(state.settings.exploration_mode):
                state.bindings_status = "Dry-run is disabled in exploration mode"
                state.bindings_status_error = False
            else:
                report = run_dry_run_2d(
                    _config_from_settings(state.settings),
                    planner_profile=bot_planner_profile_from_index(
                        state.settings.bot_profile_index
                    ),
                    planning_budget_ms=state.settings.bot_budget_ms,
                    planner_algorithm=bot_planner_algorithm_from_index(
                        state.settings.bot_algorithm_index
                    ),
                )
                state.bindings_status = report.reason
                state.bindings_status_error = not report.passed

        draw_menu(
            screen,
            fonts,
            state.settings,
            state.selected_index,
            bindings_file_hint=None,
            extra_hint_lines=tuple(setup_hints_for_dimension(2)) or (
                "F7 dry-run verify (bot, no graphics)",
                "Use Main Menu -> Settings for Random type and Advanced topology.",
                "Use Main Menu -> Bot Options / Keybindings for shared controls.",
            ),
            bindings_status=state.bindings_status,
            bindings_status_error=state.bindings_status_error,
            menu_fields=fields,
            value_formatter=_menu_value_formatter,
        )
        pygame.display.flip()

    if state.start_game and state.running:
        ok, msg = save_menu_settings(state, 2)
        if not ok:
            state.bindings_status = msg
            state.bindings_status_error = True
        else:
            topology_mode = topology_mode_from_index(state.settings.topology_mode)
            export_resolved_topology_profile(
                dimension=2,
                gravity_axis=1,
                topology_mode=topology_mode,
                topology_advanced=bool(state.settings.topology_advanced),
                profile_index=state.settings.topology_profile_index,
            )
        return state.settings
    # Autosave setup/session state on exit as well (without explicit Save action).
    save_menu_settings(state, 2)
    return None


# ---------- Game helpers ----------


def create_initial_state(cfg: GameConfig) -> GameState:
    board = BoardND((cfg.width, cfg.height))
    if cfg.rng_mode == RNG_MODE_TRUE_RANDOM:
        rng = random.Random()
    else:
        rng = random.Random(cfg.rng_seed)
    state = GameState(config=cfg, board=board, rng=rng)
    if not cfg.exploration_mode:
        apply_challenge_prefill_2d(state, layers=cfg.challenge_layers)
    return state


def _system_decision_for_key(key: int) -> str | None:
    system_action = match_bound_action(
        key,
        SYSTEM_KEYS,
        ("quit", "menu", "restart", "toggle_grid", "help"),
    )
    if system_action is None:
        return None
    if system_action == "quit" and int(key) == int(pygame.K_ESCAPE):
        play_sfx("menu_confirm")
        return "menu"
    if system_action == "quit":
        return "quit"
    if system_action == "menu":
        play_sfx("menu_confirm")
        return "menu"
    if system_action == "restart":
        play_sfx("menu_confirm")
        return "restart"
    if system_action == "help":
        play_sfx("menu_move")
        return "help"
    play_sfx("menu_move")
    return "toggle_grid"


def _dispatch_2d_gameplay_action(state: GameState, key: int) -> str | None:
    action = _gameplay_action_for_key_2d(state, key)
    if action is None:
        return None
    _apply_2d_gameplay_action(state, action)
    if action.startswith("rotate_"):
        play_sfx("rotate")
    elif action == "hard_drop":
        play_sfx("drop")
    else:
        play_sfx("move")
    return action


def _gameplay_action_for_key_2d(state: GameState, key: int) -> str | None:
    action_order = [
        "move_x_neg",
        "move_x_pos",
        "rotate_xy_pos",
        "rotate_xy_neg",
        "hard_drop",
        "soft_drop",
    ]
    if state.config.exploration_mode:
        action_order.extend(["move_y_neg", "move_y_pos"])
    return match_bound_action(key, KEYS_2D, tuple(action_order))


def _overlay_action_for_key_2d(key: int) -> str | None:
    return match_bound_action(
        key,
        CAMERA_KEYS_3D,
        ("overlay_alpha_dec", "overlay_alpha_inc"),
    )


def _apply_2d_gameplay_action(state: GameState, action: str) -> None:
    handlers = {
        "move_x_neg": lambda: state.try_move(-1, 0),
        "move_x_pos": lambda: state.try_move(1, 0),
        "rotate_xy_pos": lambda: state.try_rotate(+1),
        "rotate_xy_neg": lambda: state.try_rotate(-1),
        "hard_drop": state.hard_drop,
        "soft_drop": lambda: state.try_move(0, 1),
        "move_y_neg": lambda: state.try_move(0, -1),
        "move_y_pos": lambda: state.try_move(0, 1),
    }
    handler = handlers.get(action)
    if handler is not None:
        handler()


def handle_game_keydown(
    event: pygame.event.Event,
    state: GameState,
    _cfg: GameConfig,
    *,
    allow_gameplay: bool = True,
    action_filter: Callable[[str], bool] | None = None,
    action_observer: Callable[[str], None] | None = None,
) -> Optional[str]:
    """
    Handle a single KEYDOWN event during the game.
    Returns:
        "quit"        -> user wants to quit the program
        "menu"        -> user wants to go back to the menu
        "restart"     -> restart game with current config
        "toggle_grid" -> toggle board grid visibility
        "help"        -> open in-game help menu
        "continue"    -> keep running
    """
    key = event.key

    system_decision = _system_decision_for_key(key)
    if system_decision is not None:
        if action_filter is not None and not action_filter(system_decision):
            return "continue"
        if action_observer is not None:
            action_observer(system_decision)
        return system_decision

    if not allow_gameplay:
        return "continue"

    if state.game_over:
        # Don't react to movement keys when game over
        return "continue"

    # Explicitly disable ND-only controls in 2D mode.
    if key in DISABLED_KEYS_2D:
        return "continue"

    gameplay_action = _gameplay_action_for_key_2d(state, key)
    if gameplay_action is None:
        return "continue"
    if action_filter is not None and not action_filter(gameplay_action):
        return "continue"
    _dispatch_2d_gameplay_action(state, key)
    if action_observer is not None:
        action_observer(gameplay_action)
    return "continue"


def _step_gravity_tick(
    state: GameState, gravity_accumulator: int, gravity_interval_ms: int
) -> int:
    if not state.game_over and gravity_accumulator >= gravity_interval_ms:
        state.step(Action.NONE)
        return 0
    return gravity_accumulator


def _tutorial_action_delay_ms_2d(action_id: str) -> int:
    if action_id == "soft_drop":
        return int(_TUTORIAL_SOFT_DROP_DELAY_MS)
    if action_id == "hard_drop":
        return int(_TUTORIAL_HARD_DROP_DELAY_MS)
    if action_id.startswith("rotate_"):
        return int(_TUTORIAL_ROTATE_DELAY_MS)
    if action_id.startswith("move_"):
        return int(_TUTORIAL_MOVE_DELAY_MS)
    return 0


def _tutorial_required_action_legal_2d(loop: "LoopContext2D", action_id: str) -> bool:
    if action_id in _TUTORIAL_ALWAYS_LEGAL_ACTIONS_2D:
        return True
    return _tutorial_can_apply_piece_action_2d(loop, action_id)


def _tutorial_can_apply_piece_action_2d(loop: "LoopContext2D", action_id: str) -> bool:
    piece = loop.state.current_piece
    if piece is None or loop.state.game_over:
        return False
    if action_id == "hard_drop":
        return True
    if action_id == "soft_drop":
        return bool(loop.state._can_exist(piece.moved(0, 1)))
    move_delta = _TUTORIAL_MOVE_DELTAS_2D.get(action_id)
    if move_delta is not None:
        return bool(loop.state._can_exist(piece.moved(*move_delta)))
    rotation = _TUTORIAL_ROTATIONS_2D.get(action_id)
    if rotation is not None:
        return bool(loop.state._can_exist(piece.rotated(rotation)))
    return True


def _tutorial_has_legal_action_2d(
    loop: "LoopContext2D",
    action_ids: tuple[str, ...] | list[str],
) -> bool:
    for action_id in action_ids:
        if _tutorial_required_action_legal_2d(loop, action_id):
            return True
    return False


def _tutorial_running_session_2d(loop: "LoopContext2D") -> object | None:
    tutorial_session = loop.tutorial_session
    if tutorial_session is None:
        return None
    if not tutorial_runtime_is_running_runtime(tutorial_session):
        return None
    return tutorial_session


def _redo_tutorial_stage_2d(loop: "LoopContext2D", tutorial_session: object) -> None:
    if tutorial_runtime_redo_stage_runtime(tutorial_session):
        _apply_pending_tutorial_setup(loop)


def _restart_tutorial_session_2d(
    loop: "LoopContext2D",
    tutorial_session: object,
) -> None:
    if tutorial_runtime_restart_runtime(tutorial_session):
        _apply_pending_tutorial_setup(loop)


def _tutorial_required_action_blocked_2d(
    loop: "LoopContext2D",
    tutorial_session: object,
) -> bool:
    required_action = tutorial_runtime_required_action_runtime(tutorial_session)
    if not required_action:
        return False
    return not _tutorial_required_action_legal_2d(loop, required_action)


def _tutorial_allowed_actions_blocked_2d(
    loop: "LoopContext2D",
    tutorial_session: object,
) -> bool:
    allowed_actions = tutorial_runtime_allowed_actions_runtime(tutorial_session)
    if not allowed_actions:
        return False
    return not _tutorial_has_legal_action_2d(loop, allowed_actions)


def _enforce_tutorial_runtime_safety_2d(loop: "LoopContext2D") -> None:
    tutorial_session = _tutorial_running_session_2d(loop)
    if tutorial_session is None:
        return

    if loop.state.game_over:
        _redo_tutorial_stage_2d(loop, tutorial_session)
        return

    visible = tutorial_ensure_piece_visibility_2d_runtime(
        loop.state,
        loop.cfg,
        min_visible_layer=int(_TUTORIAL_MIN_VISIBLE_LAYER),
    )
    if not visible:
        _redo_tutorial_stage_2d(loop, tutorial_session)
        return

    if _tutorial_allowed_actions_blocked_2d(loop, tutorial_session):
        _redo_tutorial_stage_2d(loop, tutorial_session)
        return

    if _tutorial_required_action_blocked_2d(loop, tutorial_session):
        _redo_tutorial_stage_2d(loop, tutorial_session)
        return



def _update_clear_animation(
    state: GameState,
    last_lines_cleared: int,
    clear_anim_levels: tuple[int, ...],
    clear_anim_elapsed_ms: float,
    clear_anim_duration_ms: float,
    dt_ms: int,
) -> tuple[tuple[int, ...], float, int]:
    if state.lines_cleared != last_lines_cleared:
        clear_anim_levels = tuple(state.board.last_cleared_levels)
        clear_anim_elapsed_ms = 0.0
        last_lines_cleared = state.lines_cleared
    if clear_anim_levels:
        clear_anim_elapsed_ms += dt_ms
        if clear_anim_elapsed_ms >= clear_anim_duration_ms:
            return (), 0.0, last_lines_cleared
    return clear_anim_levels, clear_anim_elapsed_ms, last_lines_cleared


def _clear_effect(
    levels: tuple[int, ...], elapsed_ms: float, duration_ms: float
) -> Optional[ClearEffect2D]:
    if not levels:
        return None
    return ClearEffect2D(
        levels=levels,
        progress=min(1.0, elapsed_ms / duration_ms),
    )


@dataclass
class LoopContext2D:
    cfg: GameConfig
    state: GameState
    bot: PlayBotController = field(default_factory=PlayBotController)
    rotation_anim: PieceRotationAnimator2D = field(
        default_factory=PieceRotationAnimator2D
    )
    gravity_accumulator: int = 0
    grid_mode: GridMode = GridMode.FULL
    clear_anim_levels: tuple[int, ...] = ()
    clear_anim_elapsed_ms: float = 0.0
    last_lines_cleared: int = 0
    was_game_over: bool = False
    base_speed_level: int = 1
    bot_speed_level: int = 7
    auto_speedup_enabled: int = _AUTO_SPEEDUP_ENABLED_DEFAULT
    lines_per_level: int = _LINES_PER_LEVEL_DEFAULT
    overlay_transparency: float = field(default_factory=default_overlay_transparency_runtime)
    tutorial_session: object | None = None
    tutorial_action_cooldown_ms: int = 0

    @classmethod
    def create(
        cls,
        cfg: GameConfig,
        *,
        bot_mode: BotMode = BotMode.OFF,
        bot_speed_level: int = 7,
        auto_speedup_enabled: int = _AUTO_SPEEDUP_ENABLED_DEFAULT,
        lines_per_level: int = _LINES_PER_LEVEL_DEFAULT,
        overlay_transparency: float | None = None,
        tutorial_lesson_id: str | None = None,
    ) -> "LoopContext2D":
        state = create_initial_state(cfg)
        tutorial_session = None
        if tutorial_lesson_id:
            tutorial_session = tutorial_runtime_create_session_runtime(
                lesson_id=tutorial_lesson_id,
                mode="2d",
            )
        return cls(
            cfg=cfg,
            state=state,
            bot=PlayBotController(mode=bot_mode),
            last_lines_cleared=state.lines_cleared,
            was_game_over=state.game_over,
            base_speed_level=int(cfg.speed_level),
            bot_speed_level=int(bot_speed_level),
            auto_speedup_enabled=clamp_toggle_index_runtime(
                auto_speedup_enabled,
                default=_AUTO_SPEEDUP_ENABLED_DEFAULT,
            ),
            lines_per_level=clamp_lines_per_level_runtime(
                lines_per_level,
                default=_LINES_PER_LEVEL_DEFAULT,
            ),
            overlay_transparency=clamp_overlay_transparency_runtime(
                overlay_transparency,
                default=default_overlay_transparency_runtime(),
            ),
            tutorial_session=tutorial_session,
        )

    def keydown_handler(self, event: pygame.event.Event) -> str:
        tutorial_action = self._handle_tutorial_hotkey(event.key)
        if tutorial_action is not None:
            return tutorial_action
        if self._handle_overlay_hotkey(event.key):
            return "continue"
        if event.key == pygame.K_F2:
            if not self._tutorial_action_allowed("bot_cycle_mode"):
                return "continue"
            self.bot.cycle_mode()
            self.refresh_score_multiplier()
            self._tutorial_observe_action("bot_cycle_mode")
            play_sfx("menu_move")
            return "continue"
        if event.key == pygame.K_F3:
            if not self._tutorial_action_allowed("bot_step"):
                return "continue"
            self.bot.request_step()
            self._tutorial_observe_action("bot_step")
            play_sfx("menu_move")
            return "continue"
        return handle_game_keydown(
            event,
            self.state,
            self.cfg,
            allow_gameplay=self.bot.user_gameplay_enabled,
            action_filter=self._tutorial_action_allowed,
            action_observer=self._tutorial_observe_action,
        )

    def _handle_tutorial_hotkey(self, key: int) -> str | None:
        session = self.tutorial_session
        if session is None:
            return None
        stage_nav = {
            pygame.K_F5: tutorial_runtime_previous_stage_runtime,
            pygame.K_F6: tutorial_runtime_next_stage_runtime,
            pygame.K_F7: tutorial_runtime_redo_stage_runtime,
        }
        step_action = stage_nav.get(key)
        if step_action is not None:
            if step_action(session):
                _apply_pending_tutorial_setup(self)
                self.tutorial_action_cooldown_ms = 0
                play_sfx("menu_confirm" if key == pygame.K_F7 else "menu_move")
            return "continue"
        if key == pygame.K_F8:
            tutorial_runtime_skip_runtime(session)
            play_sfx("menu_move")
            return "menu"
        if key == pygame.K_F9:
            if tutorial_runtime_restart_runtime(session):
                _apply_pending_tutorial_setup(self)
                self.tutorial_action_cooldown_ms = 0
            else:
                self.on_restart()
            play_sfx("menu_confirm")
            return "continue"
        return None

    def _handle_overlay_hotkey(self, key: int) -> bool:
        action = _overlay_action_for_key_2d(key)
        if action is None:
            return False
        if not self._tutorial_action_allowed(action):
            return True
        direction = -1 if action == "overlay_alpha_dec" else 1
        self.adjust_overlay_transparency(direction)
        self._tutorial_observe_action(action)
        play_sfx("menu_move")
        return True

    def _tutorial_action_allowed(self, action_id: str) -> bool:
        if self.tutorial_session is None:
            return True
        if (
            int(self.tutorial_action_cooldown_ms) > 0
            and action_id in _TUTORIAL_DELAYED_ACTIONS_2D
        ):
            return False
        return tutorial_runtime_action_allowed_runtime(self.tutorial_session, action_id)

    def _tutorial_observe_action(self, action_id: str) -> None:
        if self.tutorial_session is None:
            return
        tutorial_runtime_observe_action_runtime(self.tutorial_session, action_id)
        self.tutorial_action_cooldown_ms = _tutorial_action_delay_ms_2d(action_id)

    def adjust_overlay_transparency(self, direction: int) -> None:
        self.overlay_transparency = clamp_overlay_transparency_runtime(
            self.overlay_transparency + (overlay_transparency_step_runtime() * direction),
            default=default_overlay_transparency_runtime(),
        )

    def on_restart(self) -> None:
        self.cfg.speed_level = int(self.base_speed_level)
        self.state = create_initial_state(self.cfg)
        self.gravity_accumulator = 0
        self.clear_anim_levels = ()
        self.clear_anim_elapsed_ms = 0.0
        self.last_lines_cleared = self.state.lines_cleared
        self.was_game_over = self.state.game_over
        self.bot.reset_runtime()
        self.rotation_anim.reset()
        self.tutorial_action_cooldown_ms = 0
        self.refresh_score_multiplier()

    def on_toggle_grid(self) -> None:
        self.grid_mode = cycle_grid_mode(self.grid_mode)
        self.refresh_score_multiplier()

    def refresh_score_multiplier(self) -> None:
        self.state.score_multiplier = combined_score_multiplier(
            bot_mode=self.bot.mode,
            grid_mode=self.grid_mode,
            speed_level=self.cfg.speed_level,
            kick_level=self.cfg.kick_level,
        )
        mode_name = self.bot.mode.value
        self.state.analysis_actor_mode = (
            "human" if self.bot.mode == BotMode.OFF else mode_name
        )
        self.state.analysis_bot_mode = mode_name
        self.state.analysis_grid_mode = self.grid_mode.value


def _maybe_apply_auto_speedup(loop: LoopContext2D) -> int | None:
    target_speed_level = compute_speed_level_runtime(
        start_level=int(loop.base_speed_level),
        lines_cleared=int(loop.state.lines_cleared),
        enabled=bool(loop.auto_speedup_enabled),
        lines_per_level=int(loop.lines_per_level),
    )
    if int(target_speed_level) == int(loop.cfg.speed_level):
        return None
    loop.cfg.speed_level = int(target_speed_level)
    gravity_interval_ms = gravity_interval_ms_from_config(loop.cfg)
    loop.bot.configure_speed(gravity_interval_ms, int(loop.bot_speed_level))
    loop.gravity_accumulator = 0
    loop.refresh_score_multiplier()
    return gravity_interval_ms


def _apply_pending_tutorial_setup(loop: LoopContext2D) -> None:
    tutorial_session = getattr(loop, "tutorial_session", None)
    if tutorial_session is None:
        return
    payload = tutorial_runtime_consume_pending_setup_runtime(tutorial_session)
    if not isinstance(payload, dict):
        return
    step_id = str(payload.get("step_id", "")).strip().lower()
    tutorial_apply_step_setup_2d_runtime(loop.state, loop.cfg, payload)
    if step_id in _TUTORIAL_GRID_OFF_STEPS_2D:
        loop.grid_mode = GridMode.OFF
    elif step_id in _TUTORIAL_GRID_HELPER_STEPS_2D:
        loop.grid_mode = GridMode.HELPER
    start_overlay = _tutorial_overlay_start_from_setup(payload)
    if start_overlay is not None:
        loop.overlay_transparency = clamp_overlay_transparency_runtime(
            start_overlay,
            default=default_overlay_transparency_runtime(),
        )


def _tutorial_overlay_start_from_setup(payload: dict[str, object]) -> float | None:
    setup_payload = payload.get("setup")
    if not isinstance(setup_payload, dict):
        return None
    raw_percent = setup_payload.get("overlay_start_percent")
    if isinstance(raw_percent, bool) or not isinstance(raw_percent, int):
        return None
    bounded_percent = max(0, min(100, int(raw_percent)))
    return float(bounded_percent) / 100.0


def _configure_game_loop(
    *,
    loop: LoopContext2D,
    bot_speed_level: int,
    bot_algorithm_index: int,
    bot_profile_index: int,
    bot_budget_ms: int,
) -> int:
    gravity_interval_ms = gravity_interval_ms_from_config(loop.cfg)
    loop.bot.configure_speed(gravity_interval_ms, bot_speed_level)
    loop.bot.configure_planner(
        ndim=2,
        dims=(loop.cfg.width, loop.cfg.height),
        profile=bot_planner_profile_from_index(bot_profile_index),
        budget_ms=bot_budget_ms,
        algorithm=bot_planner_algorithm_from_index(bot_algorithm_index),
    )
    loop.refresh_score_multiplier()
    return gravity_interval_ms


def _sync_runtime_speed(loop: LoopContext2D) -> int:
    gravity_interval_ms = gravity_interval_ms_from_config(loop.cfg)
    loop.bot.configure_speed(gravity_interval_ms, int(loop.bot_speed_level))
    return gravity_interval_ms


def _open_help_screen(
    screen: pygame.Surface,
    fonts: GfxFonts,
    loop: LoopContext2D,
) -> pygame.Surface:
    return run_help_menu(
        screen,
        fonts,
        dimension=2,
        context_label="2D Gameplay",
        on_escape_back=lambda: loop._tutorial_observe_action("menu_back"),
    )


def _restart_tutorial_if_running_2d(loop: LoopContext2D) -> bool:
    tutorial_session = getattr(loop, "tutorial_session", None)
    if tutorial_session is None:
        return False
    if not tutorial_runtime_is_running_runtime(tutorial_session):
        return False
    loop._tutorial_observe_action("restart")
    restarted = tutorial_runtime_restart_runtime(tutorial_session)
    if not restarted:
        return False
    _apply_pending_tutorial_setup(loop)
    loop.tutorial_action_cooldown_ms = 0
    return True


def _pause_tutorial_restart_2d(loop: LoopContext2D) -> bool:
    if not _restart_tutorial_if_running_2d(loop):
        return False
    return True


def _pause_tutorial_skip_2d(loop: LoopContext2D) -> bool:
    if loop.tutorial_session is None:
        return False
    return bool(tutorial_runtime_skip_runtime(loop.tutorial_session))


def _resolve_loop_decision(
    *,
    decision: str,
    screen: pygame.Surface,
    fonts: GfxFonts,
    loop: LoopContext2D,
) -> tuple[str, pygame.Surface]:
    if decision == "quit":
        return "quit", screen
    if decision != "menu":
        return "continue", screen
    pause_decision, next_screen = run_pause_menu(
        screen,
        fonts,
        dimension=2,
        on_tutorial_restart=lambda: _pause_tutorial_restart_2d(loop),
        on_tutorial_skip=lambda: _pause_tutorial_skip_2d(loop),
        on_escape_back=lambda: loop._tutorial_observe_action("menu_back"),
    )
    if pause_decision == "quit":
        return "quit", next_screen
    if pause_decision == "menu":
        return "menu", next_screen
    if pause_decision == "restart":
        if _restart_tutorial_if_running_2d(loop):
            return "continue", next_screen
        loop.on_restart()
        return "restart", next_screen
    return "continue", next_screen


def _advance_simulation(
    *,
    loop: LoopContext2D,
    dt: int,
    gravity_interval_ms: int,
    tutorial_step_pause_active: bool = False,
) -> None:
    if tutorial_step_pause_active:
        loop.gravity_accumulator = 0
        return
    if loop.cfg.exploration_mode:
        loop.gravity_accumulator = 0
        return
    loop.bot.tick_2d(loop.state, dt)
    if loop.bot.controls_descent:
        loop.gravity_accumulator = 0
        return
    loop.gravity_accumulator = _step_gravity_tick(
        loop.state,
        loop.gravity_accumulator,
        gravity_interval_ms,
    )


def _update_feedback_and_animation(
    *,
    loop: LoopContext2D,
    dt: int,
    clear_anim_duration_ms: float,
) -> None:
    if loop.state.lines_cleared != loop.last_lines_cleared:
        play_sfx("clear")
    if loop.state.game_over and not loop.was_game_over:
        play_sfx("game_over")
    loop.was_game_over = loop.state.game_over
    (
        loop.clear_anim_levels,
        loop.clear_anim_elapsed_ms,
        loop.last_lines_cleared,
    ) = _update_clear_animation(
        state=loop.state,
        last_lines_cleared=loop.last_lines_cleared,
        clear_anim_levels=loop.clear_anim_levels,
        clear_anim_elapsed_ms=loop.clear_anim_elapsed_ms,
        clear_anim_duration_ms=clear_anim_duration_ms,
        dt_ms=dt,
    )


def _resolve_terminal_status(
    status: str,
    *,
    record_session: Callable[[str], None],
) -> bool | None:
    if status == "quit":
        record_session("quit")
        return False
    if status == "menu":
        record_session("menu")
        return True
    return None


def _handle_loop_event_cycle(
    *,
    screen: pygame.Surface,
    fonts: GfxFonts,
    loop: LoopContext2D,
    display_settings: DisplaySettings,
    restart_with_record: Callable[[], None],
    record_session: Callable[[str], None],
) -> tuple[pygame.Surface, DisplaySettings, bool | None, bool]:
    def _runtime_event_handler(event: pygame.event.Event) -> None:
        nonlocal display_settings
        display_settings = capture_windowed_display_settings_from_event(
            display_settings,
            event=event,
        )

    decision = process_game_events(
        keydown_handler=loop.keydown_handler,
        on_restart=restart_with_record,
        on_toggle_grid=loop.on_toggle_grid,
        event_handler=_runtime_event_handler,
    )
    if decision == "help":
        return _open_help_screen(screen, fonts, loop), display_settings, None, True

    status, next_screen = _resolve_loop_decision(
        decision=decision,
        screen=screen,
        fonts=fonts,
        loop=loop,
    )
    terminal = _resolve_terminal_status(status, record_session=record_session)
    if terminal is not None:
        return next_screen, display_settings, terminal, False
    if status == "restart":
        record_session("restart")
        return next_screen, display_settings, None, True
    return next_screen, display_settings, None, False


def _tutorial_target_cells_2d(loop: LoopContext2D) -> tuple[tuple[int, int], ...]:
    session = loop.tutorial_session
    if session is None:
        return ()
    payload = tutorial_runtime_overlay_payload_runtime(session)
    step_id = str(payload.get("step_id", "")).strip().lower()
    if step_id not in {"target_drop", "line_fill", "full_clear_bonus"}:
        return ()

    if step_id == "full_clear_bonus":
        candidate_rows = (loop.cfg.height - 2, loop.cfg.height - 1)
    else:
        candidate_rows = (loop.cfg.height - 1,)
    target_cells: list[tuple[int, int]] = []
    for y in candidate_rows:
        for x in range(loop.cfg.width):
            if (x, y) in loop.state.board.cells:
                continue
            target_cells.append((x, y))
    return tuple(target_cells)


def _draw_tutorial_targets_2d(screen: pygame.Surface, loop: LoopContext2D) -> None:
    target_cells = _tutorial_target_cells_2d(loop)
    if not target_cells:
        return
    board_offset, _panel_offset = compute_game_layout(screen, loop.cfg)
    ox, oy = board_offset
    for x, y in target_cells:
        rect = pygame.Rect(
            ox + x * CELL_SIZE + 2,
            oy + y * CELL_SIZE + 2,
            CELL_SIZE - 4,
            CELL_SIZE - 4,
        )
        fill = pygame.Surface(rect.size, pygame.SRCALPHA)
        fill.fill(_TUTORIAL_TARGET_FILL_RGBA)
        screen.blit(fill, rect.topleft)
        pygame.draw.rect(screen, _TUTORIAL_TARGET_BORDER_RGBA, rect, 2)


def _run_game_frame_2d(
    *,
    screen: pygame.Surface,
    fonts: GfxFonts,
    loop: LoopContext2D,
    dt: int,
    clear_anim_duration_ms: float,
) -> None:
    tutorial_step_pause_active = (
        loop.tutorial_session is not None
        and tutorial_runtime_is_running_runtime(loop.tutorial_session)
    )
    _gravity_interval_ms = _sync_runtime_speed(loop)
    _advance_simulation(
        loop=loop,
        dt=dt,
        gravity_interval_ms=_gravity_interval_ms,
        tutorial_step_pause_active=tutorial_step_pause_active,
    )
    _update_feedback_and_animation(
        loop=loop,
        dt=dt,
        clear_anim_duration_ms=clear_anim_duration_ms,
    )
    _maybe_apply_auto_speedup(loop)
    if loop.tutorial_session is not None:
        tutorial_runtime_sync_and_advance_runtime(
            loop.tutorial_session,
            lines_cleared=int(loop.state.lines_cleared),
            overlay_transparency=float(loop.overlay_transparency),
            grid_visible=bool(loop.grid_mode != GridMode.OFF),
            grid_mode=str(loop.grid_mode.value),
            board_cell_count=len(loop.state.board.cells),
        )
        _apply_pending_tutorial_setup(loop)
        _enforce_tutorial_runtime_safety_2d(loop)
        if not tutorial_runtime_is_running_runtime(loop.tutorial_session):
            loop.tutorial_session = None
            loop.tutorial_action_cooldown_ms = 0
    clear_effect = _clear_effect(
        loop.clear_anim_levels,
        loop.clear_anim_elapsed_ms,
        clear_anim_duration_ms,
    )
    loop.rotation_anim.observe(loop.state.current_piece, dt)
    active_overlay = loop.rotation_anim.overlay_cells(loop.state.current_piece)
    draw_game_frame(
        screen,
        loop.cfg,
        loop.state,
        fonts,
        grid_mode=loop.grid_mode,
        bot_lines=tuple(loop.bot.status_lines()),
        overlay_transparency=loop.overlay_transparency,
        clear_effect=clear_effect,
        active_piece_overlay=active_overlay,
    )
    if loop.tutorial_session is not None:
        _draw_tutorial_targets_2d(screen, loop)
        draw_tutorial_overlay(
            screen,
            fonts,
            dimension=2,
            tutorial_session=loop.tutorial_session,
        )
    pygame.display.flip()


def _apply_tutorial_min_board_dims_2d(
    cfg: GameConfig,
    *,
    tutorial_lesson_id: str | None,
) -> None:
    if not tutorial_lesson_id:
        return
    cfg.width = max(int(cfg.width), int(_TUTORIAL_MIN_WIDTH_2D))
    cfg.height = max(int(cfg.height), int(_TUTORIAL_MIN_HEIGHT_2D))


def _record_leaderboard_session_2d(
    *,
    tutorial_lesson_id: str | None,
    screen: pygame.Surface,
    fonts: GfxFonts,
    loop: LoopContext2D,
    session_start_ms: int,
    outcome: str,
) -> None:
    if tutorial_lesson_id:
        return
    elapsed_ms = max(0, pygame.time.get_ticks() - session_start_ms)
    try:
        maybe_record_leaderboard_session(
            screen,
            fonts,
            dimension=2,
            score=int(loop.state.score),
            lines_cleared=int(loop.state.lines_cleared),
            start_speed_level=int(loop.base_speed_level),
            end_speed_level=int(loop.cfg.speed_level),
            duration_seconds=float(elapsed_ms / 1000.0),
            outcome=outcome,
            bot_mode=str(loop.bot.mode.value),
            grid_mode=str(loop.grid_mode.value),
            random_mode=str(loop.cfg.rng_mode),
            topology_mode=str(loop.cfg.topology_mode),
            kick_level=str(loop.cfg.kick_level),
            exploration_mode=bool(loop.cfg.exploration_mode),
        )
    except Exception:
        return


def run_game_loop(
    screen: pygame.Surface,
    cfg: GameConfig,
    fonts: GfxFonts,
    display_settings: DisplaySettings,
    *,
    bot_mode: BotMode = BotMode.OFF,
    bot_speed_level: int = 7,
    bot_algorithm_index: int = 0,
    bot_profile_index: int = 1,
    bot_budget_ms: int = 12,
    tutorial_lesson_id: str | None = None,
) -> bool:
    """
    Run a single game session.
    Returns:
        True  -> user wants to go back to menu
        False -> user wants to quit the program
    """
    _apply_tutorial_min_board_dims_2d(
        cfg,
        tutorial_lesson_id=tutorial_lesson_id,
    )
    if cfg.exploration_mode:
        bot_mode = BotMode.OFF
    session_start_ms = pygame.time.get_ticks()

    def _record_session(outcome: str) -> None:
        _record_leaderboard_session_2d(
            tutorial_lesson_id=tutorial_lesson_id,
            screen=screen,
            fonts=fonts,
            loop=loop,
            session_start_ms=session_start_ms,
            outcome=outcome,
        )

    def _restart_with_record() -> None:
        if _restart_tutorial_if_running_2d(loop):
            return
        _record_session("restart")
        loop.on_restart()

    overlay_transparency = _load_overlay_transparency_for_runtime_2d()

    auto_speedup_enabled, lines_per_level = _load_speedup_settings_for_mode("2d")
    loop = LoopContext2D.create(
        cfg,
        bot_mode=bot_mode,
        bot_speed_level=bot_speed_level,
        auto_speedup_enabled=auto_speedup_enabled,
        lines_per_level=lines_per_level,
        overlay_transparency=overlay_transparency,
        tutorial_lesson_id=tutorial_lesson_id,
    )
    _apply_pending_tutorial_setup(loop)
    _configure_game_loop(
        loop=loop,
        bot_speed_level=bot_speed_level,
        bot_algorithm_index=bot_algorithm_index,
        bot_profile_index=bot_profile_index,
        bot_budget_ms=bot_budget_ms,
    )
    clear_anim_duration_ms = project_constant_float(
        ("animation", "clear_effect_duration_ms_2d"),
        320.0,
        min_value=120.0,
        max_value=1200.0,
    )

    clock = pygame.time.Clock()
    while True:
        dt = clock.tick(60)
        loop.gravity_accumulator += dt
        if hasattr(loop, "tutorial_action_cooldown_ms"):
            cooldown = int(getattr(loop, "tutorial_action_cooldown_ms", 0))
            if cooldown > 0:
                setattr(loop, "tutorial_action_cooldown_ms", max(0, cooldown - int(dt)))
        loop.refresh_score_multiplier()

        screen, display_settings, terminal, continue_loop = _handle_loop_event_cycle(
            screen=screen,
            fonts=fonts,
            loop=loop,
            display_settings=display_settings,
            restart_with_record=_restart_with_record,
            record_session=_record_session,
        )
        if terminal is not None:
            return terminal
        if continue_loop:
            continue
        _run_game_frame_2d(
            screen=screen,
            fonts=fonts,
            loop=loop,
            dt=dt,
            clear_anim_duration_ms=clear_anim_duration_ms,
        )

    # Normally not reached
    return False


# ---------- Main run ----------


def run():
    runtime = initialize_runtime(sync_audio_state=False)
    fonts = init_fonts()

    display_settings = DisplaySettings(
        fullscreen=runtime.display_settings.fullscreen,
        windowed_size=runtime.display_settings.windowed_size,
    )

    running = True
    while running:
        # --- MENU ---
        menu_screen = open_display(
            display_settings,
            caption="2D Tetris – Setup",
        )
        settings = run_menu(menu_screen, fonts)
        if settings is None:
            break  # user quit from menu

        # --- GAME ---
        cfg = GameConfig(
            width=settings.width,
            height=settings.height,
            gravity_axis=1,
            speed_level=settings.speed_level,
            piece_set=_piece_set_index_to_id(settings.piece_set_index),
            challenge_layers=settings.challenge_layers,
        )

        # Initial suggested window size; user can resize afterwards
        board_px_w = cfg.width * 30  # CELL_SIZE from gfx
        board_px_h = cfg.height * 30
        window_w = board_px_w + 200 + 3 * 20  # SIDE_PANEL + margins
        window_h = board_px_h + 2 * 20

        preferred_size = (
            max(window_w, display_settings.windowed_size[0]),
            max(window_h, display_settings.windowed_size[1]),
        )
        game_screen = open_display(
            display_settings,
            caption="2D Tetris",
            preferred_windowed_size=preferred_size,
        )

        back_to_menu = run_game_loop(
            game_screen,
            cfg,
            fonts,
            display_settings,
            bot_mode=bot_mode_from_index(settings.bot_mode_index),
            bot_speed_level=settings.bot_speed_level,
            bot_algorithm_index=settings.bot_algorithm_index,
            bot_profile_index=settings.bot_profile_index,
            bot_budget_ms=settings.bot_budget_ms,
        )
        display_settings = capture_windowed_display_settings(display_settings)
        if not back_to_menu:
            running = False
            continue

    pygame.quit()
    sys.exit()


def main(argv=None):
    if argv is None:
        if _PREPARSED_ARGS is None:
            _parse_cli_args(sys.argv[1:])
    else:
        _parse_cli_args(argv)
    run()


if __name__ == "__main__":
    main()
