# tetris_nd/front3d_game.py
import sys
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Tuple

import pygame

from .app_runtime import (
    initialize_runtime,
)
from .audio import play_sfx
from .assist_scoring import combined_score_multiplier
from .camera_mouse import MouseOrbitState, apply_mouse_orbit_event, mouse_wheel_delta
from .control_helper import control_groups_for_dimension
from .display import DisplaySettings
from .front3d_setup import (
    build_config,
    create_initial_state,
    gravity_interval_ms_from_config,
    run_menu,
)
from .frontend_nd import (
    route_nd_keydown,
)
from .game_nd import GameConfigND, GameStateND
from .key_dispatch import dispatch_bound_action
from .keybindings import (
    CAMERA_KEYS_3D,
)
from .pieces_nd import piece_set_label
from .playbot import (
    PlayBotController,
)
from .playbot.types import (
    BotMode,
    bot_planner_algorithm_from_index,
    bot_mode_from_index,
    bot_planner_profile_from_index,
)
from .projection3d import (
    Face,
    Cell3,
    Point2,
    build_cube_faces,
    color_for_cell,
    draw_projected_box_edges,
    draw_projected_box_shadow,
    draw_projected_helper_lattice,
    draw_gradient_background,
    draw_projected_lattice,
    fit_orthographic_zoom,
    orthographic_point,
    perspective_point,
    projective_point,
    raw_to_world,
    transform_point,
)
from .score_analyzer import hud_analysis_lines
from .loop_runner_nd import run_nd_loop
from .runtime_helpers import collect_cleared_ghost_cells
from .panel_utils import draw_game_side_panel
from .rotation_anim import PieceRotationAnimatorND
from .view_controls import YawPitchTurnAnimator
from .view_modes import GridMode, cycle_grid_mode, grid_mode_label
from .pause_menu import run_pause_menu
from .help_menu import run_help_menu
from .launcher_nd_runner import run_nd_mode_launcher


MARGIN = 20
SIDE_PANEL = 360
BG_TOP = (18, 24, 50)
BG_BOTTOM = (6, 8, 20)
TEXT_COLOR = (230, 230, 230)
GRID_COLOR = (75, 90, 125)

COLOR_MAP = {
    1: (0, 255, 255),
    2: (255, 255, 0),
    3: (160, 0, 240),
    4: (0, 255, 0),
    5: (255, 0, 0),
    6: (0, 0, 255),
    7: (255, 165, 0),
}

ActiveOverlay3D = tuple[tuple[tuple[float, float, float], ...], int]

@dataclass
class GfxFonts:
    title_font: pygame.font.Font
    menu_font: pygame.font.Font
    hint_font: pygame.font.Font
    panel_font: pygame.font.Font


def init_fonts() -> GfxFonts:
    try:
        return GfxFonts(
            title_font=pygame.font.SysFont("consolas", 36, bold=True),
            menu_font=pygame.font.SysFont("consolas", 24),
            hint_font=pygame.font.SysFont("consolas", 18),
            panel_font=pygame.font.SysFont("consolas", 17),
        )
    except (pygame.error, OSError):
        return GfxFonts(
            title_font=pygame.font.Font(None, 36),
            menu_font=pygame.font.Font(None, 24),
            hint_font=pygame.font.Font(None, 18),
            panel_font=pygame.font.Font(None, 17),
        )

class ProjectionMode3D(Enum):
    PROJECTIVE = auto()
    ORTHOGRAPHIC = auto()
    PERSPECTIVE = auto()


def projection_label(mode: ProjectionMode3D) -> str:
    if mode == ProjectionMode3D.PROJECTIVE:
        return "Projective"
    if mode == ProjectionMode3D.ORTHOGRAPHIC:
        return "Orthographic"
    return "Perspective"


@dataclass
class ClearAnimation3D:
    ghost_cells: tuple[tuple[Cell3, tuple[int, int, int]], ...]
    elapsed_ms: float = 0.0
    duration_ms: float = 360.0

    @property
    def progress(self) -> float:
        if self.duration_ms <= 0:
            return 1.0
        return max(0.0, min(1.0, self.elapsed_ms / self.duration_ms))

    @property
    def done(self) -> bool:
        return self.progress >= 1.0

    def step(self, dt_ms: float) -> None:
        self.elapsed_ms += max(0.0, dt_ms)


