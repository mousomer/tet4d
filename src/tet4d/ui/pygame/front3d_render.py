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
    ProjectedFacePrimitive,
    build_oriented_cube_faces,
    color_for_cell,
    draw_gradient_background,
    projection_cache_key,
    projection_helper_cache_key,
)
from tet4d.ui.pygame.endgame_animation import (
    EndgameAnimationState,
    EndgameRenderContext,
    transform_relics_for_animation,
    transform_shell_geometry,
)
from tet4d.ui.pygame.render.font_profiles import (
    GfxFonts,
    init_fonts as init_fonts_for_profile,
)
from tet4d.ui.pygame.render.front3d_cell_render import (
    draw_sorted_faces,
    draw_translucent_faces,
    draw_cells as draw_cells_helper,
    overlay_opacity_scale as overlay_opacity_scale_3d,
    split_faces_for_cells,
)
from tet4d.ui.pygame.render.front3d_projection_helpers import (
    ProjectionParams3D,
    build_cell_face_primitives as build_cell_face_primitives_helper,
    build_cell_faces as build_cell_faces_helper,
    depth_denominator_for_depth,
    draw_board_grid as draw_board_grid_helper,
    fit_orthographic_zoom_for_rect,
    project_raw_point as project_raw_point_helper,
    transform_raw_point as transform_raw_point_helper,
)
from tet4d.ui.pygame.render.grid_mode_render import (
    build_projected_grid_primitives,
    draw_projected_grid_mode,
    draw_projected_line_buckets,
)
from tet4d.ui.pygame.render.panel_utils import (
    draw_game_over_banner,
    draw_unified_game_side_panel,
)
from tet4d.ui.pygame.render.projected_occlusion import resolve_board_line_occlusion

from tet4d.engine.gameplay.game_nd import GameConfigND, GameStateND
from .frontend_nd_setup import gravity_interval_ms_from_config
from tet4d.engine.gameplay.pieces_nd import piece_set_label
from tet4d.engine.gameplay.topology import map_overlay_cells
from tet4d.engine.runtime.project_config import (
    project_constant_float,
    project_constant_int,
)
from tet4d.engine.runtime.score_analyzer import hud_analysis_lines
from tet4d.engine.ui_logic.view_modes import GridMode, grid_mode_label


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


def _projection_params_from_context(
    context: EndgameRenderContext,
) -> ProjectionParams3D:
    return ProjectionParams3D(
        projection_name=str(context.projection_name),
        yaw_deg=float(context.yaw_deg),
        pitch_deg=float(context.pitch_deg),
        zoom=float(context.zoom),
        cam_dist=float(context.cam_dist),
        projective_strength=float(context.projective_strength),
        projective_bias=float(context.projective_bias),
    )


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


