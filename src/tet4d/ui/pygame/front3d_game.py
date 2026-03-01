# tetris_nd/front3d_game.py
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

import pygame

import tet4d.engine.api as engine_api
from tet4d.ui.pygame.runtime_ui.app_runtime import (
    capture_windowed_display_settings_from_event,
    initialize_runtime,
)
from tet4d.ui.pygame.runtime_ui.audio import play_sfx
from tet4d.ui.pygame.input.camera_mouse import (
    MouseOrbitState,
    apply_mouse_orbit_event,
    mouse_wheel_delta,
)
from tet4d.ui.pygame.runtime_ui.app_runtime import DisplaySettings
from tet4d.ui.pygame.runtime_ui.help_menu import run_help_menu
from tet4d.ui.pygame.input.key_dispatch import dispatch_bound_action
from tet4d.ui.pygame.keybindings import CAMERA_KEYS_3D
from tet4d.ui.pygame.launch.launcher_nd_runner import run_nd_mode_launcher
from tet4d.ui.pygame.launch.launcher_play import (
    game_caption_for_dimension,
    setup_caption_for_dimension,
)
from tet4d.ui.pygame.runtime_ui.loop_runner_nd import run_nd_loop
from tet4d.ui.pygame.runtime_ui.pause_menu import run_pause_menu
from tet4d.ai.playbot.types import (
    BotMode,
    bot_mode_from_index,
    bot_planner_algorithm_from_index,
    bot_planner_profile_from_index,
)

GameConfigND = engine_api.GameConfigND
GameStateND = engine_api.GameStateND
PlayBotController = engine_api.PlayBotController
GfxFonts = Any
Camera3D = engine_api.front3d_render_camera_type()
ClearAnimation3D = engine_api.front3d_render_clear_animation_type()
color_for_cell_3d = engine_api.front3d_render_color_for_cell_3d
draw_game_frame = engine_api.front3d_render_draw_game_frame
init_fonts = engine_api.front3d_render_init_fonts
suggested_window_size = engine_api.front3d_render_suggested_window_size
route_nd_keydown = engine_api.frontend_nd_route_keydown
build_config = engine_api.front3d_setup_build_config_nd
create_initial_state = engine_api.front3d_setup_create_initial_state_nd
gravity_interval_ms_from_config = (
    engine_api.front3d_setup_gravity_interval_ms_from_config_nd
)
run_menu = engine_api.front3d_setup_run_menu_nd
combined_score_multiplier = engine_api.runtime_assist_combined_score_multiplier
collect_cleared_ghost_cells = engine_api.runtime_collect_cleared_ghost_cells
PieceRotationAnimatorND = engine_api.rotation_anim_piece_rotation_animator_nd_type()
GridMode = engine_api.GridMode
cycle_grid_mode = engine_api.grid_mode_cycle_view
clamp_overlay_transparency = engine_api.clamp_overlay_transparency_runtime
overlay_transparency_step = engine_api.overlay_transparency_step_runtime
default_overlay_transparency = engine_api.default_overlay_transparency_runtime


def handle_camera_key(
    key: int,
    camera: Camera3D,
    *,
    on_overlay_alpha_dec: Callable[[], None] | None = None,
    on_overlay_alpha_inc: Callable[[], None] | None = None,
) -> bool:
    overlay_alpha_dec_handler = (
        on_overlay_alpha_dec if on_overlay_alpha_dec is not None else (lambda: None)
    )
    overlay_alpha_inc_handler = (
        on_overlay_alpha_inc if on_overlay_alpha_inc is not None else (lambda: None)
    )
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
                "overlay_alpha_dec": overlay_alpha_dec_handler,
                "overlay_alpha_inc": overlay_alpha_inc_handler,
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
    overlay_transparency: float = field(default_factory=default_overlay_transparency)
    grid_mode: GridMode = GridMode.FULL
    clear_anim: Optional[ClearAnimation3D] = None
    last_lines_cleared: int = 0
    gravity_accumulator: int = 0
    was_game_over: bool = False

    @classmethod
    def create(
        cls,
        cfg: GameConfigND,
        *,
        bot_mode: BotMode = BotMode.OFF,
        overlay_transparency: float | None = None,
    ) -> "LoopContext3D":
        state = create_initial_state(cfg)
        overlay_default = default_overlay_transparency()
        return cls(
            cfg=cfg,
            state=state,
            bot=PlayBotController(mode=bot_mode),
            overlay_transparency=clamp_overlay_transparency(
                overlay_transparency,
                default=overlay_default,
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
            yaw_deg_for_view_movement=self.camera.yaw_deg,
            view_key_handler=lambda key: handle_camera_key(
                key,
                self.camera,
                on_overlay_alpha_dec=lambda: self.adjust_overlay_transparency(-1),
                on_overlay_alpha_inc=lambda: self.adjust_overlay_transparency(1),
            ),
            sfx_handler=play_sfx,
            allow_gameplay=self.bot.user_gameplay_enabled,
        )

    def adjust_overlay_transparency(self, direction: int) -> None:
        self.overlay_transparency = clamp_overlay_transparency(
            self.overlay_transparency + (overlay_transparency_step() * direction),
            default=default_overlay_transparency(),
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
    display_payload = engine_api.get_display_settings_runtime()
    fullscreen = (
        bool(display_payload.get("fullscreen", False))
        if isinstance(display_payload, dict)
        else False
    )
    display_settings = DisplaySettings(
        fullscreen=fullscreen,
        windowed_size=screen.get_size(),
    )
    default_overlay = default_overlay_transparency()
    overlay_transparency = (
        clamp_overlay_transparency(
            display_payload.get("overlay_transparency"),
            default=default_overlay,
        )
        if isinstance(display_payload, dict)
        else default_overlay
    )
    loop = LoopContext3D.create(
        cfg,
        bot_mode=bot_mode,
        overlay_transparency=overlay_transparency,
    )
    loop.bot.configure_speed(gravity_interval_ms, bot_speed_level)
    loop.bot.configure_planner(
        ndim=3,
        dims=cfg.dims,
        profile=bot_planner_profile_from_index(bot_profile_index),
        budget_ms=bot_budget_ms,
        algorithm=bot_planner_algorithm_from_index(bot_algorithm_index),
    )
    loop.refresh_score_multiplier()

    def runtime_event_handler(event: pygame.event.Event) -> None:
        nonlocal display_settings
        display_settings = capture_windowed_display_settings_from_event(
            display_settings,
            event=event,
        )
        loop.pointer_event_handler(event)

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
            overlay_transparency=loop.overlay_transparency,
        ),
        play_clear_sfx=lambda: play_sfx("clear"),
        play_game_over_sfx=lambda: play_sfx("game_over"),
        event_handler=runtime_event_handler,
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
        setup_caption=setup_caption_for_dimension(3),
        game_caption=game_caption_for_dimension(3),
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
