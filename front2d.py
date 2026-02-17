# tetris_nd/frontend_pygame.py

import sys
import random
from dataclasses import dataclass, field
from typing import Optional

import pygame

from tetris_nd.app_runtime import (
    capture_windowed_display_settings,
    initialize_runtime,
    open_display,
)
from tetris_nd.audio import play_sfx
from tetris_nd.assist_scoring import combined_score_multiplier
from tetris_nd.board import BoardND
from tetris_nd.challenge_mode import apply_challenge_prefill_2d
from tetris_nd.display import DisplaySettings
from tetris_nd.game2d import GameConfig, GameState, Action
from tetris_nd.game_loop_common import process_game_events
from tetris_nd.gfx_game import (
    ClearEffect2D,
    GfxFonts,
    init_fonts,
    draw_menu,
    draw_game_frame,
    gravity_interval_ms_from_config,
)
from tetris_nd.keybindings import (
    DISABLED_KEYS_2D,
    KEYS_2D,
    SYSTEM_KEYS,
    active_key_profile,
    keybinding_file_label,
    load_active_profile_bindings,
)
from tetris_nd.key_dispatch import (
    dispatch_bound_action,
    match_bound_action,
)
from tetris_nd.menu_controls import (
    FieldSpec,
    apply_menu_actions,
    gather_menu_actions,
)
from tetris_nd.menu_settings_state import (
    load_menu_settings,
)
from tetris_nd.playbot import (
    BOT_MODE_OPTIONS,
    PlayBotController,
    bot_mode_label,
    run_dry_run_2d,
)
from tetris_nd.playbot.types import BotMode, bot_mode_from_index
from tetris_nd.pieces2d import piece_set_2d_label, PIECE_SET_2D_OPTIONS
from tetris_nd.rotation_anim import PieceRotationAnimator2D
from tetris_nd.view_modes import GridMode, cycle_grid_mode

DEFAULT_GAME_SEED = 1337


# ---------- Menu state & actions (logic, not drawing) ----------

@dataclass
class GameSettings:
    width: int = 10
    height: int = 20
    piece_set_index: int = 0
    bot_mode_index: int = 0
    bot_speed_level: int = 7
    challenge_layers: int = 0
    speed_level: int = 1  # 1..10, mapped to gravity interval


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


_MENU_FIELDS: list[FieldSpec] = [
    ("Board width", "width", 6, 16),
    ("Board height", "height", 12, 30),
    ("Piece set", "piece_set_index", 0, len(PIECE_SET_2D_OPTIONS) - 1),
    ("Playbot mode", "bot_mode_index", 0, len(BOT_MODE_OPTIONS) - 1),
    ("Bot speed", "bot_speed_level", 1, 10),
    ("Challenge layers", "challenge_layers", 0, 20),
    ("Speed level", "speed_level", 1, 10),
]


def _piece_set_index_to_id(index: int) -> str:
    safe_index = max(0, min(len(PIECE_SET_2D_OPTIONS) - 1, int(index)))
    return PIECE_SET_2D_OPTIONS[safe_index]


def _menu_value_formatter(attr_name: str, value: object) -> str:
    if attr_name == "piece_set_index":
        return piece_set_2d_label(_piece_set_index_to_id(int(value)))
    if attr_name == "bot_mode_index":
        return bot_mode_label(bot_mode_from_index(int(value)))
    if attr_name == "bot_speed_level":
        return f"{value}   (1 = slow bot, 10 = fast bot)"
    if attr_name == "challenge_layers":
        return str(value)
    if attr_name == "speed_level":
        return f"{value}   (1 = slow, 10 = fast)"
    return str(value)


