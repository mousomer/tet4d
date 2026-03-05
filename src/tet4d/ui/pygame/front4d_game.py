# tetris_nd/front4d_game.py
import math
import sys
from dataclasses import dataclass
from typing import Any, Optional, Tuple

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
from tet4d.ai.playbot.types import (
    BotMode,
    bot_planner_algorithm_from_index,
    bot_mode_from_index,
    bot_planner_profile_from_index,
)
from tet4d.ui.pygame.runtime_ui.loop_runner_nd import run_nd_loop
from tet4d.ui.pygame.runtime_ui.pause_menu import run_pause_menu
from tet4d.ui.pygame.runtime_ui.help_menu import run_help_menu
from tet4d.ui.pygame.runtime_ui.tutorial_overlay import tutorial_panel_last_rect
from tet4d.ui.pygame.runtime_ui.panel_drag import (
    PanelDragMixin,
    helper_panel_rect_for_surface,
)
from tet4d.ui.pygame.runtime_ui.tutorial_loop_common import (
    handle_tutorial_hotkey,
    maintain_tutorial_runtime_safety,
    redo_tutorial_stage,
    refresh_score_multiplier_state,
    restart_loop_runtime_state,
    running_tutorial_session,
    tutorial_allowed_actions_blocked,
    tutorial_action_delay_ms,
    tutorial_overlay_start_from_setup,
    tutorial_required_action_blocked,
    tutorial_sync,
)

from tet4d.ui.pygame.input.key_dispatch import match_bound_action
from tet4d.ui.pygame.keybindings import CAMERA_KEYS_4D
from tet4d.ui.pygame.launch.launcher_nd_runner import run_nd_mode_launcher
from tet4d.ui.pygame.launch.launcher_play import (
    game_caption_for_dimension,
    setup_caption_for_dimension,
)

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
viewer_axes_for_view = engine_api.front4d_render_viewer_axes_for_view
spawn_clear_animation_if_needed = engine_api.front4d_render_spawn_clear_anim
build_config = engine_api.front3d_setup_build_config_nd
create_initial_state = engine_api.front3d_setup_create_initial_state_nd
gravity_interval_ms_from_config = (
    engine_api.front3d_setup_gravity_interval_ms_from_config_nd
)
route_nd_keydown = engine_api.frontend_nd_route_keydown
run_menu = engine_api.front3d_setup_run_menu_nd
init_fonts = engine_api.profile_4d_init_fonts
combined_score_multiplier = engine_api.runtime_assist_combined_score_multiplier
PieceRotationAnimatorND = engine_api.rotation_anim_piece_rotation_animator_nd_type()
GridMode = engine_api.GridMode
cycle_grid_mode = engine_api.grid_mode_cycle_view
clamp_overlay_transparency = engine_api.clamp_overlay_transparency_runtime
overlay_transparency_step = engine_api.overlay_transparency_step_runtime
default_overlay_transparency = engine_api.default_overlay_transparency_runtime
tutorial_runtime_create_session = engine_api.tutorial_runtime_create_session_runtime
tutorial_runtime_action_allowed = engine_api.tutorial_runtime_action_allowed_runtime
tutorial_runtime_observe_action = engine_api.tutorial_runtime_observe_action_runtime
tutorial_runtime_sync_and_advance = engine_api.tutorial_runtime_sync_and_advance_runtime
tutorial_runtime_consume_pending_setup = (
    engine_api.tutorial_runtime_consume_pending_setup_runtime
)
tutorial_apply_step_setup_nd = engine_api.tutorial_apply_step_setup_nd_runtime
tutorial_runtime_restart = engine_api.tutorial_runtime_restart_runtime
tutorial_runtime_previous_stage = engine_api.tutorial_runtime_previous_stage_runtime
tutorial_runtime_next_stage = engine_api.tutorial_runtime_next_stage_runtime
tutorial_runtime_skip = engine_api.tutorial_runtime_skip_runtime

