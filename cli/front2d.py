# ruff: noqa: E402
# tetris_nd/frontend_pygame.py

import argparse
import sys
import random
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


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

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(1, str(_REPO_ROOT))

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
    ClearEffect2D,
    GfxFonts,
    init_fonts,
    draw_menu,
    draw_game_frame,
    gravity_interval_ms_from_config,
)
from tet4d.ui.pygame.keybindings import (
    DISABLED_KEYS_2D,
    KEYS_2D,
    SYSTEM_KEYS,
    active_key_profile,
    load_active_profile_bindings,
)
from tet4d.ui.pygame.input.key_dispatch import (
    dispatch_bound_action,
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
    setup_fields_for_dimension,
)
from tet4d.engine.runtime.menu_settings_state import (
    load_menu_settings,
    save_menu_settings,
)
from tet4d.engine.runtime.project_config import project_constant_float
from tet4d.engine.api import (
    PlayBotController,
    run_dry_run_2d,
    BotMode,
    bot_planner_algorithm_from_index,
    bot_mode_from_index,
    bot_planner_profile_from_index,
    runtime_assist_combined_score_multiplier,
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
from tet4d.ui.pygame.runtime_ui.pause_menu import run_pause_menu
from tet4d.ui.pygame.runtime_ui.help_menu import run_help_menu

RANDOM_MODE_FIXED_INDEX = 0
RANDOM_MODE_TRUE_RANDOM_INDEX = 1
_RANDOM_MODE_CHOICES = (
    RNG_MODE_FIXED_SEED,
    RNG_MODE_TRUE_RANDOM,
)
_RANDOM_MODE_LABELS = (
    "Fixed seed",
    "True random",
)
_DEFAULT_MODE_2D = default_settings_payload()["settings"]["2d"]


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
            extra_hint_lines=(
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
    handlers = {
        "move_x_neg": lambda: state.try_move(-1, 0),
        "move_x_pos": lambda: state.try_move(1, 0),
        "rotate_xy_pos": lambda: state.try_rotate(+1),
        "rotate_xy_neg": lambda: state.try_rotate(-1),
        "hard_drop": state.hard_drop,
        "soft_drop": lambda: state.try_move(0, 1),
    }
    if state.config.exploration_mode:
        handlers.update(
            {
                "move_y_neg": lambda: state.try_move(0, -1),
                "move_y_pos": lambda: state.try_move(0, 1),
            }
        )
    action = dispatch_bound_action(key, KEYS_2D, handlers)
    if action is None:
        return None
    if action.startswith("rotate_"):
        play_sfx("rotate")
    elif action == "hard_drop":
        play_sfx("drop")
    else:
        play_sfx("move")
    return action


def handle_game_keydown(
    event: pygame.event.Event,
    state: GameState,
    _cfg: GameConfig,
    *,
    allow_gameplay: bool = True,
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
        return system_decision

    if not allow_gameplay:
        return "continue"

    if state.game_over:
        # Don't react to movement keys when game over
        return "continue"

    # Explicitly disable ND-only controls in 2D mode.
    if key in DISABLED_KEYS_2D:
        return "continue"

    _dispatch_2d_gameplay_action(state, key)
    return "continue"


def _step_gravity_tick(
    state: GameState, gravity_accumulator: int, gravity_interval_ms: int
) -> int:
    if not state.game_over and gravity_accumulator >= gravity_interval_ms:
        state.step(Action.NONE)
        return 0
    return gravity_accumulator


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

    @classmethod
    def create(
        cls, cfg: GameConfig, *, bot_mode: BotMode = BotMode.OFF
    ) -> "LoopContext2D":
        state = create_initial_state(cfg)
        return cls(
            cfg=cfg,
            state=state,
            bot=PlayBotController(mode=bot_mode),
            last_lines_cleared=state.lines_cleared,
            was_game_over=state.game_over,
        )

    def keydown_handler(self, event: pygame.event.Event) -> str:
        if event.key == pygame.K_F2:
            self.bot.cycle_mode()
            self.refresh_score_multiplier()
            play_sfx("menu_move")
            return "continue"
        if event.key == pygame.K_F3:
            self.bot.request_step()
            play_sfx("menu_move")
            return "continue"
        return handle_game_keydown(
            event,
            self.state,
            self.cfg,
            allow_gameplay=self.bot.user_gameplay_enabled,
        )

    def on_restart(self) -> None:
        self.state = create_initial_state(self.cfg)
        self.gravity_accumulator = 0
        self.clear_anim_levels = ()
        self.clear_anim_elapsed_ms = 0.0
        self.last_lines_cleared = self.state.lines_cleared
        self.was_game_over = self.state.game_over
        self.bot.reset_runtime()
        self.rotation_anim.reset()
        self.refresh_score_multiplier()

    def on_toggle_grid(self) -> None:
        self.grid_mode = cycle_grid_mode(self.grid_mode)
        self.refresh_score_multiplier()

    def refresh_score_multiplier(self) -> None:
        self.state.score_multiplier = combined_score_multiplier(
            bot_mode=self.bot.mode,
            grid_mode=self.grid_mode,
            speed_level=self.cfg.speed_level,
        )
        mode_name = self.bot.mode.value
        self.state.analysis_actor_mode = (
            "human" if self.bot.mode == BotMode.OFF else mode_name
        )
        self.state.analysis_bot_mode = mode_name
        self.state.analysis_grid_mode = self.grid_mode.value


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


def _open_help_screen(screen: pygame.Surface, fonts: GfxFonts) -> pygame.Surface:
    return run_help_menu(
        screen,
        fonts,
        dimension=2,
        context_label="2D Gameplay",
    )


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
    pause_decision, next_screen = run_pause_menu(screen, fonts, dimension=2)
    if pause_decision == "quit":
        return "quit", next_screen
    if pause_decision == "menu":
        return "menu", next_screen
    if pause_decision == "restart":
        loop.on_restart()
        return "restart", next_screen
    return "continue", next_screen


def _advance_simulation(
    *,
    loop: LoopContext2D,
    dt: int,
    gravity_interval_ms: int,
) -> None:
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
) -> bool:
    """
    Run a single game session.
    Returns:
        True  -> user wants to go back to menu
        False -> user wants to quit the program
    """
    if cfg.exploration_mode:
        bot_mode = BotMode.OFF
    loop = LoopContext2D.create(cfg, bot_mode=bot_mode)
    gravity_interval_ms = _configure_game_loop(
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
        loop.refresh_score_multiplier()

        def _runtime_event_handler(event: pygame.event.Event) -> None:
            nonlocal display_settings
            display_settings = capture_windowed_display_settings_from_event(
                display_settings,
                event=event,
            )

        decision = process_game_events(
            keydown_handler=loop.keydown_handler,
            on_restart=loop.on_restart,
            on_toggle_grid=loop.on_toggle_grid,
            event_handler=_runtime_event_handler,
        )
        if decision == "help":
            screen = _open_help_screen(screen, fonts)
            continue
        status, screen = _resolve_loop_decision(
            decision=decision,
            screen=screen,
            fonts=fonts,
            loop=loop,
        )
        if status == "quit":
            return False
        if status == "menu":
            return True
        if status == "restart":
            continue

        _advance_simulation(
            loop=loop,
            dt=dt,
            gravity_interval_ms=gravity_interval_ms,
        )
        _update_feedback_and_animation(
            loop=loop,
            dt=dt,
            clear_anim_duration_ms=clear_anim_duration_ms,
        )
        clear_effect = _clear_effect(
            loop.clear_anim_levels,
            loop.clear_anim_elapsed_ms,
            clear_anim_duration_ms,
        )
        loop.rotation_anim.observe(loop.state.current_piece, dt)
        active_overlay = loop.rotation_anim.overlay_cells(loop.state.current_piece)

        # ----- Drawing -----
        draw_game_frame(
            screen,
            cfg,
            loop.state,
            fonts,
            grid_mode=loop.grid_mode,
            bot_lines=tuple(loop.bot.status_lines()),
            clear_effect=clear_effect,
            active_piece_overlay=active_overlay,
        )
        pygame.display.flip()

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