def _build_cell_face_primitives(
    cell: Cell3,
    color: tuple[int, int, int],
    camera: Camera3D,
    center_px: Point2,
    dims: Cell3,
    active: bool,
) -> list[ProjectedFacePrimitive]:
    params = _projection_params(camera)
    return build_cell_face_primitives_helper(
        cell=cell,
        color=color,
        params=params,
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
        if (
            state.config.exploration_mode
            and state.config.explorer_topology_profile is not None
        ):
            mapped_overlay = tuple(
                tuple(float(value) for value in coord) for coord in overlay_cells
            )
        else:
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


def _active_piece_face_primitives(
    cells: list[VisibleCell3D],
    *,
    camera: Camera3D,
    center_px: Point2,
    dims: Cell3,
) -> tuple[ProjectedFacePrimitive, ...]:
    primitives: list[ProjectedFacePrimitive] = []
    for coord, cell_id, active, is_overlay in cells:
        if not active or is_overlay:
            continue
        primitives.extend(
            _build_cell_face_primitives(
                cell=coord,
                color=color_for_cell_3d(cell_id),
                camera=camera,
                center_px=center_px,
                dims=dims,
                active=True,
            )
        )
    return tuple(primitives)


def _draw_cells_with_occluding_board_lines(
    surface: pygame.Surface,
    *,
    cells: list[VisibleCell3D],
    board_rect: pygame.Rect,
    camera: Camera3D,
    dims: Cell3,
    board_lines_under_piece: tuple,
    board_lines_over_piece: tuple,
    overlay_transparency: float,
) -> None:
    locked_faces, active_faces, overlay_faces = split_faces_for_cells(
        cells,
        build_faces_fn=lambda coord, color, active: _build_cell_faces(
            cell=coord,
            color=color,
            camera=camera,
            center_px=(board_rect.centerx, board_rect.centery),
            dims=dims,
            active=active,
        ),
        color_for_cell_fn=color_for_cell_3d,
    )
    draw_projected_line_buckets(
        surface=surface,
        fragments=board_lines_under_piece,
        frame_color=GRID_COLOR,
        inner_color=(52, 64, 95),
        frame_width=2,
    )
    if locked_faces:
        locked_alpha = overlay_opacity_scale_3d(overlay_transparency)
        draw_translucent_faces(
            surface,
            locked_faces,
            fill_alpha=int(round(255 * locked_alpha)),
            outline_alpha=max(70, int(round(255 * min(1.0, locked_alpha + 0.12)))),
        )
    if active_faces:
        draw_sorted_faces(surface, active_faces)
    if overlay_faces:
        draw_translucent_faces(
            surface,
            overlay_faces,
            fill_alpha=int(round(255 * _ASSIST_OVERLAY_OPACITY_SCALE)),
            outline_alpha=max(
                70, int(round(255 * min(1.0, _ASSIST_OVERLAY_OPACITY_SCALE + 0.12)))
            ),
        )
    draw_projected_line_buckets(
        surface=surface,
        fragments=board_lines_over_piece,
        frame_color=GRID_COLOR,
        inner_color=(52, 64, 95),
        frame_width=2,
    )


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
    side_panel_offset: tuple[int, int] = (0, 0),
) -> None:
    dims = state.config.dims
    center_px = (board_rect.centerx, board_rect.centery)
    helper_marks = _helper_grid_marks_3d(state)
    params = _projection_params(camera)
    full_grid_cache_key = projection_cache_key(
        prefix="3d-full",
        dims=dims,
        center_px=center_px,
        yaw_deg=params.yaw_deg,
        pitch_deg=params.pitch_deg,
        zoom=params.zoom,
        extras=(
            params.projection_name,
            round(params.cam_dist, 3),
            round(params.projective_strength, 4),
            round(params.projective_bias, 4),
        ),
    )
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
    visible_cells = _collect_visible_cells(state, active_overlay)
    active_piece_faces = _active_piece_face_primitives(
        visible_cells,
        camera=camera,
        center_px=center_px,
        dims=dims,
    )
    if active_piece_faces and grid_mode != GridMode.SHADOW:
        board_line_primitives = build_projected_grid_primitives(
            dims=dims,
            grid_mode=grid_mode,
            project_raw=lambda raw: project_raw_point_helper(
                raw, dims, params, center_px
            ),
            transform_raw=lambda raw: transform_raw_point_helper(raw, dims, params),
            depth_denominator=lambda depth: depth_denominator_for_depth(depth, params),
            helper_marks=helper_marks,
            helper_cache_key=helper_cache_key,
            full_grid_cache_key=full_grid_cache_key,
        )
        occlusion_buckets = resolve_board_line_occlusion(
            tuple(board_line_primitives),
            active_piece_faces,
        )
        _draw_cells_with_occluding_board_lines(
            surface,
            cells=visible_cells,
            board_rect=board_rect,
            camera=camera,
            dims=dims,
            board_lines_under_piece=occlusion_buckets.segments_under_piece,
            board_lines_over_piece=occlusion_buckets.segments_over_piece,
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
        return
    draw_projected_grid_mode(
        surface=surface,
        dims=dims,
        grid_mode=grid_mode,
        draw_full_grid=lambda: _draw_board_grid(surface, dims, camera, board_rect),
        project_raw=lambda raw: project_raw_point_helper(raw, dims, params, center_px),
        transform_raw=lambda raw: transform_raw_point_helper(raw, dims, params),
        depth_denominator=lambda depth: depth_denominator_for_depth(depth, params),
        helper_marks=helper_marks,
        helper_cache_key=helper_cache_key,
        full_grid_cache_key=full_grid_cache_key,
        frame_color=GRID_COLOR,
        inner_color=(52, 64, 95),
        frame_width=2,
        edge_width=2,
    )

    _draw_cells(
        surface,
        cells=visible_cells,
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


def _draw_endgame_board_3d(
    surface: pygame.Surface,
    *,
    board_rect: pygame.Rect,
    endgame_animation: EndgameAnimationState,
) -> None:
    snapshot = endgame_animation.snapshot
    context = snapshot.render_context
    dims = snapshot.render_dims
    center_px = (board_rect.centerx, board_rect.centery)
    params = _projection_params_from_context(context)
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    drag = float(endgame_animation.tuning.burst_drag_per_second)

    for shell_fragment in endgame_animation.shell_fragments:
        transformed, alpha = transform_shell_geometry(
            shell_fragment,
            elapsed_ms=float(endgame_animation.elapsed_ms),
            drag_per_second=drag,
        )
        if alpha <= 0.0:
            continue
        start = project_raw_point_helper(transformed[0], dims, params, center_px)
        end = project_raw_point_helper(transformed[1], dims, params, center_px)
        if start is None or end is None:
            continue
        pygame.draw.line(
            overlay,
            (*GRID_COLOR, max(0, min(255, int(round(210 * alpha))))),
            start,
            end,
            2,
        )

    fragment_faces: list[tuple[float, list[Point2], tuple[int, int, int], float]] = []
    relic_transforms = transform_relics_for_animation(endgame_animation)
    for cell_relic, (position, rotation_deg, alpha) in zip(
        endgame_animation.cell_relics,
        relic_transforms,
    ):
        if alpha <= 0.0:
            continue
        faces = build_oriented_cube_faces(
            center=position,
            color=color_for_cell_3d(cell_relic.color_id),
            project_raw=lambda raw: project_raw_point_helper(
                raw,
                dims,
                params,
                center_px,
            ),
            transform_raw=lambda raw: transform_raw_point_helper(raw, dims, params),
            active=True,
            rotation_deg=rotation_deg,
        )
        fragment_faces.extend(
            (depth, polygon, color, alpha) for depth, polygon, color, _active in faces
        )

    fragment_faces.sort(key=lambda item: item[0], reverse=True)
    for _depth, polygon, color, alpha in fragment_faces:
        fill_alpha = max(0, min(255, int(round(255 * alpha))))
        outline_alpha = max(0, min(255, int(round(230 * alpha))))
        pygame.draw.polygon(overlay, (*color, fill_alpha), polygon)
        pygame.draw.polygon(overlay, (255, 255, 255, outline_alpha), polygon, 2)
    surface.blit(overlay, (0, 0))


def _draw_side_panel(
    surface: pygame.Surface,
    state: GameStateND,
    camera: Camera3D,
    panel_rect: pygame.Rect,
    fonts: GfxFonts,
    grid_mode: GridMode,
    bot_lines: tuple[str, ...] = (),
    overlay_transparency: float = 0.25,
    frozen_context: EndgameRenderContext | None = None,
) -> None:
    gravity_ms = gravity_interval_ms_from_config(state.config)
    rows_per_sec = 1000.0 / gravity_ms if gravity_ms > 0 else 0.0
    analysis_lines = hud_analysis_lines(state.last_score_analysis)
    yaw_deg = (
        float(frozen_context.yaw_deg)
        if frozen_context is not None
        else float(camera.yaw_deg)
    )
    pitch_deg = (
        float(frozen_context.pitch_deg)
        if frozen_context is not None
        else float(camera.pitch_deg)
    )
    zoom_value = (
        float(frozen_context.zoom) if frozen_context is not None else float(camera.zoom)
    )
    extra_state_lines = [
        f"Dims: {state.config.dims}",
        f"Score mod: x{state.score_multiplier:.2f}",
        f"Piece set: {piece_set_label(state.config.piece_set_id)}",
        f"Exploration: {'ON' if state.config.exploration_mode else 'OFF'}",
        f"Challenge layers: {state.config.challenge_layers}",
        f"Fall: {rows_per_sec:.2f}/s",
        f"Grid: {grid_mode_label(grid_mode)}",
        f"Yaw: {yaw_deg:.1f}",
        f"Pitch: {pitch_deg:.1f}",
        f"Zoom: {zoom_value:.1f}",
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
        meter_label="Locked-cell transparency",
        meter_value=float(overlay_transparency),
        meter_hint="Camera control",
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
    side_panel_offset: tuple[int, int] = (0, 0),
    endgame_animation: EndgameAnimationState | None = None,
) -> None:
    draw_gradient_background(screen, BG_TOP, BG_BOTTOM)
    window_w, window_h = screen.get_size()

    panel_rect = pygame.Rect(
        window_w - SIDE_PANEL - MARGIN,
        MARGIN,
        SIDE_PANEL,
        window_h - 2 * MARGIN,
    )
    panel_rect.move_ip(int(side_panel_offset[0]), int(side_panel_offset[1]))
    panel_rect.x = max(0, min(window_w - panel_rect.width, panel_rect.x))
    panel_rect.y = max(0, min(window_h - panel_rect.height, panel_rect.y))
    board_rect = pygame.Rect(
        MARGIN,
        MARGIN,
        window_w - SIDE_PANEL - 3 * MARGIN,
        window_h - 2 * MARGIN,
    )

    pygame.draw.rect(screen, (16, 20, 40), board_rect, border_radius=10)
    frozen_context = (
        endgame_animation.snapshot.render_context
        if endgame_animation is not None and endgame_animation.frozen_render_active
        else None
    )
    if endgame_animation is not None and endgame_animation.frozen_render_active:
        _draw_endgame_board_3d(
            screen,
            board_rect=board_rect,
            endgame_animation=endgame_animation,
        )
    else:
        _auto_fit_orthographic_zoom(camera, state.config.dims, board_rect)
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
    if state.game_over:
        draw_game_over_banner(
            screen,
            rect=board_rect,
            fonts=fonts,
            subtitle="Frozen board fragments dispersing in projection space",
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
        frozen_context=frozen_context,
    )


def suggested_window_size(cfg: GameConfigND) -> Tuple[int, int]:
    board_w = int(max(560, cfg.dims[0] * 68))
    board_h = int(max(620, cfg.dims[1] * 30))
    return board_w + SIDE_PANEL + 3 * MARGIN, board_h + 2 * MARGIN