_VIEW_ACTIONS_4D = (
    "yaw_fine_neg",
    "yaw_neg",
    "yaw_pos",
    "yaw_fine_pos",
    "pitch_pos",
    "pitch_neg",
    "zoom_in",
    "zoom_out",
    "reset",
    "cycle_projection",
    "view_xw_neg",
    "view_xw_pos",
    "view_zw_neg",
    "view_zw_pos",
    "overlay_alpha_dec",
    "overlay_alpha_inc",
)
_TUTORIAL_MOVE_DELAY_MS = engine_api.project_constant_int(
    ("tutorial", "action_delay_ms", "movement"),
    170,
    min_value=0,
    max_value=2000,
)
_TUTORIAL_ROTATE_DELAY_MS = engine_api.project_constant_int(
    ("tutorial", "action_delay_ms", "rotation"),
    190,
    min_value=0,
    max_value=2000,
)
_TUTORIAL_DROP_DELAY_MS = engine_api.project_constant_int(
    ("tutorial", "action_delay_ms", "drop"),
    260,
    min_value=0,
    max_value=2000,
)
_TUTORIAL_SOFT_DROP_DELAY_MS = engine_api.project_constant_int(
    ("tutorial", "action_delay_ms", "soft_drop"),
    min(200, int(_TUTORIAL_DROP_DELAY_MS)),
    min_value=0,
    max_value=2000,
)
_TUTORIAL_HARD_DROP_DELAY_MS = engine_api.project_constant_int(
    ("tutorial", "action_delay_ms", "hard_drop"),
    int(_TUTORIAL_DROP_DELAY_MS),
    min_value=0,
    max_value=2000,
)
_TUTORIAL_DELAYED_ACTIONS_4D = {
    "move_x_neg",
    "move_x_pos",
    "move_y_neg",
    "move_y_pos",
    "move_z_neg",
    "move_z_pos",
    "move_w_neg",
    "move_w_pos",
    "rotate_xy_pos",
    "rotate_xy_neg",
    "rotate_xz_pos",
    "rotate_xz_neg",
    "rotate_yz_pos",
    "rotate_yz_neg",
    "rotate_xw_pos",
    "rotate_xw_neg",
    "rotate_yw_pos",
    "rotate_yw_neg",
    "rotate_zw_pos",
    "rotate_zw_neg",
    "soft_drop",
    "hard_drop",
}
_TUTORIAL_ALWAYS_LEGAL_ACTIONS_4D = {
    "menu",
    "help",
    "restart",
    "menu_back",
    "yaw_fine_neg",
    "yaw_neg",
    "yaw_pos",
    "yaw_fine_pos",
    "pitch_neg",
    "pitch_pos",
    "zoom_in",
    "zoom_out",
    "cycle_projection",
    "reset",
    "view_xw_neg",
    "view_xw_pos",
    "view_zw_neg",
    "view_zw_pos",
    "overlay_alpha_dec",
    "overlay_alpha_inc",
}
_TUTORIAL_GAMEPLAY_ACTIONS_4D = (
    "soft_drop",
    "hard_drop",
    "move_x_neg",
    "move_x_pos",
    "move_z_neg",
    "move_z_pos",
    "move_w_neg",
    "move_w_pos",
    "rotate_xy_pos",
    "rotate_xy_neg",
    "rotate_xz_pos",
    "rotate_xz_neg",
    "rotate_yz_pos",
    "rotate_yz_neg",
    "rotate_xw_pos",
    "rotate_xw_neg",
    "rotate_yw_pos",
    "rotate_yw_neg",
    "rotate_zw_pos",
    "rotate_zw_neg",
)
_TUTORIAL_GRID_OFF_STEPS_4D = frozenset({"toggle_grid"})
_TUTORIAL_GRID_HELPER_STEPS_4D = frozenset({"hyper_layer_fill", "full_clear_bonus"})
_TUTORIAL_MIN_VISIBLE_LAYER = engine_api.project_constant_int(
    ("tutorial", "min_visible_layer"),
    2,
    min_value=0,
    max_value=10,
)
_TUTORIAL_MIN_DIMS_4D = (
    engine_api.project_constant_int(
        ("tutorial", "min_board_dims", "4d", "x"),
        10,
        min_value=4,
        max_value=60,
    ),
    engine_api.project_constant_int(
        ("tutorial", "min_board_dims", "4d", "y"),
        20,
        min_value=8,
        max_value=100,
    ),
    engine_api.project_constant_int(
        ("tutorial", "min_board_dims", "4d", "z"),
        8,
        min_value=4,
        max_value=40,
    ),
    engine_api.project_constant_int(
        ("tutorial", "min_board_dims", "4d", "w"),
        8,
        min_value=3,
        max_value=20,
    ),
)


def _tutorial_required_action_legal_4d(loop: "LoopContext4D", action_id: str) -> bool:
    if action_id in _TUTORIAL_ALWAYS_LEGAL_ACTIONS_4D:
        return True
    return bool(
        engine_api.frontend_nd_can_apply_gameplay_action_with_view(
            loop.state,
            action_id,
            yaw_deg_for_view_movement=loop.view.yaw_deg,
            axis_overrides_by_action=movement_axis_overrides_for_view(
                loop.view,
                loop.cfg.dims,
            ),
            viewer_axes_by_label=viewer_axes_for_view(loop.view, loop.cfg.dims),
        )
    )


