# tet4d/ui/pygame/front4d_game.py
import math
import sys
from dataclasses import dataclass
from typing import Any, Optional, Tuple

import pygame

from tet4d.ai.playbot import PlayBotController
from tet4d.ai.playbot.types import (
    BotMode,
    bot_planner_algorithm_from_index,
    bot_mode_from_index,
    bot_planner_profile_from_index,
)
from tet4d.engine.gameplay.api import runtime_assist_combined_score_multiplier
from tet4d.engine.gameplay.game_nd import GameConfigND, GameStateND
from tet4d.engine.gameplay.rotation_anim import PieceRotationAnimatorND
from tet4d.engine.runtime.menu_settings_state import (
    DEFAULT_OVERLAY_TRANSPARENCY,
    OVERLAY_TRANSPARENCY_STEP,
    clamp_overlay_transparency,
    get_display_settings,
)
from tet4d.engine.runtime.project_config import project_constant_int
from tet4d.engine.tutorial.api import (
    tutorial_apply_step_setup_nd_runtime,
    tutorial_board_dims_runtime,
    tutorial_ensure_piece_visibility_nd_runtime,
    tutorial_runtime_action_allowed_runtime,
    tutorial_runtime_allowed_actions_runtime,
    tutorial_runtime_completion_ready_runtime,
    tutorial_runtime_consume_pending_setup_runtime,
    tutorial_runtime_create_session_runtime,
    tutorial_runtime_is_running_runtime,
    tutorial_runtime_next_stage_runtime,
    tutorial_runtime_observe_action_runtime,
    tutorial_runtime_previous_stage_runtime,
    tutorial_runtime_redo_stage_runtime,
    tutorial_runtime_required_action_runtime,
    tutorial_runtime_restart_runtime,
    tutorial_runtime_skip_runtime,
    tutorial_runtime_sync_and_advance_runtime,
    tutorial_runtime_transition_pending_runtime,
)
from tet4d.engine.ui_logic.view_modes import GridMode, cycle_grid_mode
from tet4d.ui.pygame import front4d_render, frontend_nd_input, frontend_nd_setup, frontend_nd_state
from tet4d.ui.pygame.input.camera_mouse import (
    MouseOrbitState,
    apply_mouse_orbit_event,
    mouse_wheel_delta,
)
from tet4d.ui.pygame.input.key_dispatch import match_bound_action
from tet4d.ui.pygame.keybindings import CAMERA_KEYS_4D
from tet4d.ui.pygame.launch.launcher_nd_runner import run_nd_mode_launcher
from tet4d.ui.pygame.launch.launcher_play import (
    game_caption_for_dimension,
    setup_caption_for_dimension,
)
from tet4d.ui.pygame.runtime_ui.app_runtime import (
    DisplaySettings,
    capture_windowed_display_settings_from_event,
    initialize_runtime,
)
from tet4d.ui.pygame.runtime_ui.audio import play_sfx
from tet4d.ui.pygame.runtime_ui.help_menu import run_help_menu
from tet4d.ui.pygame.runtime_ui.loop_runner_nd import run_nd_loop
from tet4d.ui.pygame.runtime_ui.panel_drag import (
    PanelDragMixin,
    helper_panel_rect_for_surface,
)
from tet4d.ui.pygame.runtime_ui.pause_menu import run_pause_menu
from tet4d.ui.pygame.runtime_ui.tutorial_loop_common import (
    handle_tutorial_hotkey,
    maintain_tutorial_runtime_safety,
    redo_tutorial_stage,
    refresh_score_multiplier_state,
    restart_loop_runtime_state,
    running_tutorial_session,
    tutorial_action_delay_ms,
    tutorial_allowed_actions_blocked,
    tutorial_gated_mouse_orbit_event,
    tutorial_overlay_start_from_setup,
    tutorial_required_action_blocked,
    tutorial_sync,
)
from tet4d.ui.pygame.runtime_ui.tutorial_overlay import tutorial_panel_last_rect