def _config_from_settings(settings: GameSettings) -> GameConfig:
    return GameConfig(
        width=settings.width,
        height=settings.height,
        gravity_axis=1,
        speed_level=settings.speed_level,
        piece_set=_piece_set_index_to_id(settings.piece_set_index),
        challenge_layers=settings.challenge_layers,
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
        apply_menu_actions(state, actions, _MENU_FIELDS, 2)
        if state.run_dry_run:
            report = run_dry_run_2d(_config_from_settings(state.settings))
            state.bindings_status = report.reason
            state.bindings_status_error = not report.passed

        rebind_target = "-"
        if state.rebind_targets:
            group, action_name = state.rebind_targets[state.rebind_index % len(state.rebind_targets)]
            rebind_target = f"{group}.{action_name}"
        draw_menu(
            screen,
            fonts,
            state.settings,
            state.selected_index,
            bindings_file_hint=keybinding_file_label(2),
            extra_hint_lines=(
                f"Profile: {state.active_profile}   [ / ] cycle   N new   Backspace delete custom",
                "F5 save settings   F9 load settings   F8 reset defaults   F6 reset keys",
                "F7 dry-run verify (bot, no graphics)",
                (
                    f"B rebind {'ON' if state.rebind_mode else 'OFF'}   target: {rebind_target}   "
                    f"Tab/` change target   C conflict={state.rebind_conflict_mode}"
                ),
            ),
            bindings_status=state.bindings_status,
            bindings_status_error=state.bindings_status_error,
            menu_fields=_MENU_FIELDS,
            value_formatter=_menu_value_formatter,
        )
        pygame.display.flip()

    if state.start_game and state.running:
        return state.settings
    return None


# ---------- Game helpers ----------

def create_initial_state(cfg: GameConfig) -> GameState:
    board = BoardND((cfg.width, cfg.height))
    state = GameState(config=cfg, board=board, rng=random.Random(DEFAULT_GAME_SEED))
    apply_challenge_prefill_2d(state, layers=cfg.challenge_layers)
    return state


def _system_decision_for_key(key: int) -> str | None:
    system_action = match_bound_action(
        key,
        SYSTEM_KEYS,
        ("quit", "menu", "restart", "toggle_grid"),
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
    play_sfx("menu_move")
    return "toggle_grid"


def _dispatch_2d_gameplay_action(state: GameState, key: int) -> str | None:
    action = dispatch_bound_action(
        key,
        KEYS_2D,
        {
            "move_x_neg": lambda: state.try_move(-1, 0),
            "move_x_pos": lambda: state.try_move(1, 0),
            "rotate_xy_pos": lambda: state.try_rotate(+1),
            "rotate_xy_neg": lambda: state.try_rotate(-1),
            "hard_drop": state.hard_drop,
            "soft_drop": lambda: state.try_move(0, 1),
        },
    )
    if action is None:
        return None
    if action.startswith("rotate_"):
        play_sfx("rotate")
    elif action == "hard_drop":
        play_sfx("drop")
    else:
        play_sfx("move")
    return action


def handle_game_keydown(event: pygame.event.Event,
                        state: GameState,
                        cfg: GameConfig,
                        *,
                        allow_gameplay: bool = True) -> Optional[str]:
    """
    Handle a single KEYDOWN event during the game.
    Returns:
        "quit"        -> user wants to quit the program
        "menu"        -> user wants to go back to the menu
        "restart"     -> restart game with current config
        "toggle_grid" -> toggle board grid visibility
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


def _step_gravity_tick(state: GameState, gravity_accumulator: int, gravity_interval_ms: int) -> int:
    if not state.game_over and gravity_accumulator >= gravity_interval_ms:
        state.step(Action.NONE)
        return 0
    return gravity_accumulator


def _update_clear_animation(state: GameState,
                            last_lines_cleared: int,
                            clear_anim_levels: tuple[int, ...],
                            clear_anim_elapsed_ms: float,
                            clear_anim_duration_ms: float,
                            dt_ms: int) -> tuple[tuple[int, ...], float, int]:
    if state.lines_cleared != last_lines_cleared:
        clear_anim_levels = tuple(state.board.last_cleared_levels)
        clear_anim_elapsed_ms = 0.0
        last_lines_cleared = state.lines_cleared
    if clear_anim_levels:
        clear_anim_elapsed_ms += dt_ms
        if clear_anim_elapsed_ms >= clear_anim_duration_ms:
            return (), 0.0, last_lines_cleared
    return clear_anim_levels, clear_anim_elapsed_ms, last_lines_cleared


def _clear_effect(levels: tuple[int, ...],
                  elapsed_ms: float,
                  duration_ms: float) -> Optional[ClearEffect2D]:
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
    rotation_anim: PieceRotationAnimator2D = field(default_factory=PieceRotationAnimator2D)
    gravity_accumulator: int = 0
    grid_mode: GridMode = GridMode.FULL
    clear_anim_levels: tuple[int, ...] = ()
    clear_anim_elapsed_ms: float = 0.0
    last_lines_cleared: int = 0

    @classmethod
    def create(cls, cfg: GameConfig, *, bot_mode: BotMode = BotMode.OFF) -> "LoopContext2D":
        state = create_initial_state(cfg)
        return cls(
            cfg=cfg,
            state=state,
            bot=PlayBotController(mode=bot_mode),
            last_lines_cleared=state.lines_cleared,
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


def run_game_loop(screen: pygame.Surface,
                  cfg: GameConfig,
                  fonts: GfxFonts,
                  *,
                  bot_mode: BotMode = BotMode.OFF,
                  bot_speed_level: int = 7) -> bool:
    """
    Run a single game session.
    Returns:
        True  -> user wants to go back to menu
        False -> user wants to quit the program
    """
    loop = LoopContext2D.create(cfg, bot_mode=bot_mode)
    gravity_interval_ms = gravity_interval_ms_from_config(cfg)
    loop.bot.configure_speed(gravity_interval_ms, bot_speed_level)
    loop.refresh_score_multiplier()
    clear_anim_duration_ms = 320.0
    was_game_over = loop.state.game_over

    clock = pygame.time.Clock()
    while True:
        dt = clock.tick(60)
        loop.gravity_accumulator += dt
        loop.refresh_score_multiplier()

        decision = process_game_events(
            keydown_handler=loop.keydown_handler,
            on_restart=loop.on_restart,
            on_toggle_grid=loop.on_toggle_grid,
        )
        if decision == "quit":
            return False
        if decision == "menu":
            return True

        loop.bot.tick_2d(loop.state, dt)
        if loop.bot.controls_descent:
            loop.gravity_accumulator = 0
        else:
            loop.gravity_accumulator = _step_gravity_tick(
                loop.state,
                loop.gravity_accumulator,
                gravity_interval_ms,
            )
        if loop.state.lines_cleared != loop.last_lines_cleared:
            play_sfx("clear")
        if loop.state.game_over and not was_game_over:
            play_sfx("game_over")
        was_game_over = loop.state.game_over
        loop.clear_anim_levels, loop.clear_anim_elapsed_ms, loop.last_lines_cleared = _update_clear_animation(
            state=loop.state,
            last_lines_cleared=loop.last_lines_cleared,
            clear_anim_levels=loop.clear_anim_levels,
            clear_anim_elapsed_ms=loop.clear_anim_elapsed_ms,
            clear_anim_duration_ms=clear_anim_duration_ms,
            dt_ms=dt,
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
            bot_mode=bot_mode_from_index(settings.bot_mode_index),
            bot_speed_level=settings.bot_speed_level,
        )
        if not back_to_menu:
            running = False
            continue

        display_settings = capture_windowed_display_settings(display_settings)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    run()