def _tutorial_has_legal_action_4d(
    loop: "LoopContext4D",
    action_ids: tuple[str, ...],
) -> bool:
    for action_id in action_ids:
        if _tutorial_required_action_legal_4d(loop, action_id):
            return True
    return False


def _maintain_tutorial_runtime_safety(loop: "LoopContext4D") -> None:
    maintain_tutorial_runtime_safety(
        loop,
        min_visible_layer=int(_TUTORIAL_MIN_VISIBLE_LAYER),
        running_tutorial_session=lambda curr_loop: running_tutorial_session(
            curr_loop,
            tutorial_is_running=engine_api.tutorial_runtime_is_running_runtime,
        ),
        completion_ready=engine_api.tutorial_runtime_completion_ready_runtime,
        transition_pending=engine_api.tutorial_runtime_transition_pending_runtime,
        redo_tutorial_stage=lambda curr_loop, session: redo_tutorial_stage(
            curr_loop,
            session,
            redo_stage=engine_api.tutorial_runtime_redo_stage_runtime,
            apply_pending_setup=_apply_pending_tutorial_setup,
        ),
        tutorial_ensure_piece_visibility=lambda curr_loop, min_visible_layer: bool(
            engine_api.tutorial_ensure_piece_visibility_nd_runtime(
                curr_loop.state,
                curr_loop.cfg,
                min_visible_layer=min_visible_layer,
            )
        ),
        tutorial_allowed_actions_blocked=lambda curr_loop, session: tutorial_allowed_actions_blocked(
            session,
            allowed_actions_runtime=engine_api.tutorial_runtime_allowed_actions_runtime,
            has_legal_action=lambda action_ids: _tutorial_has_legal_action_4d(
                curr_loop,
                action_ids,
            ),
        ),
        tutorial_required_action_blocked=lambda curr_loop, session: tutorial_required_action_blocked(
            session,
            required_action_runtime=engine_api.tutorial_runtime_required_action_runtime,
            required_action_legal=lambda action_id: _tutorial_required_action_legal_4d(
                curr_loop,
                action_id,
            ),
        ),
    )


def _apply_tutorial_camera_preset(loop: "LoopContext4D", preset: str) -> None:
    clean_preset = str(preset).strip().lower()
    if not clean_preset:
        return
    if clean_preset != "tutorial_4d_default":
        raise RuntimeError(f"Unsupported tutorial camera preset for 4D: {preset}")
    loop.view.stop_animation()
    loop.view.yaw_deg = 32.0
    loop.view.pitch_deg = -26.0
    loop.view.zoom_scale = 1.0
    loop.view.xw_deg = 0.0
    loop.view.zw_deg = 0.0
    loop.mouse_orbit.reset()


def _apply_pending_tutorial_setup(loop: "LoopContext4D") -> None:
    tutorial_session = getattr(loop, "tutorial_session", None)
    if tutorial_session is None:
        return
    payload = tutorial_runtime_consume_pending_setup(tutorial_session)
    if not isinstance(payload, dict):
        return
    step_id = str(payload.get("step_id", "")).strip().lower()
    tutorial_apply_step_setup_nd(loop.state, loop.cfg, payload)
    if step_id in _TUTORIAL_GRID_OFF_STEPS_4D:
        loop.grid_mode = GridMode.OFF
    elif step_id in _TUTORIAL_GRID_HELPER_STEPS_4D:
        loop.grid_mode = GridMode.HELPER
    setup_payload = payload.get("setup")
    if isinstance(setup_payload, dict):
        _apply_tutorial_camera_preset(
            loop,
            str(setup_payload.get("camera_preset", "")),
        )
    start_overlay = tutorial_overlay_start_from_setup(payload)
    if start_overlay is not None:
        loop.overlay_transparency = clamp_overlay_transparency(
            start_overlay,
            default=default_overlay_transparency(),
        )