GfxFonts = Any
LAYER_GAP = front4d_render.LAYER_GAP
MARGIN = front4d_render.MARGIN
SIDE_PANEL = front4d_render.SIDE_PANEL
LayerView3D = front4d_render.LayerView3D
ClearAnimation4D = front4d_render.ClearAnimation4D
draw_game_frame = front4d_render.draw_game_frame
handle_view_key = front4d_render.handle_view_key
movement_axis_overrides_for_view = front4d_render.movement_axis_overrides_for_view
viewer_axes_for_view = front4d_render.viewer_axes_for_view
spawn_clear_animation_if_needed = front4d_render.spawn_clear_animation_if_needed
build_config = frontend_nd_setup.build_config
create_initial_state = frontend_nd_state.create_initial_state
gravity_interval_ms_from_config = frontend_nd_setup.gravity_interval_ms_from_config
route_nd_keydown = frontend_nd_input.route_nd_keydown
run_menu = frontend_nd_setup.run_menu
init_fonts = frontend_nd_setup.init_fonts
combined_score_multiplier = runtime_assist_combined_score_multiplier
tutorial_runtime_create_session = tutorial_runtime_create_session_runtime
tutorial_runtime_action_allowed = tutorial_runtime_action_allowed_runtime
tutorial_runtime_observe_action = tutorial_runtime_observe_action_runtime
tutorial_runtime_sync_and_advance = tutorial_runtime_sync_and_advance_runtime
tutorial_runtime_consume_pending_setup = (
    tutorial_runtime_consume_pending_setup_runtime
)
tutorial_runtime_restart = tutorial_runtime_restart_runtime
tutorial_runtime_previous_stage = tutorial_runtime_previous_stage_runtime
tutorial_runtime_next_stage = tutorial_runtime_next_stage_runtime
tutorial_runtime_skip = tutorial_runtime_skip_runtime
tutorial_apply_step_setup_nd = tutorial_apply_step_setup_nd_runtime
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
_TUTORIAL_DELAYED_ACTIONS_4D = {
    "move_x_neg",
    "move_x_pos",
    "move_up",
    "move_down",
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
_TUTORIAL_MIN_VISIBLE_LAYER = project_constant_int(
    ("tutorial", "min_visible_layer"),
    2,
    min_value=0,
    max_value=10,
)
def _tutorial_board_dims_4d() -> tuple[int, int, int, int]:
    dims = tutorial_board_dims_runtime("4d")
    return (int(dims[0]), int(dims[1]), int(dims[2]), int(dims[3]))


def _apply_tutorial_board_profile_4d(
    cfg: GameConfigND,
    *,
    tutorial_lesson_id: str | None,
) -> None:
    if not tutorial_lesson_id:
        return
    cfg.dims = _tutorial_board_dims_4d()



def _tutorial_required_action_legal_4d(loop: "LoopContext4D", action_id: str) -> bool:
    if action_id in _TUTORIAL_ALWAYS_LEGAL_ACTIONS_4D:
        return True
    return bool(
        frontend_nd_input.can_apply_nd_gameplay_action_with_view(
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
            tutorial_is_running=tutorial_runtime_is_running_runtime,
        ),
        completion_ready=tutorial_runtime_completion_ready_runtime,
        transition_pending=tutorial_runtime_transition_pending_runtime,
        redo_tutorial_stage=lambda curr_loop, session: redo_tutorial_stage(
            curr_loop,
            session,
            redo_stage=tutorial_runtime_redo_stage_runtime,
            apply_pending_setup=_apply_pending_tutorial_setup,
        ),
        tutorial_ensure_piece_visibility=lambda curr_loop, min_visible_layer: bool(
            tutorial_ensure_piece_visibility_nd_runtime(
                curr_loop.state,
                curr_loop.cfg,
                min_visible_layer=min_visible_layer,
            )
        ),
        tutorial_allowed_actions_blocked=lambda curr_loop, session: tutorial_allowed_actions_blocked(
            session,
            allowed_actions_runtime=tutorial_runtime_allowed_actions_runtime,
            has_legal_action=lambda action_ids: _tutorial_has_legal_action_4d(
                curr_loop,
                action_ids,
            ),
        ),
        tutorial_required_action_blocked=lambda curr_loop, session: tutorial_required_action_blocked(
            session,
            required_action_runtime=tutorial_runtime_required_action_runtime,
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
            default=float(DEFAULT_OVERLAY_TRANSPARENCY),
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
        _apply_tutorial_board_profile_4d(
            cfg,
            tutorial_lesson_id=tutorial_lesson_id,
        )
        state = create_initial_state(cfg)
        overlay_default = float(DEFAULT_OVERLAY_TRANSPARENCY)
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
            redo_stage=tutorial_runtime_redo_stage_runtime,
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
        self.tutorial_action_cooldown_ms = tutorial_action_delay_ms(action_id)

    def adjust_overlay_transparency(self, direction: int) -> None:
        self.overlay_transparency = clamp_overlay_transparency(
            self.overlay_transparency + (float(OVERLAY_TRANSPARENCY_STEP) * direction),
            default=float(DEFAULT_OVERLAY_TRANSPARENCY),
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
            if not self._tutorial_action_allowed("mouse_zoom"):
                return
            current_zoom = float(self.view.zoom_scale)
            next_zoom = (
                min(2.6, current_zoom * (1.08**wheel))
                if wheel > 0
                else max(0.45, current_zoom / (1.08 ** abs(wheel)))
            )
            if next_zoom == current_zoom:
                return
            self.view.stop_animation()
            self.view.zoom_scale = next_zoom
            self._tutorial_observe_action("mouse_zoom")
            return

        yaw_deg, pitch_deg, changed = tutorial_gated_mouse_orbit_event(
            event,
            mouse_orbit=self.mouse_orbit,
            yaw_deg=self.view.yaw_deg,
            pitch_deg=self.view.pitch_deg,
            action_allowed=self._tutorial_action_allowed("mouse_orbit"),
            apply_mouse_orbit_event=apply_mouse_orbit_event,
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
    if cfg.exploration_mode:
        bot_mode = BotMode.OFF
    gravity_interval_ms = gravity_interval_ms_from_config(cfg)
    display_payload = get_display_settings()
    fullscreen = (
        bool(display_payload.get("fullscreen", False))
        if isinstance(display_payload, dict)
        else False
    )
    display_settings = DisplaySettings(
        fullscreen=fullscreen,
        windowed_size=screen.get_size(),
    )
    default_overlay = float(DEFAULT_OVERLAY_TRANSPARENCY)
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
            tutorial_is_running=tutorial_runtime_is_running_runtime,
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
        build_config=lambda settings: frontend_nd_setup.build_play_menu_config(
            settings,
            4,
        ),
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








