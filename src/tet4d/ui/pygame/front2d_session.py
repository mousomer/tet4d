from __future__ import annotations

import random
from dataclasses import dataclass, field

import pygame

from tet4d.ai.playbot import PlayBotController
from tet4d.ai.playbot.types import BotMode
from tet4d.engine.core.model import BoardND
from tet4d.engine.core.rng import RNG_MODE_TRUE_RANDOM
from tet4d.engine.gameplay.api import runtime_assist_combined_score_multiplier
from tet4d.engine.gameplay.challenge_mode import apply_challenge_prefill_2d
from tet4d.engine.gameplay.game2d import GameConfig, GameState
from tet4d.engine.gameplay.rotation_anim import PieceRotationAnimator2D
from tet4d.engine.runtime.menu_settings_state import (
    DEFAULT_OVERLAY_TRANSPARENCY,
    clamp_overlay_transparency,
)
from tet4d.engine.runtime.settings_schema import (
    clamp_lines_per_level,
    clamp_toggle_index,
)
from tet4d.engine.ui_logic.view_modes import GridMode, cycle_grid_mode
from tet4d.ui.pygame.runtime_ui.audio import play_sfx

from .front2d_input import handle_game_keydown
from .front2d_setup import (
    _AUTO_SPEEDUP_ENABLED_DEFAULT,
    _LINES_PER_LEVEL_DEFAULT,
)
from .front2d_tutorial import (
    apply_tutorial_board_profile_2d,
    handle_overlay_hotkey,
    handle_tutorial_hotkey,
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
        rotation_animation_mode: str | None = None,
        rotation_animation_duration_ms: int | float | None = None,
        translation_animation_duration_ms: int | float | None = None,
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
            rotation_anim=PieceRotationAnimator2D(
                rotation_animation_mode=(
                    str(rotation_animation_mode)
                    if rotation_animation_mode is not None
                    else PieceRotationAnimator2D().rotation_animation_mode
                ),
                duration_ms=(
                    float(rotation_animation_duration_ms)
                    if rotation_animation_duration_ms is not None
                    else PieceRotationAnimator2D().duration_ms
                ),
                translation_duration_ms=(
                    float(translation_animation_duration_ms)
                    if translation_animation_duration_ms is not None
                    else PieceRotationAnimator2D().translation_duration_ms
                ),
            ),
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