@dataclass
class Camera3D(YawPitchTurnAnimator):
    # Default to the same angled preset used by 4D layer views.
    projection: ProjectionMode3D = ProjectionMode3D.ORTHOGRAPHIC
    zoom: float = 52.0
    cam_dist: float = 6.5
    projective_strength: float = 0.22
    projective_bias: float = 3.0
    auto_fit_once: bool = True

    def reset(self) -> None:
        self.projection = ProjectionMode3D.ORTHOGRAPHIC
        self.yaw_deg = 32.0
        self.pitch_deg = -26.0
        self.zoom = 52.0
        self.cam_dist = 6.5
        self.auto_fit_once = True
        self.stop_animation()

    def cycle_projection(self) -> None:
        if self.projection == ProjectionMode3D.PROJECTIVE:
            self.projection = ProjectionMode3D.ORTHOGRAPHIC
            self.auto_fit_once = True
        elif self.projection == ProjectionMode3D.ORTHOGRAPHIC:
            self.projection = ProjectionMode3D.PERSPECTIVE
        else:
            self.projection = ProjectionMode3D.PROJECTIVE

    def _start_turn(self, target_yaw: float, target_pitch: float) -> None:
        super()._start_turn(target_yaw, target_pitch)
        self.auto_fit_once = True

def _transform_raw_point(raw: Cell3 | tuple[float, float, float],
                         dims: Cell3,
                         camera: Camera3D) -> tuple[float, float, float]:
    world = raw_to_world(raw, dims)
    return transform_point(world, camera.yaw_deg, camera.pitch_deg)


def _project_point(trans: tuple[float, float, float],
                   camera: Camera3D,
                   center_px: Point2) -> Point2 | None:
    if camera.projection == ProjectionMode3D.ORTHOGRAPHIC:
        return orthographic_point(trans, center_px, camera.zoom)
    if camera.projection == ProjectionMode3D.PERSPECTIVE:
        return perspective_point(trans, center_px, camera.zoom, camera.cam_dist)
    return projective_point(
        trans,
        center_px,
        camera.zoom,
        camera.projective_strength,
        camera.projective_bias,
    )


def _project_raw_point(raw: tuple[float, float, float],
                       dims: Cell3,
                       camera: Camera3D,
                       center_px: Point2) -> Point2 | None:
    trans = _transform_raw_point(raw, dims, camera)
    return _project_point(trans, camera, center_px)


def _draw_board_grid(surface: pygame.Surface,
                     dims: Cell3,
                     camera: Camera3D,
                     board_rect: pygame.Rect) -> None:
    center_px = (board_rect.centerx, board_rect.centery)
    draw_projected_lattice(
        surface,
        dims,
        lambda raw: _project_raw_point(raw, dims, camera, center_px),
        inner_color=(52, 64, 95),
        frame_color=GRID_COLOR,
        frame_width=2,
    )


def _build_cell_faces(cell: Cell3,
                      color: tuple[int, int, int],
                      camera: Camera3D,
                      center_px: Point2,
                      dims: Cell3,
                      active: bool) -> list[Face]:
    return build_cube_faces(
        cell=cell,
        color=color,
        project_raw=lambda raw: _project_raw_point(raw, dims, camera, center_px),
        transform_raw=lambda raw: _transform_raw_point(raw, dims, camera),
        active=active,
    )


