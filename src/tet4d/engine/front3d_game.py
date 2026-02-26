# tetris_nd/front3d_game.py
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Optional

import pygame

from .app_runtime import initialize_runtime
from tet4d.ui.pygame.audio import play_sfx
from .runtime.assist_scoring import combined_score_multiplier
from tet4d.ui.pygame.camera_mouse import (
    MouseOrbitState,
    apply_mouse_orbit_event,
    mouse_wheel_delta,
)
from tet4d.ui.pygame.display import DisplaySettings
from .front3d_render import (
    Camera3D,
    ClearAnimation3D,
    GfxFonts,
    color_for_cell_3d,
    draw_game_frame,
    init_fonts,
    suggested_window_size,
)
from tet4d.ui.pygame.front3d_setup import (
    build_config,
    create_initial_state,
    gravity_interval_ms_from_config,
    run_menu,
)
from .frontend_nd import route_nd_keydown
from .gameplay.game_nd import GameConfigND, GameStateND
from .help_menu import run_help_menu
from .ui_logic.key_dispatch import dispatch_bound_action
from .keybindings import CAMERA_KEYS_3D
from tet4d.ui.pygame.launcher_nd_runner import run_nd_mode_launcher
from tet4d.ui.pygame.loop_runner_nd import run_nd_loop
from .pause_menu import run_pause_menu
from .playbot import PlayBotController
from tet4d.ai.playbot.types import (
    BotMode,
    bot_mode_from_index,
    bot_planner_algorithm_from_index,
    bot_planner_profile_from_index,
)
from .gameplay.rotation_anim import PieceRotationAnimatorND
from .runtime.runtime_helpers import collect_cleared_ghost_cells
from .ui_logic.view_modes import GridMode, cycle_grid_mode


def handle_camera_key(key: int, camera: Camera3D) -> bool:
    return (
        dispatch_bound_action(
            key,
            CAMERA_KEYS_3D,
            {
                "yaw_fine_neg": lambda: camera.start_yaw_turn(-15.0),
                "yaw_neg": lambda: camera.start_yaw_turn(-90.0),
                "yaw_pos": lambda: camera.start_yaw_turn(90.0),
                "yaw_fine_pos": lambda: camera.start_yaw_turn(15.0),
                "pitch_pos": lambda: camera.start_pitch_turn(90.0),
                "pitch_neg": lambda: camera.start_pitch_turn(-90.0),
                "zoom_in": lambda: setattr(
                    camera, "zoom", min(140.0, camera.zoom + 3.0)
                ),
                "zoom_out": lambda: setattr(
                    camera, "zoom", max(18.0, camera.zoom - 3.0)
                ),
                "reset": camera.reset,
                "cycle_projection": camera.cycle_projection,
            },
        )
        is not None
    )


def handle_camera_keydown(event: pygame.event.Event, camera: Camera3D) -> bool:
    return handle_camera_key(event.key, camera)


def handle_game_keydown(
    event: pygame.event.Event,
    state: GameStateND,
    camera: Camera3D | GameConfigND | None = None,
    _cfg: GameConfigND | None = None,
    *,
    allow_gameplay: bool = True,
) -> str:
    yaw_for_movement = camera.yaw_deg if isinstance(camera, Camera3D) else 32.0
    return route_nd_keydown(
        event.key,
        state,
        yaw_deg_for_view_movement=yaw_for_movement,
        sfx_handler=play_sfx,
        allow_gameplay=allow_gameplay,
    )


def _spawn_clear_animation_if_needed(
    state: GameStateND,
    last_lines_cleared: int,
) -> tuple[Optional[ClearAnimation3D], int]:
    if state.lines_cleared == last_lines_cleared:
        return None, last_lines_cleared

    raw_ghost_cells = collect_cleared_ghost_cells(
        state,
        expected_coord_len=3,
        color_for_cell=color_for_cell_3d,
    )
    ghost_cells = tuple(
        ((coord[0], coord[1], coord[2]), color) for coord, color in raw_ghost_cells
    )
    if not ghost_cells:
        return None, state.lines_cleared
    return ClearAnimation3D(ghost_cells=tuple(ghost_cells)), state.lines_cleared


