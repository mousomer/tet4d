from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Tuple

import pygame

from tet4d.ui.pygame.input.view_controls import YawPitchTurnAnimator
from tet4d.ui.pygame.projection3d import (
    Cell3,
    Face,
    Point2,
    color_for_cell,
    draw_gradient_background,
    projection_helper_cache_key,
)
from tet4d.ui.pygame.render.font_profiles import (
    GfxFonts,
    init_fonts as init_fonts_for_profile,
)
from tet4d.ui.pygame.render.front3d_cell_render import (
    draw_cells as draw_cells_helper,
    draw_sorted_faces as draw_sorted_faces_helper,
    draw_translucent_faces as draw_translucent_faces_helper,
    overlay_opacity_scale as overlay_opacity_scale_helper,
    split_faces_for_cells as split_faces_for_cells_helper,
)
from tet4d.ui.pygame.render.front3d_projection_helpers import (
    ProjectionParams3D,
    build_cell_faces as build_cell_faces_helper,
    draw_board_grid as draw_board_grid_helper,
    fit_orthographic_zoom_for_rect,
    project_point as project_point_helper,
    project_raw_point as project_raw_point_helper,
    transform_raw_point as transform_raw_point_helper,
)
from tet4d.ui.pygame.render.grid_mode_render import draw_projected_grid_mode
from tet4d.ui.pygame.render.panel_utils import (
    draw_unified_game_side_panel,
)

from .gameplay.game_nd import GameConfigND, GameStateND
from .frontend_nd import gravity_interval_ms_from_config
from .gameplay.pieces_nd import piece_set_label
from .gameplay.topology import map_overlay_cells
from .runtime.project_config import project_constant_float, project_constant_int
from .runtime.score_analyzer import hud_analysis_lines
from .ui_logic.view_modes import GridMode, grid_mode_label


MARGIN = project_constant_int(
    ("rendering", "3d", "margin"), 20, min_value=0, max_value=400
)
SIDE_PANEL = project_constant_int(
    ("rendering", "3d", "side_panel"), 360, min_value=180, max_value=960
)
BG_TOP = (18, 24, 50)
BG_BOTTOM = (6, 8, 20)
TEXT_COLOR = (230, 230, 230)
GRID_COLOR = (75, 90, 125)
_CLEAR_DURATION_MS_3D = project_constant_float(
    ("animation", "clear_effect_duration_ms_3d"),
    360.0,
    min_value=120.0,
    max_value=1200.0,
)

COLOR_MAP_3D = {
    1: (0, 255, 255),
    2: (255, 255, 0),
    3: (160, 0, 240),
    4: (0, 255, 0),
    5: (255, 0, 0),
    6: (0, 0, 255),
    7: (255, 165, 0),
}
_ASSIST_OVERLAY_OPACITY_SCALE = 0.3

ActiveOverlay3D = tuple[tuple[tuple[float, float, float], ...], int]
VisibleCell3D = tuple[tuple[float, float, float], int, bool, bool]


def init_fonts() -> GfxFonts:
    return init_fonts_for_profile("nd")


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
    duration_ms: float = _CLEAR_DURATION_MS_3D

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


def color_for_cell_3d(cell_id: int) -> tuple[int, int, int]:
    return color_for_cell(cell_id, COLOR_MAP_3D)


def _projection_params(camera: Camera3D) -> ProjectionParams3D:
    return ProjectionParams3D(
        projection_name=camera.projection.name,
        yaw_deg=camera.yaw_deg,
        pitch_deg=camera.pitch_deg,
        zoom=camera.zoom,
        cam_dist=camera.cam_dist,
        projective_strength=camera.projective_strength,
        projective_bias=camera.projective_bias,
    )


def _transform_raw_point(
    raw: Cell3 | tuple[float, float, float],
    dims: Cell3,
    camera: Camera3D,
) -> tuple[float, float, float]:
    return transform_raw_point_helper(raw, dims, _projection_params(camera))


def _project_point(
    trans: tuple[float, float, float],
    camera: Camera3D,
    center_px: Point2,
) -> Point2 | None:
    return project_point_helper(trans, _projection_params(camera), center_px)


def _project_raw_point(
    raw: tuple[float, float, float],
    dims: Cell3,
    camera: Camera3D,
    center_px: Point2,
) -> Point2 | None:
    return project_raw_point_helper(raw, dims, _projection_params(camera), center_px)


def _draw_board_grid(
    surface: pygame.Surface,
    dims: Cell3,
    camera: Camera3D,
    board_rect: pygame.Rect,
) -> None:
    draw_board_grid_helper(
        surface,
        dims,
        _projection_params(camera),
        board_rect,
        inner_color=(52, 64, 95),
        frame_color=GRID_COLOR,
        frame_width=2,
    )