def _collect_visible_cells(
    state: GameStateND,
    active_overlay: ActiveOverlay3D | None = None,
) -> list[tuple[tuple[float, float, float], int, bool]]:
    dims = state.config.dims
    cells: list[tuple[tuple[float, float, float], int, bool]] = []

    for coord, cell_id in state.board.cells.items():
        x, y, z = coord
        if 0 <= x < dims[0] and 0 <= y < dims[1] and 0 <= z < dims[2]:
            cells.append(((float(x), float(y), float(z)), cell_id, False))

    if active_overlay is not None:
        overlay_cells, overlay_color = active_overlay
        for x, y, z in overlay_cells:
            if 0.0 <= x < dims[0] and 0.0 <= y < dims[1] and 0.0 <= z < dims[2]:
                cells.append(((x, y, z), overlay_color, True))
        return cells

    if state.current_piece is None:
        return cells

    piece_id = state.current_piece.shape.color_id
    for coord in state.current_piece.cells():
        x, y, z = coord
        if 0 <= x < dims[0] and 0 <= y < dims[1] and 0 <= z < dims[2]:
            cells.append(((float(x), float(y), float(z)), piece_id, True))
    return cells


def _helper_grid_marks_3d(state: GameStateND) -> tuple[set[int], set[int], set[int]]:
    if state.current_piece is None:
        return set(), set(), set()
    dims = state.config.dims
    x_marks: set[int] = set()
    y_marks: set[int] = set()
    z_marks: set[int] = set()
    for x, y, z in state.current_piece.cells():
        if 0 <= x < dims[0] and 0 <= y < dims[1] and 0 <= z < dims[2]:
            x_marks.add(x)
            x_marks.add(x + 1)
            y_marks.add(y)
            y_marks.add(y + 1)
            z_marks.add(z)
            z_marks.add(z + 1)
    return x_marks, y_marks, z_marks


def _faces_for_cells(cells: list[tuple[tuple[float, float, float], int, bool]],
                     camera: Camera3D,
                     center_px: Point2,
                     dims: Cell3) -> list[Face]:
    faces: list[Face] = []
    for coord, cell_id, active in cells:
        faces.extend(
            _build_cell_faces(
                cell=coord,
                color=color_for_cell(cell_id, COLOR_MAP),
                camera=camera,
                center_px=center_px,
                dims=dims,
                active=active,
            )
        )
    return faces


def _draw_sorted_faces(surface: pygame.Surface, faces: list[Face]) -> None:
    faces.sort(key=lambda x: x[0], reverse=True)
    for _depth, poly, color, active in faces:
        pygame.draw.polygon(surface, color, poly)
        border = (255, 255, 255) if active else (25, 25, 35)
        pygame.draw.polygon(surface, border, poly, 2 if active else 1)


def _draw_clear_animation(surface: pygame.Surface,
                          clear_anim: Optional[ClearAnimation3D],
                          camera: Camera3D,
                          center_px: Point2,
                          dims: Cell3) -> None:
    if clear_anim is None or not clear_anim.ghost_cells:
        return

    fade = 1.0 - clear_anim.progress
    if fade <= 0.0:
        return

    ghost_faces: list[Face] = []
    for coord, base_color in clear_anim.ghost_cells:
        glow_color = tuple(
            min(255, int(channel * (0.65 + 0.35 * fade) + 160 * fade))
            for channel in base_color
        )
        ghost_faces.extend(
            _build_cell_faces(
                cell=coord,
                color=glow_color,
                camera=camera,
                center_px=center_px,
                dims=dims,
                active=True,
            )
        )

    if not ghost_faces:
        return

    ghost_faces.sort(key=lambda x: x[0], reverse=True)
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    fill_alpha = int(160 * fade)
    outline_alpha = int(220 * fade)
    for _depth, poly, color, _active in ghost_faces:
        pygame.draw.polygon(overlay, (*color, fill_alpha), poly)
        pygame.draw.polygon(overlay, (255, 255, 255, outline_alpha), poly, 2)
    surface.blit(overlay, (0, 0))