@dataclass
class LoopContext3D:
    cfg: GameConfigND
    state: GameStateND
    camera: Camera3D = field(default_factory=Camera3D)
    mouse_orbit: MouseOrbitState = field(default_factory=MouseOrbitState)
    bot: PlayBotController = field(default_factory=PlayBotController)
    rotation_anim: PieceRotationAnimatorND = field(
        default_factory=lambda: PieceRotationAnimatorND(ndim=3, gravity_axis=1)
    )
    grid_mode: GridMode = GridMode.FULL
    clear_anim: Optional[ClearAnimation3D] = None
    last_lines_cleared: int = 0
    gravity_accumulator: int = 0
    was_game_over: bool = False

    @classmethod
    def create(
        cls, cfg: GameConfigND, *, bot_mode: BotMode = BotMode.OFF
    ) -> "LoopContext3D":
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
        return route_nd_keydown(
            event.key,
            self.state,
            yaw_deg_for_view_movement=self.camera.yaw_deg,
            view_key_handler=lambda key: handle_camera_key(key, self.camera),
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
            self.camera.stop_animation()
            self.camera.auto_fit_once = False
            step = 3.0 * abs(wheel)
            if wheel > 0:
                self.camera.zoom = min(140.0, self.camera.zoom + step)
            else:
                self.camera.zoom = max(18.0, self.camera.zoom - step)
            return

        yaw_deg, pitch_deg, changed = apply_mouse_orbit_event(
            event,
            self.mouse_orbit,
            yaw_deg=self.camera.yaw_deg,
            pitch_deg=self.camera.pitch_deg,
        )
        if not changed:
            return
        self.camera.stop_animation()
        self.camera.auto_fit_once = False
        self.camera.yaw_deg = yaw_deg
        self.camera.pitch_deg = pitch_deg


def run_game_loop(
    screen: pygame.Surface,
    cfg: GameConfigND,
    fonts: GfxFonts,
    *,
    bot_mode: BotMode = BotMode.OFF,
    bot_speed_level: int = 7,
    bot_algorithm_index: int = 0,
    bot_profile_index: int = 1,
    bot_budget_ms: int = 24,
) -> bool:
    if cfg.exploration_mode:
        bot_mode = BotMode.OFF
    gravity_interval_ms = gravity_interval_ms_from_config(cfg)
    loop = LoopContext3D.create(cfg, bot_mode=bot_mode)
    loop.bot.configure_speed(gravity_interval_ms, bot_speed_level)
    loop.bot.configure_planner(
        ndim=3,
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
        pause_dimension=3,
        run_pause_menu=run_pause_menu,
        run_help_menu=lambda target, active_fonts, dim, ctx: run_help_menu(
            target,
            active_fonts,
            dimension=dim,
            context_label=ctx,
        ),
        spawn_clear_animation=_spawn_clear_animation_if_needed,
        step_view=loop.camera.step_animation,
        draw_frame=lambda target, active_overlay: draw_game_frame(
            target,
            loop.state,
            loop.camera,
            fonts,
            grid_mode=loop.grid_mode,
            bot_lines=tuple(loop.bot.status_lines()),
            clear_anim=loop.clear_anim,
            active_overlay=active_overlay,
        ),
        play_clear_sfx=lambda: play_sfx("clear"),
        play_game_over_sfx=lambda: play_sfx("game_over"),
    )


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
        setup_caption="3D Tetris – Setup",
        game_caption="3D Tetris",
        run_menu=lambda menu_screen, active_fonts: run_menu(menu_screen, active_fonts),
        build_config=build_config,
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