def _build_cell_faces(
    cell: Cell3,
    color: tuple[int, int, int],
    camera: Camera3D,
    center_px: Point2,
    dims: Cell3,
    active: bool,
) -> list[Face]:
    return build_cell_faces_helper(
        cell=cell,
        color=color,
        params=_projection_params(camera),
        center_px=center_px,
        dims=dims,
        active=active,
    )


def _collect_visible_cells(
    state: GameStateND,
    active_overlay: ActiveOverlay3D | None = None,
) -> list[VisibleCell3D]:
    dims = state.config.dims
    cells: list[VisibleCell3D] = []

    for coord, cell_id in state.board.cells.items():
        x, y, z = coord
        if 0 <= x < dims[0] and 0 <= y < dims[1] and 0 <= z < dims[2]:
            cells.append(((float(x), float(y), float(z)), cell_id, False, False))

    if active_overlay is not None:
        overlay_cells, overlay_color = active_overlay
        mapped_overlay = map_overlay_cells(
            state.topology_policy,
            overlay_cells,
            allow_above_gravity=False,
        )
        for x, y, z in mapped_overlay:
            if 0.0 <= x < dims[0] and 0.0 <= y < dims[1] and 0.0 <= z < dims[2]:
                cells.append(((x, y, z), overlay_color, True, True))
        return cells

    if state.current_piece is None:
        return cells

    piece_id = state.current_piece.shape.color_id
    for coord in state.current_piece_cells_mapped(include_above=False):
        x, y, z = coord
        if 0 <= x < dims[0] and 0 <= y < dims[1] and 0 <= z < dims[2]:
            cells.append(((float(x), float(y), float(z)), piece_id, True, False))
    return cells


def _helper_grid_marks_3d(state: GameStateND) -> tuple[set[int], set[int], set[int]]:
    dims = state.config.dims
    x_marks: set[int] = set()
    y_marks: set[int] = set()
    z_marks: set[int] = set()
    for x, y, z in state.current_piece_cells_mapped(include_above=False):
        if 0 <= x < dims[0] and 0 <= y < dims[1] and 0 <= z < dims[2]:
            x_marks.add(x)
            x_marks.add(x + 1)
            y_marks.add(y)
            y_marks.add(y + 1)
            z_marks.add(z)
            z_marks.add(z + 1)
    return x_marks, y_marks, z_marks


def _split_faces_for_cells(
    cells: list[VisibleCell3D],
    camera: Camera3D,
    center_px: Point2,
    dims: Cell3,
) -> tuple[list[Face], list[Face], list[Face]]:
    return split_faces_for_cells_helper(
        cells,
        build_faces_fn=lambda coord, color, active: _build_cell_faces(
            cell=coord,
            color=color,
            camera=camera,
            center_px=center_px,
            dims=dims,
            active=active,
        ),
        color_for_cell_fn=color_for_cell_3d,
    )


def _draw_sorted_faces(surface: pygame.Surface, faces: list[Face]) -> None:
    draw_sorted_faces_helper(surface, faces)


def _draw_translucent_faces(
    surface: pygame.Surface,
    faces: list[Face],
    *,
    fill_alpha: int,
    outline_alpha: int,
) -> None:
    draw_translucent_faces_helper(
        surface,
        faces,
        fill_alpha=fill_alpha,
        outline_alpha=outline_alpha,
    )


def _draw_cells(
    surface: pygame.Surface,
    *,
    cells: list[VisibleCell3D],
    camera: Camera3D,
    center_px: Point2,
    dims: Cell3,
    overlay_transparency: float,
) -> None:
    draw_cells_helper(
        surface,
        cells=cells,
        build_faces_fn=lambda coord, color, active: _build_cell_faces(
            cell=coord,
            color=color,
            camera=camera,
            center_px=center_px,
            dims=dims,
            active=active,
        ),
        color_for_cell_fn=color_for_cell_3d,
        overlay_transparency=overlay_transparency,
        assist_overlay_opacity_scale=_ASSIST_OVERLAY_OPACITY_SCALE,
    )


def _overlay_opacity_scale(overlay_transparency: float) -> float:
    return overlay_opacity_scale_helper(overlay_transparency)


def _draw_clear_animation(
    surface: pygame.Surface,
    clear_anim: Optional[ClearAnimation3D],
    camera: Camera3D,
    center_px: Point2,
    dims: Cell3,
    overlay_transparency: float = 1.0,
) -> None:
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
    alpha_scale = _ASSIST_OVERLAY_OPACITY_SCALE
    fill_alpha = int(160 * fade * alpha_scale)
    outline_alpha = int(220 * fade * alpha_scale)
    for _depth, poly, color, _active in ghost_faces:
        pygame.draw.polygon(overlay, (*color, fill_alpha), poly)
        pygame.draw.polygon(overlay, (255, 255, 255, outline_alpha), poly, 2)
    surface.blit(overlay, (0, 0))