def _draw_board_3d(surface: pygame.Surface,
                   state: GameStateND,
                   camera: Camera3D,
                   board_rect: pygame.Rect,
                   grid_mode: GridMode = GridMode.FULL,
                   clear_anim: Optional[ClearAnimation3D] = None,
                   active_overlay: ActiveOverlay3D | None = None) -> None:
    dims = state.config.dims
    center_px = (board_rect.centerx, board_rect.centery)

    if grid_mode == GridMode.FULL:
        _draw_board_grid(surface, dims, camera, board_rect)
    elif grid_mode == GridMode.EDGE:
        draw_projected_box_edges(
            surface,
            dims,
            lambda raw: _project_raw_point(raw, dims, camera, center_px),
            edge_color=GRID_COLOR,
            edge_width=2,
        )
    elif grid_mode == GridMode.HELPER:
        draw_projected_box_shadow(
            surface,
            dims,
            project_raw=lambda raw: _project_raw_point(raw, dims, camera, center_px),
            transform_raw=lambda raw: _transform_raw_point(raw, dims, camera),
        )
        x_marks, y_marks, z_marks = _helper_grid_marks_3d(state)
        draw_projected_helper_lattice(
            surface,
            dims,
            lambda raw: _project_raw_point(raw, dims, camera, center_px),
            x_marks=x_marks,
            y_marks=y_marks,
            z_marks=z_marks,
            inner_color=(52, 64, 95),
            frame_color=GRID_COLOR,
            frame_width=2,
        )
    else:
        draw_projected_box_shadow(
            surface,
            dims,
            project_raw=lambda raw: _project_raw_point(raw, dims, camera, center_px),
            transform_raw=lambda raw: _transform_raw_point(raw, dims, camera),
        )

    _draw_sorted_faces(
        surface,
        _faces_for_cells(_collect_visible_cells(state, active_overlay), camera, center_px, dims),
    )
    _draw_clear_animation(surface, clear_anim, camera, center_px, dims)


def _draw_side_panel(surface: pygame.Surface,
                     state: GameStateND,
                     camera: Camera3D,
                     panel_rect: pygame.Rect,
                     fonts: GfxFonts,
                     grid_mode: GridMode,
                     bot_lines: tuple[str, ...] = ()) -> None:
    gravity_ms = gravity_interval_ms_from_config(state.config)
    rows_per_sec = 1000.0 / gravity_ms if gravity_ms > 0 else 0.0

    analysis_lines = hud_analysis_lines(state.last_score_analysis)
    low_priority_lines = [*bot_lines, *([""] if bot_lines and analysis_lines else []), *analysis_lines]
    lines = (
        "3D Tetris",
        "",
        f"Dims: {state.config.dims}",
        f"Piece set: {piece_set_label(state.config.piece_set_id)}",
        f"Projection: {projection_label(camera.projection)}",
        f"Score: {state.score}",
        f"Layers: {state.lines_cleared}",
        f"Speed: {state.config.speed_level}",
        f"Exploration: {'ON' if state.config.exploration_mode else 'OFF'}",
        f"Challenge layers: {state.config.challenge_layers}",
        f"Fall: {rows_per_sec:.2f}/s",
        f"Score mod: x{state.score_multiplier:.2f}",
        f"Grid: {grid_mode_label(grid_mode)}",
        "",
        f"Yaw: {camera.yaw_deg:.1f}",
        f"Pitch: {camera.pitch_deg:.1f}",
        f"Zoom: {camera.zoom:.1f}",
    )

    draw_game_side_panel(
        surface,
        panel_rect=panel_rect,
        fonts=fonts,
        header_lines=lines,
        control_groups=control_groups_for_dimension(3),
        low_priority_lines=tuple(low_priority_lines),
        game_over=state.game_over,
        min_controls_h=138,
    )


def _auto_fit_orthographic_zoom(camera: Camera3D,
                                dims: Tuple[int, int, int],
                                board_rect: pygame.Rect) -> None:
    """
    One-shot fit so the entire board is visible for orthographic projection
    at the current yaw/pitch.
    """
    if not camera.auto_fit_once and not camera.is_animating():
        return
    if camera.projection != ProjectionMode3D.ORTHOGRAPHIC:
        return

    camera.zoom = fit_orthographic_zoom(
        dims=dims,
        yaw_deg=camera.yaw_deg,
        pitch_deg=camera.pitch_deg,
        rect=board_rect,
        pad_x=18,
        pad_y=18,
        min_zoom=12.0,
        max_zoom=140.0,
    )
    if not camera.is_animating():
        camera.auto_fit_once = False


