from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable, Optional

import pygame

from tet4d.ai.playbot import PlayBotController
from tet4d.ai.playbot.types import (
    BotMode,
    bot_planner_algorithm_from_index,
    bot_planner_profile_from_index,
)
from tet4d.engine.core.model import Action, BoardND
from tet4d.engine.core.rng import RNG_MODE_TRUE_RANDOM
from tet4d.engine.gameplay.api import runtime_assist_combined_score_multiplier
from tet4d.engine.gameplay.challenge_mode import apply_challenge_prefill_2d
from tet4d.engine.gameplay.game2d import GameConfig, GameState
from tet4d.engine.gameplay.leveling import compute_speed_level
from tet4d.engine.gameplay.rotation_anim import PieceRotationAnimator2D
from tet4d.engine.runtime.menu_settings_state import (
    DEFAULT_OVERLAY_TRANSPARENCY,
    clamp_overlay_transparency,
)
from tet4d.engine.runtime.project_config import project_constant_float
from tet4d.engine.runtime.settings_schema import (
    clamp_lines_per_level,
    clamp_toggle_index,
)
from tet4d.engine.tutorial.api import (
    tutorial_runtime_is_running_runtime,
    tutorial_runtime_sync_and_advance_runtime,
)
from tet4d.engine.ui_logic.view_modes import GridMode, cycle_grid_mode
from tet4d.ui.pygame.launch.leaderboard_menu import maybe_record_leaderboard_session
from tet4d.ui.pygame.render.gfx_game import (
    ClearEffect2D,
    GfxFonts,
    draw_game_frame,
    gravity_interval_ms_from_config,
)
from tet4d.ui.pygame.runtime_ui.app_runtime import (
    DisplaySettings,
    capture_windowed_display_settings_from_event,
)
from tet4d.ui.pygame.runtime_ui.audio import play_sfx
from tet4d.ui.pygame.runtime_ui.loop_runner_nd import process_game_events
from tet4d.ui.pygame.runtime_ui.pause_menu import run_pause_menu

from .front2d_input import handle_game_keydown
from .front2d_setup import (
    _AUTO_SPEEDUP_ENABLED_DEFAULT,
    _LINES_PER_LEVEL_DEFAULT,
    load_overlay_transparency_for_runtime_2d as _load_overlay_transparency_for_runtime_2d,
    load_speedup_settings_for_mode as _load_speedup_settings_for_mode,
)
from .front2d_tutorial import (
    apply_pending_tutorial_setup,
    apply_tutorial_board_profile_2d,
    draw_tutorial_overlays_2d,
    enforce_tutorial_runtime_safety_2d,
    handle_overlay_hotkey,
    handle_tutorial_hotkey,
    open_help_screen,
    pause_tutorial_restart_2d,
    pause_tutorial_skip_2d,
    restart_tutorial_if_running_2d,
    tutorial_action_allowed,
    tutorial_create_session_2d,
    tutorial_observe_action,
)


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


def _step_gravity_tick(
    state: GameState, gravity_accumulator: int, gravity_interval_ms: int
) -> int:
    if not state.game_over and gravity_accumulator >= gravity_interval_ms:
        state.step(Action.NONE)
        return 0
    return gravity_accumulator


def _update_clear_animation(
    *,
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
    overlay_transparency: float = field(
        default_factory=lambda: float(DEFAULT_OVERLAY_TRANSPARENCY)
    )
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
        apply_tutorial_board_profile_2d(
            cfg,
            tutorial_lesson_id=tutorial_lesson_id,
        )
        state = create_initial_state(cfg)
        tutorial_session = None
        if tutorial_lesson_id:
            tutorial_session = tutorial_create_session_2d(
                lesson_id=tutorial_lesson_id,
            )
        return cls(
            cfg=cfg,
            state=state,
            bot=PlayBotController(mode=bot_mode),
            last_lines_cleared=state.lines_cleared,
            was_game_over=state.game_over,
            base_speed_level=int(cfg.speed_level),
            bot_speed_level=int(bot_speed_level),
            auto_speedup_enabled=clamp_toggle_index(
                auto_speedup_enabled,
                default=_AUTO_SPEEDUP_ENABLED_DEFAULT,
            ),
            lines_per_level=clamp_lines_per_level(
                lines_per_level,
                default=_LINES_PER_LEVEL_DEFAULT,
            ),
            overlay_transparency=clamp_overlay_transparency(
                overlay_transparency,
                default=float(DEFAULT_OVERLAY_TRANSPARENCY),
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
        return handle_tutorial_hotkey(self, key)

    def _handle_overlay_hotkey(self, key: int) -> bool:
        return handle_overlay_hotkey(self, key)

    def _tutorial_action_allowed(self, action_id: str) -> bool:
        return tutorial_action_allowed(self, action_id)

    def _tutorial_observe_action(self, action_id: str) -> None:
        tutorial_observe_action(self, action_id)

    def adjust_overlay_transparency(self, direction: int) -> None:
        self.overlay_transparency = clamp_overlay_transparency(
            self.overlay_transparency + (0.05 * direction),
            default=float(DEFAULT_OVERLAY_TRANSPARENCY),
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
        self.state.score_multiplier = runtime_assist_combined_score_multiplier(
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
    target_speed_level = compute_speed_level(
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
        on_tutorial_restart=lambda: pause_tutorial_restart_2d(loop),
        on_tutorial_skip=lambda: pause_tutorial_skip_2d(loop),
        on_escape_back=lambda: tutorial_observe_action(loop, "menu_back"),
    )
    if pause_decision == "quit":
        return "quit", next_screen
    if pause_decision == "menu":
        return "menu", next_screen
    if pause_decision == "restart":
        if restart_tutorial_if_running_2d(loop):
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
    if tutorial_step_pause_active or loop.cfg.exploration_mode:
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
        return open_help_screen(screen, fonts, loop), display_settings, None, True

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
    gravity_interval_ms = _sync_runtime_speed(loop)
    _advance_simulation(
        loop=loop,
        dt=dt,
        gravity_interval_ms=gravity_interval_ms,
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
        apply_pending_tutorial_setup(loop)
        enforce_tutorial_runtime_safety_2d(loop)
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
    draw_tutorial_overlays_2d(screen, fonts, loop)
    pygame.display.flip()


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
        if restart_tutorial_if_running_2d(loop):
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
    apply_pending_tutorial_setup(loop)
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
        cooldown = int(getattr(loop, "tutorial_action_cooldown_ms", 0))
        if cooldown > 0:
            loop.tutorial_action_cooldown_ms = max(0, cooldown - int(dt))
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

    return False