def _draw_board_3d(
    surface: pygame.Surface,
    state: GameStateND,
    camera: Camera3D,
    board_rect: pygame.Rect,
    grid_mode: GridMode = GridMode.FULL,
    clear_anim: Optional[ClearAnimation3D] = None,
    active_overlay: ActiveOverlay3D | None = None,
    overlay_transparency: float = 0.25,
) -> None:
    dims = state.config.dims
    center_px = (board_rect.centerx, board_rect.centery)
    helper_marks = _helper_grid_marks_3d(state)
    params = _projection_params(camera)
    helper_cache_key = projection_helper_cache_key(
        prefix="3d-helper",
        dims=dims,
        center_px=center_px,
        yaw_deg=params.yaw_deg,
        pitch_deg=params.pitch_deg,
        zoom=params.zoom,
        marks=helper_marks,
        extras=(
            params.projection_name,
            round(params.cam_dist, 3),
            round(params.projective_strength, 4),
            round(params.projective_bias, 4),
        ),
    )
    draw_projected_grid_mode(
        surface=surface,
        dims=dims,
        grid_mode=grid_mode,
        draw_full_grid=lambda: _draw_board_grid(surface, dims, camera, board_rect),
        project_raw=lambda raw: project_raw_point_helper(raw, dims, params, center_px),
        transform_raw=lambda raw: transform_raw_point_helper(raw, dims, params),
        helper_marks=helper_marks,
        helper_cache_key=helper_cache_key,
        frame_color=GRID_COLOR,
        inner_color=(52, 64, 95),
        frame_width=2,
        edge_width=2,
    )

    _draw_cells(
        surface,
        cells=_collect_visible_cells(state, active_overlay),
        camera=camera,
        center_px=center_px,
        dims=dims,
        overlay_transparency=overlay_transparency,
    )
    _draw_clear_animation(
        surface,
        clear_anim,
        camera,
        center_px,
        dims,
        overlay_transparency=overlay_transparency,
    )


def _draw_side_panel(
    surface: pygame.Surface,
    state: GameStateND,
    camera: Camera3D,
    panel_rect: pygame.Rect,
    fonts: GfxFonts,
    grid_mode: GridMode,
    bot_lines: tuple[str, ...] = (),
    overlay_transparency: float = 0.25,
) -> None:
    gravity_ms = gravity_interval_ms_from_config(state.config)
    rows_per_sec = 1000.0 / gravity_ms if gravity_ms > 0 else 0.0
    analysis_lines = hud_analysis_lines(state.last_score_analysis)
    extra_state_lines = [
        f"Dims: {state.config.dims}",
        f"Score mod: x{state.score_multiplier:.2f}",
        f"Piece set: {piece_set_label(state.config.piece_set_id)}",
        f"Exploration: {'ON' if state.config.exploration_mode else 'OFF'}",
        f"Challenge layers: {state.config.challenge_layers}",
        f"Fall: {rows_per_sec:.2f}/s",
        f"Grid: {grid_mode_label(grid_mode)}",
        f"Yaw: {camera.yaw_deg:.1f}",
        f"Pitch: {camera.pitch_deg:.1f}",
        f"Zoom: {camera.zoom:.1f}",
    ]
    draw_unified_game_side_panel(
        surface,
        panel_rect=panel_rect,
        fonts=fonts,
        title="3D Tetris",
        score=state.score,
        lines_cleared=state.lines_cleared,
        speed_level=state.config.speed_level,
        dimension=3,
        include_exploration=bool(state.config.exploration_mode),
        data_lines=extra_state_lines,
        bot_lines=bot_lines,
        analysis_lines=analysis_lines,
        game_over=state.game_over,
        min_controls_h=138,
    )


def _auto_fit_orthographic_zoom(
    camera: Camera3D,
    dims: Tuple[int, int, int],
    board_rect: pygame.Rect,
) -> None:
    """
    One-shot fit so the entire board is visible for orthographic projection
    at the current yaw/pitch.
    """
    if not camera.auto_fit_once and not camera.is_animating():
        return
    if camera.projection != ProjectionMode3D.ORTHOGRAPHIC:
        return

    camera.zoom = fit_orthographic_zoom_for_rect(
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


def draw_game_frame(
    screen: pygame.Surface,
    state: GameStateND,
    camera: Camera3D,
    fonts: GfxFonts,
    grid_mode: GridMode,
    bot_lines: tuple[str, ...] = (),
    clear_anim: Optional[ClearAnimation3D] = None,
    active_overlay: ActiveOverlay3D | None = None,
    overlay_transparency: float = 0.25,
) -> None:
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
        overlay_transparency=overlay_transparency,
    )
    _draw_side_panel(
        screen,
        state,
        camera,
        panel_rect,
        fonts,
        grid_mode=grid_mode,
        bot_lines=bot_lines,
        overlay_transparency=overlay_transparency,
    )


def suggested_window_size(cfg: GameConfigND) -> Tuple[int, int]:
    board_w = int(max(560, cfg.dims[0] * 68))
    board_h = int(max(620, cfg.dims[1] * 30))
    return board_w + SIDE_PANEL + 3 * MARGIN, board_h + 2 * MARGIN