def draw_game_frame(screen: pygame.Surface,
                    state: GameStateND,
                    camera: Camera3D,
                    fonts: GfxFonts,
                    grid_mode: GridMode,
                    bot_lines: tuple[str, ...] = (),
                    clear_anim: Optional[ClearAnimation3D] = None,
                    active_overlay: ActiveOverlay3D | None = None) -> None:
    draw_gradient_background(screen, BG_TOP, BG_BOTTOM)
    window_w, window_h = screen.get_size()

    panel_rect = pygame.Rect(
        window_w - SIDE_PANEL - MARGIN,
        MARGIN,
        SIDE_PANEL,
        window_h - 2 * MARGIN,
    )
    board_rect = pygame.Rect(
        MARGIN,
        MARGIN,
        window_w - SIDE_PANEL - 3 * MARGIN,
        window_h - 2 * MARGIN,
    )

    _auto_fit_orthographic_zoom(camera, state.config.dims, board_rect)

    pygame.draw.rect(screen, (16, 20, 40), board_rect, border_radius=10)
    _draw_board_3d(
        screen,
        state,
        camera,
        board_rect,
        grid_mode=grid_mode,
        clear_anim=clear_anim,
        active_overlay=active_overlay,
    )
    _draw_side_panel(screen, state, camera, panel_rect, fonts, grid_mode=grid_mode, bot_lines=bot_lines)


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
                "zoom_in": lambda: setattr(camera, "zoom", min(140.0, camera.zoom + 3.0)),
                "zoom_out": lambda: setattr(camera, "zoom", max(18.0, camera.zoom - 3.0)),
                "reset": camera.reset,
                "cycle_projection": camera.cycle_projection,
            },
        )
        is not None
    )


def handle_camera_keydown(event: pygame.event.Event, camera: Camera3D) -> bool:
    return handle_camera_key(event.key, camera)


def handle_game_keydown(event: pygame.event.Event,
                        state: GameStateND,
                        camera: Camera3D | GameConfigND | None = None,
                        _cfg: GameConfigND | None = None,
                        *,
                        allow_gameplay: bool = True) -> str:
    yaw_for_movement = camera.yaw_deg if isinstance(camera, Camera3D) else 32.0
    return route_nd_keydown(
        event.key,
        state,
        yaw_deg_for_view_movement=yaw_for_movement,
        sfx_handler=play_sfx,
        allow_gameplay=allow_gameplay,
    )


def _spawn_clear_animation_if_needed(state: GameStateND,
                                     last_lines_cleared: int) -> tuple[Optional[ClearAnimation3D], int]:
    if state.lines_cleared == last_lines_cleared:
        return None, last_lines_cleared

    raw_ghost_cells = collect_cleared_ghost_cells(
        state,
        expected_coord_len=3,
        color_for_cell=lambda cell_id: color_for_cell(cell_id, COLOR_MAP),
    )
    ghost_cells = tuple(
        ((coord[0], coord[1], coord[2]), color)
        for coord, color in raw_ghost_cells
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
    def create(cls, cfg: GameConfigND, *, bot_mode: BotMode = BotMode.OFF) -> "LoopContext3D":
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
        self.state.analysis_actor_mode = "human" if self.bot.mode == BotMode.OFF else mode_name
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


def run_game_loop(screen: pygame.Surface,
                  cfg: GameConfigND,
                  fonts: GfxFonts,
                  *,
                  bot_mode: BotMode = BotMode.OFF,
                  bot_speed_level: int = 7,
                  bot_algorithm_index: int = 0,
                  bot_profile_index: int = 1,
                  bot_budget_ms: int = 24) -> bool:
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


def suggested_window_size(cfg: GameConfigND) -> Tuple[int, int]:
    board_w = int(max(560, cfg.dims[0] * 68))
    board_h = int(max(620, cfg.dims[1] * 30))
    return board_w + SIDE_PANEL + 3 * MARGIN, board_h + 2 * MARGIN


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