@dataclass
class LoopContext4D(PanelDragMixin):
    cfg: GameConfigND
    state: GameStateND
    view: LayerView3D
    mouse_orbit: MouseOrbitState
    bot: PlayBotController
    rotation_anim: PieceRotationAnimatorND
    overlay_transparency: float
    grid_mode: GridMode = GridMode.FULL
    clear_anim: Optional[ClearAnimation4D] = None
    last_lines_cleared: int = 0
    gravity_accumulator: int = 0
    was_game_over: bool = False
    base_speed_level: int = 1
    bot_speed_level: int = 7
    tutorial_session: Any | None = None
    tutorial_action_cooldown_ms: int = 0
    helper_panel_offset: tuple[int, int] = (0, 0)
    tutorial_panel_offset: tuple[int, int] = (0, 0)
    panel_drag_target: str | None = None
    panel_drag_origin_mouse: tuple[int, int] | None = None
    panel_drag_origin_offset: tuple[int, int] | None = None

    @classmethod
    def create(
        cls,
        cfg: GameConfigND,
        *,
        bot_mode: BotMode = BotMode.OFF,
        overlay_transparency: float | None = None,
        bot_speed_level: int = 7,
        tutorial_lesson_id: str | None = None,
    ) -> "LoopContext4D":
        state = create_initial_state(cfg)
        overlay_default = default_overlay_transparency()
        tutorial_session = None
        if tutorial_lesson_id:
            tutorial_session = tutorial_runtime_create_session(
                lesson_id=tutorial_lesson_id,
                mode="4d",
            )
        return cls(
            cfg=cfg,
            state=state,
            view=LayerView3D(),
            mouse_orbit=MouseOrbitState(),
            bot=PlayBotController(mode=bot_mode),
            rotation_anim=PieceRotationAnimatorND(
                ndim=4, gravity_axis=cfg.gravity_axis
            ),
            overlay_transparency=clamp_overlay_transparency(
                overlay_transparency,
                default=overlay_default,
            ),
            last_lines_cleared=state.lines_cleared,
            was_game_over=state.game_over,
            base_speed_level=int(cfg.speed_level),
            bot_speed_level=int(bot_speed_level),
            tutorial_session=tutorial_session,
        )

    def keydown_handler(self, event: pygame.event.Event) -> str:
        tutorial_action = self._handle_tutorial_hotkey(event.key)
        if tutorial_action is not None:
            return tutorial_action
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
        return route_nd_keydown(
            event.key,
            self.state,
            yaw_deg_for_view_movement=self.view.yaw_deg,
            axis_overrides_by_action=movement_axis_overrides_for_view(
                self.view, self.cfg.dims
            ),
            viewer_axes_by_label=viewer_axes_for_view(self.view, self.cfg.dims),
            view_key_handler=lambda key: handle_view_key(
                key,
                self.view,
                on_overlay_alpha_dec=lambda: self.adjust_overlay_transparency(-1),
                on_overlay_alpha_inc=lambda: self.adjust_overlay_transparency(1),
            ),
            view_action_lookup=lambda key: match_bound_action(
                key,
                CAMERA_KEYS_4D,
                _VIEW_ACTIONS_4D,
            ),
            sfx_handler=play_sfx,
            allow_gameplay=self.bot.user_gameplay_enabled,
            action_filter=self._tutorial_action_allowed,
            action_observer=self._tutorial_observe_action,
        )

    def _handle_tutorial_hotkey(self, key: int) -> str | None:
        return handle_tutorial_hotkey(
            key=key,
            session=self.tutorial_session,
            previous_stage=tutorial_runtime_previous_stage,
            next_stage=tutorial_runtime_next_stage,
            redo_stage=engine_api.tutorial_runtime_redo_stage_runtime,
            skip_tutorial=tutorial_runtime_skip,
            restart_tutorial=tutorial_runtime_restart,
            apply_pending_setup=lambda: _apply_pending_tutorial_setup(self),
            on_restart_loop=self.on_restart,
            reset_cooldown=lambda: setattr(self, "tutorial_action_cooldown_ms", 0),
            play_sfx=play_sfx,
        )
    def _tutorial_action_allowed(self, action_id: str) -> bool:
        if self.tutorial_session is None:
            return True
        if (
            int(self.tutorial_action_cooldown_ms) > 0
            and action_id in _TUTORIAL_DELAYED_ACTIONS_4D
        ):
            return False
        return tutorial_runtime_action_allowed(self.tutorial_session, action_id)

    def _tutorial_observe_action(self, action_id: str) -> None:
        if self.tutorial_session is None:
            return
        tutorial_runtime_observe_action(self.tutorial_session, action_id)
        self.tutorial_action_cooldown_ms = tutorial_action_delay_ms(
            action_id,
            soft_drop_delay_ms=int(_TUTORIAL_SOFT_DROP_DELAY_MS),
            hard_drop_delay_ms=int(_TUTORIAL_HARD_DROP_DELAY_MS),
            rotate_delay_ms=int(_TUTORIAL_ROTATE_DELAY_MS),
            move_delay_ms=int(_TUTORIAL_MOVE_DELAY_MS),
         )

    def adjust_overlay_transparency(self, direction: int) -> None:
        self.overlay_transparency = clamp_overlay_transparency(
            self.overlay_transparency + (overlay_transparency_step() * direction),
            default=default_overlay_transparency(),
        )

    def on_restart(self) -> None:
        restart_loop_runtime_state(
            self,
            create_initial_state=create_initial_state,
            refresh_score_multiplier=self.refresh_score_multiplier,
         )

    def on_toggle_grid(self) -> None:
        self.grid_mode = cycle_grid_mode(self.grid_mode)
        self.refresh_score_multiplier()

    def refresh_score_multiplier(self) -> None:
        refresh_score_multiplier_state(
            self,
            off_mode=BotMode.OFF,
            combined_score_multiplier=combined_score_multiplier,
         )

    def _panel_rects(self) -> tuple[pygame.Rect | None, pygame.Rect | None]:
        surface = pygame.display.get_surface()
        if surface is None:
            return None, None
        helper_rect = helper_panel_rect_for_surface(
            surface_size=surface.get_size(),
            offset=self.helper_panel_offset,
            side_panel=SIDE_PANEL,
            margin=MARGIN,
        )
        return helper_rect, tutorial_panel_last_rect(4)

    def pointer_event_handler(self, event: pygame.event.Event) -> None:
        if self._handle_panel_drag_event(event):
            return
        wheel = mouse_wheel_delta(event)
        if wheel != 0:
            self.view.stop_animation()
            if wheel > 0:
                self.view.zoom_scale = min(2.6, self.view.zoom_scale * (1.08**wheel))
            else:
                self.view.zoom_scale = max(
                    0.45, self.view.zoom_scale / (1.08 ** abs(wheel))
                )
            self._tutorial_observe_action("mouse_zoom")
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
        self._tutorial_observe_action("mouse_orbit")


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
    tutorial_lesson_id: str | None = None,
) -> bool:
    if tutorial_lesson_id:
        dims = cfg.dims
        cfg.dims = (
            max(int(dims[0]), int(_TUTORIAL_MIN_DIMS_4D[0])),
            max(int(dims[1]), int(_TUTORIAL_MIN_DIMS_4D[1])),
            max(int(dims[2]), int(_TUTORIAL_MIN_DIMS_4D[2])),
            max(int(dims[3]), int(_TUTORIAL_MIN_DIMS_4D[3])),
        )
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
    loop = LoopContext4D.create(
        cfg,
        bot_mode=bot_mode,
        overlay_transparency=overlay_transparency,
        bot_speed_level=bot_speed_level,
        tutorial_lesson_id=tutorial_lesson_id,
    )
    setattr(
        loop,
        "_apply_pending_tutorial_setup",
        lambda: _apply_pending_tutorial_setup(loop),
    )
    setattr(
        loop,
        "_maintain_tutorial_safety",
        lambda: _maintain_tutorial_runtime_safety(loop),
    )
    _apply_pending_tutorial_setup(loop)
    loop.bot.configure_speed(gravity_interval_ms, bot_speed_level)
    loop.bot.configure_planner(
        ndim=4,
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

    def _tutorial_sync(lines_cleared: int) -> bool:
        return tutorial_sync(
            loop,
            lines_cleared=lines_cleared,
            grid_mode_off=GridMode.OFF,
            sync_and_advance=tutorial_runtime_sync_and_advance,
            apply_pending_setup=_apply_pending_tutorial_setup,
            tutorial_is_running=engine_api.tutorial_runtime_is_running_runtime,
        )
    return run_nd_loop(
        screen=screen,
        fonts=fonts,
        loop=loop,
        gravity_interval_from_config=gravity_interval_ms_from_config,
        pause_dimension=4,
        run_pause_menu=run_pause_menu,
        run_help_menu=lambda target, active_fonts, dim, ctx, on_escape_back=None: run_help_menu(
            target,
            active_fonts,
            dimension=dim,
            context_label=ctx,
            on_escape_back=on_escape_back,
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
            overlay_transparency=loop.overlay_transparency,
            side_panel_offset=tuple(loop.helper_panel_offset),
        ),
        play_clear_sfx=lambda: play_sfx("clear"),
        play_game_over_sfx=lambda: play_sfx("game_over"),
        event_handler=runtime_event_handler,
        tutorial_sync=_tutorial_sync,
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
        setup_caption=setup_caption_for_dimension(4),
        game_caption=game_caption_for_dimension(4),
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







