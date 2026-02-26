# tetris_nd/front4d_game.py
import math
import sys
from dataclasses import dataclass
from typing import Any, Optional, Tuple

import pygame

import tet4d.engine.api as engine_api
from tet4d.ui.pygame.runtime_ui.app_runtime import (
    initialize_runtime,
)
from tet4d.ui.pygame.runtime_ui.audio import play_sfx
from tet4d.ui.pygame.input.camera_mouse import (
    MouseOrbitState,
    apply_mouse_orbit_event,
    mouse_wheel_delta,
)
from tet4d.ui.pygame.runtime_ui.display import DisplaySettings
from tet4d.ai.playbot.types import (
    BotMode,
    bot_planner_algorithm_from_index,
    bot_mode_from_index,
    bot_planner_profile_from_index,
)
from tet4d.ui.pygame.loop.loop_runner_nd import run_nd_loop
from tet4d.ui.pygame.runtime_ui.pause_menu import run_pause_menu
from tet4d.ui.pygame.runtime_ui.help_menu import run_help_menu
from tet4d.ui.pygame.launch.launcher_nd_runner import run_nd_mode_launcher

GameConfigND = engine_api.GameConfigND
GameStateND = engine_api.GameStateND
PlayBotController = engine_api.PlayBotController
GfxFonts = Any
LAYER_GAP = engine_api.front4d_render_layer_gap()
MARGIN = engine_api.front4d_render_margin()
SIDE_PANEL = engine_api.front4d_render_side_panel()
LayerView3D = engine_api.front4d_render_layer_view3d_type()
ClearAnimation4D = engine_api.front4d_render_clear_animation_type()
draw_game_frame = engine_api.front4d_render_draw_game_frame_api
handle_view_key = engine_api.front4d_render_handle_view_key
movement_axis_overrides_for_view = engine_api.front4d_render_movement_axis_overrides
spawn_clear_animation_if_needed = engine_api.front4d_render_spawn_clear_anim
build_config = engine_api.front3d_setup_build_config_nd
create_initial_state = engine_api.front3d_setup_create_initial_state_nd
gravity_interval_ms_from_config = engine_api.front3d_setup_gravity_interval_ms_from_config_nd
route_nd_keydown = engine_api.frontend_nd_route_keydown
run_menu = engine_api.front3d_setup_run_menu_nd
init_fonts = engine_api.profile_4d_init_fonts
combined_score_multiplier = engine_api.runtime_assist_combined_score_multiplier
PieceRotationAnimatorND = engine_api.rotation_anim_piece_rotation_animator_nd_type()
GridMode = engine_api.GridMode
cycle_grid_mode = engine_api.grid_mode_cycle_view


