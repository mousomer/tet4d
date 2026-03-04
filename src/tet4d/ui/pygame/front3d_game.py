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
from tet4d.ui.pygame.input.key_dispatch import dispatch_bound_action, match_bound_action
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

_CAMERA_ACTIONS_3D = (
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
_TUTORIAL_DELAYED_ACTIONS_3D = {
    "move_x_neg",
    "move_x_pos",
    "move_y_neg",
    "move_y_pos",
    "move_z_neg",
    "move_z_pos",
    "rotate_xy_pos",
    "rotate_xy_neg",
    "rotate_xz_pos",
    "rotate_xz_neg",
    "rotate_yz_pos",
    "rotate_yz_neg",
    "soft_drop",
    "hard_drop",
}
_TUTORIAL_ALWAYS_LEGAL_ACTIONS_3D = {
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
    "overlay_alpha_dec",
    "overlay_alpha_inc",
}
_TUTORIAL_MOVE_DELTAS_3D = {
    "move_x_neg": (-1, 0, 0),
    "move_x_pos": (1, 0, 0),
    "move_z_neg": (0, 0, -1),
    "move_z_pos": (0, 0, 1),
}
_TUTORIAL_GAMEPLAY_ACTIONS_3D = (
    "soft_drop",
    "hard_drop",
    "move_x_neg",
    "move_x_pos",
    "move_z_neg",
    "move_z_pos",
    "rotate_xy_pos",
    "rotate_xy_neg",
    "rotate_xz_pos",
    "rotate_xz_neg",
    "rotate_yz_pos",
    "rotate_yz_neg",
)
_TUTORIAL_GRID_REQUIRED_STEPS_3D = frozenset(
    {
        "layer_fill",
        "full_clear_bonus",
    }
)
_TUTORIAL_MIN_VISIBLE_LAYER = engine_api.project_constant_int(
    ("tutorial", "min_visible_layer"),
    2,
    min_value=0,
    max_value=10,
)
_TUTORIAL_MIN_DIMS_3D = (
    engine_api.project_constant_int(
        ("tutorial", "min_board_dims", "3d", "x"),
        6,
        min_value=4,
        max_value=40,
    ),
    engine_api.project_constant_int(
        ("tutorial", "min_board_dims", "3d", "y"),
        18,
        min_value=8,
        max_value=80,
    ),
    engine_api.project_constant_int(
        ("tutorial", "min_board_dims", "3d", "z"),
        6,
        min_value=4,
        max_value=40,
    ),
)


def _tutorial_action_delay_ms_3d(action_id: str) -> int:
    if action_id in {"soft_drop", "hard_drop"}:
        return int(_TUTORIAL_DROP_DELAY_MS)
    if action_id.startswith("rotate_"):
        return int(_TUTORIAL_ROTATE_DELAY_MS)
    if action_id.startswith("move_"):
        return int(_TUTORIAL_MOVE_DELAY_MS)
    return 0


def _tutorial_required_action_legal_3d(loop: "LoopContext3D", action_id: str) -> bool:
    if action_id in _TUTORIAL_ALWAYS_LEGAL_ACTIONS_3D:
        return True
    return _tutorial_can_apply_piece_action_3d(loop, action_id)


def _tutorial_rotation_axes_3d(
    action_id: str,
    gravity_axis: int,
) -> tuple[int, int, int] | None:
    if action_id == "rotate_xy_pos":
        return (0, gravity_axis, 1)
    if action_id == "rotate_xy_neg":
        return (0, gravity_axis, -1)
    if action_id == "rotate_xz_pos":
        return (0, 2, 1)
    if action_id == "rotate_xz_neg":
        return (0, 2, -1)
    if action_id == "rotate_yz_pos":
        return (gravity_axis, 2, 1)
    if action_id == "rotate_yz_neg":
        return (gravity_axis, 2, -1)
    return None


def _tutorial_can_apply_piece_action_3d(
    loop: "LoopContext3D",
    action_id: str,
) -> bool:
    piece = loop.state.current_piece
    if piece is None or loop.state.game_over:
        return False
    if action_id == "hard_drop":
        return True
    if action_id == "soft_drop":
        delta = [0, 0, 0]
        delta[loop.cfg.gravity_axis] = 1
        return bool(loop.state._can_exist(piece.moved(tuple(delta))))
    move_delta = _TUTORIAL_MOVE_DELTAS_3D.get(action_id)
    if move_delta is not None:
        return bool(loop.state._can_exist(piece.moved(move_delta)))
    rotation_axes = _tutorial_rotation_axes_3d(action_id, loop.cfg.gravity_axis)
    if rotation_axes is not None:
        axis_a, axis_b, rotation_step = rotation_axes
        return bool(loop.state._can_exist(piece.rotated(axis_a, axis_b, rotation_step)))
    return True


def _tutorial_has_legal_action_3d(
    loop: "LoopContext3D",
    action_ids: tuple[str, ...],
) -> bool:
    for action_id in action_ids:
        if _tutorial_required_action_legal_3d(loop, action_id):
            return True
    return False


def _running_tutorial_session(loop: "LoopContext3D") -> object | None:
    session = loop.tutorial_session
    if session is None:
        return None
    if not engine_api.tutorial_runtime_is_running_runtime(session):
        return None
    return session


def _redo_tutorial_stage(loop: "LoopContext3D", session: object) -> None:
    if engine_api.tutorial_runtime_redo_stage_runtime(session):
        _apply_pending_tutorial_setup(loop)


def _restart_tutorial_session(loop: "LoopContext3D", session: object) -> None:
    if tutorial_runtime_restart(session):
        _apply_pending_tutorial_setup(loop)


def _tutorial_required_action_blocked(
    loop: "LoopContext3D",
    session: object,
) -> bool:
    required = engine_api.tutorial_runtime_required_action_runtime(session)
    if not required:
        return False
    return not _tutorial_required_action_legal_3d(loop, required)


def _tutorial_allowed_actions_blocked(
    loop: "LoopContext3D",
    session: object,
) -> bool:
    allowed_actions = engine_api.tutorial_runtime_allowed_actions_runtime(session)
    if not allowed_actions:
        return False
    return not _tutorial_has_legal_action_3d(loop, allowed_actions)


def _maintain_tutorial_runtime_safety(loop: "LoopContext3D") -> None:
    session = _running_tutorial_session(loop)
    if session is None:
        return
    if loop.state.game_over:
        _redo_tutorial_stage(loop, session)
        return
    visible = engine_api.tutorial_ensure_piece_visibility_nd_runtime(
        loop.state,
        loop.cfg,
        min_visible_layer=int(_TUTORIAL_MIN_VISIBLE_LAYER),
    )
    if not visible:
        _redo_tutorial_stage(loop, session)
        return
    if _tutorial_allowed_actions_blocked(loop, session):
        _redo_tutorial_stage(loop, session)
        return
    if _tutorial_required_action_blocked(loop, session):
        _redo_tutorial_stage(loop, session)
        return


def _apply_tutorial_camera_preset(loop: "LoopContext3D", preset: str) -> None:
    clean_preset = str(preset).strip().lower()
    if not clean_preset:
        return
    if clean_preset != "tutorial_3d_default":
        raise RuntimeError(f"Unsupported tutorial camera preset for 3D: {preset}")
    loop.camera.reset()
    loop.mouse_orbit.reset()


def _apply_pending_tutorial_setup(loop: "LoopContext3D") -> None:
    tutorial_session = getattr(loop, "tutorial_session", None)
    if tutorial_session is None:
        return
    payload = tutorial_runtime_consume_pending_setup(tutorial_session)
    if not isinstance(payload, dict):
        return
    step_id = str(payload.get("step_id", "")).strip().lower()
    tutorial_apply_step_setup_nd(loop.state, loop.cfg, payload)
    if step_id in _TUTORIAL_GRID_REQUIRED_STEPS_3D:
        loop.grid_mode = GridMode.OFF
    setup_payload = payload.get("setup")
    if isinstance(setup_payload, dict):
        _apply_tutorial_camera_preset(
            loop,
            str(setup_payload.get("camera_preset", "")),
        )


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
    action = dispatch_bound_action(
        key,
        CAMERA_KEYS_3D,
        {
            "yaw_fine_neg": lambda: camera.start_yaw_turn(-15.0),
            "yaw_neg": lambda: camera.start_yaw_turn(-90.0),
            "yaw_pos": lambda: camera.start_yaw_turn(90.0),
            "yaw_fine_pos": lambda: camera.start_yaw_turn(15.0),
            "pitch_pos": lambda: camera.start_pitch_turn(90.0),
            "pitch_neg": lambda: camera.start_pitch_turn(-90.0),
            "zoom_in": lambda: setattr(camera, "zoom", min(140.0, camera.zoom + 3.0)),
            "zoom_out": lambda: setattr(camera, "zoom", max(18.0, camera.zoom - 3.0)),
            "reset": camera.reset,
            "cycle_projection": camera.cycle_projection,
            "overlay_alpha_dec": overlay_alpha_dec_handler,
            "overlay_alpha_inc": overlay_alpha_inc_handler,
        },
    )
    return action is not None


def handle_camera_keydown(event: pygame.event.Event, camera: Camera3D) -> bool:
    return handle_camera_key(event.key, camera)


def _camera_action_for_key(key: int) -> str | None:
    return match_bound_action(key, CAMERA_KEYS_3D, _CAMERA_ACTIONS_3D)


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
    if state is None:
        return None, int(last_lines_cleared)
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
    base_speed_level: int = 1
    bot_speed_level: int = 7
    tutorial_session: Any | None = None
    tutorial_action_cooldown_ms: int = 0

    @classmethod
    def create(
        cls,
        cfg: GameConfigND,
        *,
        bot_mode: BotMode = BotMode.OFF,
        overlay_transparency: float | None = None,
        bot_speed_level: int = 7,
        tutorial_lesson_id: str | None = None,
    ) -> "LoopContext3D":
        state = create_initial_state(cfg)
        overlay_default = default_overlay_transparency()
        tutorial_session = None
        if tutorial_lesson_id:
            tutorial_session = tutorial_runtime_create_session(
                lesson_id=tutorial_lesson_id,
                mode="3d",
            )
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
            yaw_deg_for_view_movement=self.camera.yaw_deg,
            view_key_handler=lambda key: handle_camera_key(
                key,
                self.camera,
                on_overlay_alpha_dec=lambda: self.adjust_overlay_transparency(-1),
                on_overlay_alpha_inc=lambda: self.adjust_overlay_transparency(1),
            ),
            view_action_lookup=_camera_action_for_key,
            sfx_handler=play_sfx,
            allow_gameplay=self.bot.user_gameplay_enabled,
            action_filter=self._tutorial_action_allowed,
            action_observer=self._tutorial_observe_action,
        )

    def _handle_tutorial_hotkey(self, key: int) -> str | None:
        session = self.tutorial_session
        if session is None:
            return None
        stage_nav = {
            pygame.K_F5: tutorial_runtime_previous_stage,
            pygame.K_F6: tutorial_runtime_next_stage,
            pygame.K_F7: engine_api.tutorial_runtime_redo_stage_runtime,
        }
        step_action = stage_nav.get(key)
        if step_action is not None:
            if step_action(session):
                _apply_pending_tutorial_setup(self)
                self.tutorial_action_cooldown_ms = 0
                play_sfx("menu_confirm" if key == pygame.K_F7 else "menu_move")
            return "continue"
        if key == pygame.K_F8:
            tutorial_runtime_skip(session)
            play_sfx("menu_move")
            return "menu"
        if key == pygame.K_F9:
            if tutorial_runtime_restart(session):
                _apply_pending_tutorial_setup(self)
                self.tutorial_action_cooldown_ms = 0
            else:
                self.on_restart()
            play_sfx("menu_confirm")
            return "continue"
        return None

    def _tutorial_action_allowed(self, action_id: str) -> bool:
        if self.tutorial_session is None:
            return True
        if (
            int(self.tutorial_action_cooldown_ms) > 0
            and action_id in _TUTORIAL_DELAYED_ACTIONS_3D
        ):
            return False
        return tutorial_runtime_action_allowed(self.tutorial_session, action_id)

    def _tutorial_observe_action(self, action_id: str) -> None:
        if self.tutorial_session is None:
            return
        tutorial_runtime_observe_action(self.tutorial_session, action_id)
        self.tutorial_action_cooldown_ms = _tutorial_action_delay_ms_3d(action_id)

    def adjust_overlay_transparency(self, direction: int) -> None:
        self.overlay_transparency = clamp_overlay_transparency(
            self.overlay_transparency + (overlay_transparency_step() * direction),
            default=default_overlay_transparency(),
        )

    def on_restart(self) -> None:
        self.cfg.speed_level = int(self.base_speed_level)
        self.state = create_initial_state(self.cfg)
        self.gravity_accumulator = 0
        self.clear_anim = None
        self.last_lines_cleared = self.state.lines_cleared
        self.was_game_over = self.state.game_over
        self.mouse_orbit.reset()
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
    tutorial_lesson_id: str | None = None,
) -> bool:
    if tutorial_lesson_id:
        dims = cfg.dims
        cfg.dims = (
            max(int(dims[0]), int(_TUTORIAL_MIN_DIMS_3D[0])),
            max(int(dims[1]), int(_TUTORIAL_MIN_DIMS_3D[1])),
            max(int(dims[2]), int(_TUTORIAL_MIN_DIMS_3D[2])),
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
    loop = LoopContext3D.create(
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

    def _tutorial_sync(lines_cleared: int) -> bool:
        if loop.tutorial_session is None:
            return False
        progressed = tutorial_runtime_sync_and_advance(
            loop.tutorial_session,
            lines_cleared=lines_cleared,
            overlay_transparency=float(loop.overlay_transparency),
            grid_visible=bool(loop.grid_mode != GridMode.OFF),
            board_cell_count=len(loop.state.board.cells),
        )
        _apply_pending_tutorial_setup(loop)
        if not engine_api.tutorial_runtime_is_running_runtime(loop.tutorial_session):
            loop.tutorial_session = None
            loop.tutorial_action_cooldown_ms = 0
        return bool(progressed)

    return run_nd_loop(
        screen=screen,
        fonts=fonts,
        loop=loop,
        gravity_interval_from_config=gravity_interval_ms_from_config,
        pause_dimension=3,
        run_pause_menu=run_pause_menu,
        run_help_menu=lambda target, active_fonts, dim, ctx, on_escape_back=None: run_help_menu(
            target,
            active_fonts,
            dimension=dim,
            context_label=ctx,
            on_escape_back=on_escape_back,
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
        tutorial_sync=_tutorial_sync,
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