@dataclass
class LoopContext4D:
    cfg: GameConfigND
    state: GameStateND
    view: LayerView3D
    mouse_orbit: MouseOrbitState
    bot: PlayBotController
    rotation_anim: PieceRotationAnimatorND
    grid_mode: GridMode = GridMode.FULL
    clear_anim: Optional[ClearAnimation4D] = None
    last_lines_cleared: int = 0
    gravity_accumulator: int = 0
    was_game_over: bool = False

    @classmethod
    def create(
        cls, cfg: GameConfigND, *, bot_mode: BotMode = BotMode.OFF
    ) -> "LoopContext4D":
        state = create_initial_state(cfg)
        return cls(
            cfg=cfg,
            state=state,
            view=LayerView3D(),
            mouse_orbit=MouseOrbitState(),
            bot=PlayBotController(mode=bot_mode),
            rotation_anim=PieceRotationAnimatorND(
                ndim=4, gravity_axis=cfg.gravity_axis
            ),
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
        return route_nd_keydown(
            event.key,
            self.state,
            yaw_deg_for_view_movement=self.view.yaw_deg,
            axis_overrides_by_action=movement_axis_overrides_for_view(
                self.view, self.cfg.dims
            ),
            view_key_handler=lambda key: handle_view_key(key, self.view),
            sfx_handler=play_sfx,
            allow_gameplay=self.bot.user_gameplay_enabled,
        )

    def on_restart(self) -> None:
        self.state = create_initial_state(self.cfg)
        self.gravity_accumulator = 0
        self.clear_anim = None
        self.last_lines_cleared = self.state.lines_cleared
        self.was_game_over = self.state.game_over
        self.mouse_orbit.reset()
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

    def pointer_event_handler(self, event: pygame.event.Event) -> None:
        wheel = mouse_wheel_delta(event)
        if wheel != 0:
            self.view.stop_animation()
            if wheel > 0:
                self.view.zoom_scale = min(2.6, self.view.zoom_scale * (1.08**wheel))
            else:
                self.view.zoom_scale = max(
                    0.45, self.view.zoom_scale / (1.08 ** abs(wheel))
                )
            return

        yaw_deg, pitch_deg, changed = apply_mouse_orbit_event(
            event,
            self.mouse_orbit,
            yaw_deg=self.view.yaw_deg,
            pitch_deg=self.view.pitch_deg,
        )
        if not changed:
            return
        self.view.stop_animation()
        self.view.yaw_deg = yaw_deg
        self.view.pitch_deg = pitch_deg


def handle_view_keydown(event: pygame.event.Event, view: LayerView3D) -> bool:
    return handle_view_key(event.key, view)


def run_game_loop(
    screen: pygame.Surface,
    cfg: GameConfigND,
    fonts: GfxFonts,
    *,
    bot_mode: BotMode = BotMode.OFF,
    bot_speed_level: int = 7,
    bot_algorithm_index: int = 0,
    bot_profile_index: int = 1,
    bot_budget_ms: int = 36,
) -> bool:
    if cfg.exploration_mode:
        bot_mode = BotMode.OFF
    gravity_interval_ms = gravity_interval_ms_from_config(cfg)
    loop = LoopContext4D.create(cfg, bot_mode=bot_mode)
    loop.bot.configure_speed(gravity_interval_ms, bot_speed_level)
    loop.bot.configure_planner(
        ndim=4,
        dims=cfg.dims,
        profile=bot_planner_profile_from_index(bot_profile_index),
        budget_ms=bot_budget_ms,
        algorithm=bot_planner_algorithm_from_index(bot_algorithm_index),
    )
    loop.refresh_score_multiplier()
    return run_nd_loop(
        screen=screen,
        fonts=fonts,
        loop=loop,
        gravity_interval_ms=gravity_interval_ms,
        pause_dimension=4,
        run_pause_menu=run_pause_menu,
        run_help_menu=lambda target, active_fonts, dim, ctx: run_help_menu(
            target,
            active_fonts,
            dimension=dim,
            context_label=ctx,
        ),
        spawn_clear_animation=spawn_clear_animation_if_needed,
        step_view=loop.view.step_animation,
        draw_frame=lambda target, active_overlay: draw_game_frame(
            target,
            loop.state,
            loop.view,
            fonts,
            grid_mode=loop.grid_mode,
            bot_lines=tuple(loop.bot.status_lines()),
            clear_anim=loop.clear_anim,
            active_overlay=active_overlay,
        ),
        play_clear_sfx=lambda: play_sfx("clear"),
        play_game_over_sfx=lambda: play_sfx("game_over"),
    )


def suggested_window_size(cfg: GameConfigND) -> Tuple[int, int]:
    layers = cfg.dims[3]
    cols = max(1, math.ceil(math.sqrt(layers)))
    rows = max(1, math.ceil(layers / cols))
    board_w = cols * 250 + (cols + 1) * LAYER_GAP
    board_h = rows * 230 + (rows + 1) * LAYER_GAP
    return max(1200, board_w + SIDE_PANEL + 3 * MARGIN), max(760, board_h + 2 * MARGIN)


def run() -> None:
    runtime = initialize_runtime(sync_audio_state=False)
    display_settings = DisplaySettings(
        fullscreen=runtime.display_settings.fullscreen,
        windowed_size=runtime.display_settings.windowed_size,
    )
    fonts = init_fonts()

    run_nd_mode_launcher(
        display_settings=display_settings,
        fonts=fonts,
        setup_caption="4D Tetris – Setup",
        game_caption="4D Tetris",
        run_menu=lambda menu_screen, active_fonts: run_menu(
            menu_screen, active_fonts, 4
        ),
        build_config=lambda settings: build_config(settings, 4),
        suggested_window_size=suggested_window_size,
        run_game=lambda game_screen, cfg, active_fonts, settings: run_game_loop(
            game_screen,
            cfg,
            active_fonts,
            bot_mode=bot_mode_from_index(settings.bot_mode_index),
            bot_speed_level=settings.bot_speed_level,
            bot_algorithm_index=settings.bot_algorithm_index,
            bot_profile_index=settings.bot_profile_index,
            bot_budget_ms=settings.bot_budget_ms,
        ),
    )

    pygame.quit()
    sys.exit()
