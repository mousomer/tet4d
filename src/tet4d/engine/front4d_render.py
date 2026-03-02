from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache
from typing import Callable, Optional

import pygame

from .frontend_nd import (
    GfxFonts,
    gravity_interval_ms_from_config,
    piece_set_4d_label,
)
from .gameplay.game_nd import GameStateND
from tet4d.ui.pygame.input.key_dispatch import dispatch_bound_action
from tet4d.ui.pygame.keybindings import CAMERA_KEYS_4D
from tet4d.ui.pygame.render.panel_utils import (
    draw_unified_game_side_panel,
)
from tet4d.ui.pygame.projection3d import (
    Cell3,
    Face,
    Point2,
    box_raw_corners,
    build_cube_faces,
    color_for_cell,
    draw_gradient_background,
    draw_projected_lattice,
    interpolate_angle_deg,
    normalize_angle_deg,
    orthographic_point,
    projection_cache_key,
    projection_helper_cache_key,
    raw_to_world,
    smoothstep01,
    transform_point,
)
from .runtime.project_config import project_constant_float, project_constant_int
from .runtime.score_analyzer import hud_analysis_lines
from tet4d.ui.pygame.render.grid_mode_render import draw_projected_grid_mode
from tet4d.ui.pygame.render.text_render_cache import render_text_cached
from .gameplay.topology import map_overlay_cells
from tet4d.ui.pygame.input.view_controls import YawPitchTurnAnimator
from .ui_logic.view_modes import GridMode, grid_mode_label


MARGIN = project_constant_int(
    ("rendering", "4d", "margin"), 16, min_value=0, max_value=400
)
LAYER_GAP = project_constant_int(
    ("rendering", "4d", "layer_gap"), 12, min_value=0, max_value=200
)
SIDE_PANEL = project_constant_int(
    ("rendering", "4d", "side_panel"), 360, min_value=180, max_value=960
)
BG_TOP = (18, 24, 50)
BG_BOTTOM = (6, 8, 20)
TEXT_COLOR = (230, 230, 230)
GRID_COLOR = (75, 90, 125)
LAYER_FRAME = (90, 105, 145)
LAYER_LABEL = (210, 220, 245)
_CLEAR_DURATION_MS_4D = project_constant_float(
    ("animation", "clear_effect_duration_ms_4d"),
    380.0,
    min_value=120.0,
    max_value=1400.0,
)

COLOR_MAP = {
    1: (0, 255, 255),
    2: (255, 255, 0),
    3: (160, 0, 240),
    4: (0, 255, 0),
    5: (255, 0, 0),
    6: (0, 0, 255),
    7: (255, 165, 0),
}
_ASSIST_OVERLAY_OPACITY_SCALE = 0.3

ActiveOverlay4D = tuple[tuple[tuple[float, float, float, float], ...], int]
VisibleLayerCell = tuple[tuple[float, float, float], int, bool, bool]
LockedLayerCells = dict[int, tuple[VisibleLayerCell, ...]]
AxisMapEntry = tuple[int, int]
AxisMap4D = tuple[AxisMapEntry, AxisMapEntry, AxisMapEntry, AxisMapEntry]
Coord4F = tuple[float, float, float, float]


@dataclass
class LayerView3D(YawPitchTurnAnimator):
    # Shared camera for each rendered 3D layer board in the active 4D basis.
    zoom_scale: float = 1.0
    xw_deg: float = 0.0
    zw_deg: float = 0.0
    hyper_animating: bool = False
    hyper_start_xw: float = 0.0
    hyper_target_xw: float = 0.0
    hyper_start_zw: float = 0.0
    hyper_target_zw: float = 0.0
    hyper_elapsed_ms: float = 0.0

    def _start_hyper_turn(
        self, *, xw_delta_deg: float = 0.0, zw_delta_deg: float = 0.0
    ) -> None:
        self.hyper_animating = True
        self.hyper_elapsed_ms = 0.0
        self.hyper_start_xw = _snap_hyper_quarter_angle(self.xw_deg)
        self.hyper_start_zw = _snap_hyper_quarter_angle(self.zw_deg)
        self.xw_deg = self.hyper_start_xw
        self.zw_deg = self.hyper_start_zw
        self.hyper_target_xw = normalize_angle_deg(self.hyper_start_xw + xw_delta_deg)
        self.hyper_target_zw = normalize_angle_deg(self.hyper_start_zw + zw_delta_deg)

    def start_xw_turn(self, delta_deg: float) -> None:
        self._start_hyper_turn(xw_delta_deg=delta_deg)

    def start_zw_turn(self, delta_deg: float) -> None:
        self._start_hyper_turn(zw_delta_deg=delta_deg)

    def is_animating(self) -> bool:
        return super().is_animating() or self.hyper_animating

    def stop_animation(self) -> None:
        super().stop_animation()
        self.hyper_animating = False
        self.hyper_elapsed_ms = 0.0

    def step_animation(self, dt_ms: float) -> None:
        super().step_animation(dt_ms)
        if not self.hyper_animating:
            return
        self.hyper_elapsed_ms += max(0.0, dt_ms)
        if self.anim_duration_ms <= 0:
            progress = 1.0
        else:
            progress = min(1.0, self.hyper_elapsed_ms / self.anim_duration_ms)
        eased = smoothstep01(progress)
        self.xw_deg = interpolate_angle_deg(
            self.hyper_start_xw, self.hyper_target_xw, eased
        )
        self.zw_deg = interpolate_angle_deg(
            self.hyper_start_zw, self.hyper_target_zw, eased
        )
        if progress >= 1.0:
            self.xw_deg = normalize_angle_deg(self.hyper_target_xw)
            self.zw_deg = normalize_angle_deg(self.hyper_target_zw)
            self.hyper_animating = False


@dataclass
class ClearAnimation4D:
    ghost_cells: tuple[tuple[tuple[int, int, int, int], tuple[int, int, int]], ...]
    elapsed_ms: float = 0.0
    duration_ms: float = _CLEAR_DURATION_MS_4D

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


def _snap_hyper_quarter_angle(angle_deg: float) -> float:
    normalized = normalize_angle_deg(angle_deg)
    return float((round(normalized / 90.0) % 4) * 90.0)


@dataclass(frozen=True)
class RenderBasis4D:
    axis_map: AxisMap4D
    dims3: Cell3
    layer_axis: int
    layer_sign: int
    layer_count: int
    xw_steps: int
    zw_steps: int

    @property
    def layer_axis_label(self) -> str:
        return "xyzw"[self.layer_axis]


def _neg_axis_map(entry: AxisMapEntry) -> AxisMapEntry:
    axis, sign = entry
    return axis, -sign


def _turn_xw_pos_once(axis_map: AxisMap4D) -> AxisMap4D:
    x_axis, y_axis, z_axis, w_axis = axis_map
    return _neg_axis_map(w_axis), y_axis, z_axis, x_axis


def _turn_zw_pos_once(axis_map: AxisMap4D) -> AxisMap4D:
    x_axis, y_axis, z_axis, w_axis = axis_map
    return x_axis, y_axis, _neg_axis_map(w_axis), z_axis


def _effective_hyper_angles(view: LayerView3D) -> tuple[float, float]:
    # Keep basis stable while hyper-turn animation is in-flight; commit on completion.
    if view.hyper_animating:
        return view.hyper_start_xw, view.hyper_start_zw
    return view.xw_deg, view.zw_deg


def _quarter_turn_steps(angle_deg: float) -> int:
    return int(round(normalize_angle_deg(angle_deg) / 90.0)) % 4


def _basis_for_view(
    view: LayerView3D, dims4: tuple[int, int, int, int]
) -> RenderBasis4D:
    xw_deg, zw_deg = _effective_hyper_angles(view)
    xw_steps = _quarter_turn_steps(xw_deg)
    zw_steps = _quarter_turn_steps(zw_deg)
    axis_map: AxisMap4D = ((0, 1), (1, 1), (2, 1), (3, 1))
    for _ in range(xw_steps):
        axis_map = _turn_xw_pos_once(axis_map)
    for _ in range(zw_steps):
        axis_map = _turn_zw_pos_once(axis_map)
    dims3: Cell3 = (
        int(dims4[axis_map[0][0]]),
        int(dims4[axis_map[1][0]]),
        int(dims4[axis_map[2][0]]),
    )
    layer_axis, layer_sign = axis_map[3]
    return RenderBasis4D(
        axis_map=axis_map,
        dims3=dims3,
        layer_axis=int(layer_axis),
        layer_sign=int(layer_sign),
        layer_count=int(dims4[layer_axis]),
        xw_steps=xw_steps,
        zw_steps=zw_steps,
    )


def _map_coord_to_layer_cell3(
    coord4: Coord4F,
    *,
    dims4: tuple[int, int, int, int],
    basis: RenderBasis4D,
) -> tuple[float, tuple[float, float, float]]:
    mapped: list[float] = []
    for axis, sign in basis.axis_map:
        value = float(coord4[axis])
        size = float(dims4[axis])
        mapped.append(value if sign > 0 else (size - 1.0 - value))
    return mapped[3], (mapped[0], mapped[1], mapped[2])


def _layer_index_if_discrete(layer_value: float) -> int | None:
    layer_idx = int(round(layer_value))
    if abs(layer_value - float(layer_idx)) > 1e-6:
        return None
    return layer_idx


def _cell3_if_discrete(
    cell3: tuple[float, float, float],
) -> tuple[int, int, int] | None:
    x, y, z = (int(round(cell3[0])), int(round(cell3[1])), int(round(cell3[2])))
    if (
        abs(cell3[0] - float(x)) > 1e-6
        or abs(cell3[1] - float(y)) > 1e-6
        or abs(cell3[2] - float(z)) > 1e-6
    ):
        return None
    return x, y, z


def _in_bounds_layer_cell(
    layer_idx: int,
    cell3: tuple[float, float, float],
    basis: RenderBasis4D,
) -> bool:
    return (
        0 <= layer_idx < basis.layer_count
        and 0.0 <= cell3[0] < basis.dims3[0]
        and 0.0 <= cell3[1] < basis.dims3[1]
        and 0.0 <= cell3[2] < basis.dims3[2]
    )


def movement_axis_overrides_for_view(
    view: LayerView3D,
    dims4: tuple[int, int, int, int],
) -> dict[str, tuple[int, int]]:
    basis = _basis_for_view(view, dims4)
    return {
        "move_w_neg": (basis.layer_axis, -basis.layer_sign),
        "move_w_pos": (basis.layer_axis, basis.layer_sign),
    }


def viewer_axes_for_view(
    view: LayerView3D,
    dims4: tuple[int, int, int, int],
) -> dict[str, tuple[int, int]]:
    basis = _basis_for_view(view, dims4)
    return {
        "x": basis.axis_map[0],
        "z": basis.axis_map[2],
        "w": basis.axis_map[3],
    }


def _transform_raw_point(
    raw: tuple[float, float, float],
    dims3: Cell3,
    view: LayerView3D,
) -> tuple[float, float, float]:
    world_xyz = raw_to_world(raw, dims3)
    return transform_point(world_xyz, view.yaw_deg, view.pitch_deg)


def _fit_zoom(
    dims3: Cell3,
    view: LayerView3D,
    rect: pygame.Rect,
) -> float:
    transformed = [
        _transform_raw_point(raw, dims3, view) for raw in box_raw_corners(dims3)
    ]
    max_abs_x = max(max(abs(point[0]) for point in transformed), 0.01)
    max_abs_y = max(max(abs(point[1]) for point in transformed), 0.01)
    fit_x = max(1.0, rect.width - 14.0) / (2.0 * max_abs_x)
    fit_y = max(1.0, rect.height - 24.0) / (2.0 * max_abs_y)
    base_zoom = min(fit_x, fit_y)
    return max(8.0, min(120.0, base_zoom))


def _basis_cache_token(basis: RenderBasis4D) -> tuple[object, ...]:
    flat_axis = tuple(value for pair in basis.axis_map for value in pair)
    return (
        *flat_axis,
        int(basis.layer_axis),
        int(basis.layer_sign),
        int(basis.layer_count),
        int(basis.xw_steps),
        int(basis.zw_steps),
    )


def _projection_extras(
    basis: RenderBasis4D,
    dims4: tuple[int, int, int, int],
    layer_index: int,
) -> tuple[object, ...]:
    return (
        int(layer_index),
        *dims4,
        *_basis_cache_token(basis),
    )


def _project_raw_point(
    raw: tuple[float, float, float],
    dims3: Cell3,
    view: LayerView3D,
    center_px: Point2,
    zoom: float,
) -> Point2:
    trans = _transform_raw_point(raw, dims3, view)
    return orthographic_point(trans, center_px, zoom)


def _draw_board_grid(
    surface: pygame.Surface,
    dims3: Cell3,
    dims4: tuple[int, int, int, int],
    layer_index: int,
    basis: RenderBasis4D,
    view: LayerView3D,
    rect: pygame.Rect,
    zoom: float,
) -> None:
    center_px = (rect.centerx, rect.centery)
    cache_key = projection_cache_key(
        prefix="4d-full",
        dims=dims3,
        center_px=center_px,
        yaw_deg=view.yaw_deg,
        pitch_deg=view.pitch_deg,
        zoom=zoom,
        extras=_projection_extras(basis, dims4, layer_index),
    )
    draw_projected_lattice(
        surface,
        dims3,
        lambda raw: _project_raw_point(raw, dims3, view, center_px, zoom),
        inner_color=(52, 64, 95),
        frame_color=GRID_COLOR,
        frame_width=2,
        cache_key=cache_key,
    )


def _build_cell_faces(
    cell: tuple[float, float, float],
    color: tuple[int, int, int],
    view: LayerView3D,
    center_px: Point2,
    dims3: Cell3,
    zoom: float,
    active: bool,
) -> list[Face]:
    return build_cube_faces(
        cell=cell,
        color=color,
        project_raw=lambda raw: _project_raw_point(raw, dims3, view, center_px, zoom),
        transform_raw=lambda raw: _transform_raw_point(raw, dims3, view),
        active=active,
    )


def _layer_cells(
    state: GameStateND,
    layer_index: int,
    locked_by_layer: LockedLayerCells,
    basis: RenderBasis4D,
    active_overlay: ActiveOverlay4D | None = None,
) -> list[VisibleLayerCell]:
    return [
        *locked_by_layer.get(layer_index, ()),
        *_layer_active_cells(state, layer_index, basis, active_overlay),
    ]


def _locked_cells_by_layer(
    state: GameStateND, basis: RenderBasis4D
) -> LockedLayerCells:
    dims4 = state.config.dims
    cells_by_layer: dict[int, list[VisibleLayerCell]] = {}
    for coord, cell_id in state.board.cells.items():
        layer_value, cell3 = _map_coord_to_layer_cell3(coord, dims4=dims4, basis=basis)
        layer_idx = _layer_index_if_discrete(layer_value)
        if layer_idx is None or not _in_bounds_layer_cell(layer_idx, cell3, basis):
            continue
        cells_by_layer.setdefault(layer_idx, []).append(
            ((cell3[0], cell3[1], cell3[2]), cell_id, False, False)
        )
    return {layer: tuple(cells) for layer, cells in cells_by_layer.items()}


def _layer_active_cells(
    state: GameStateND,
    layer_index: int,
    basis: RenderBasis4D,
    active_overlay: ActiveOverlay4D | None,
) -> list[VisibleLayerCell]:
    if active_overlay is not None:
        return _overlay_active_layer_cells(state, layer_index, active_overlay, basis)
    return _piece_active_layer_cells(state, layer_index, basis)


def _overlay_active_layer_cells(
    state: GameStateND,
    layer_index: int,
    active_overlay: ActiveOverlay4D,
    basis: RenderBasis4D,
) -> list[VisibleLayerCell]:
    dims4 = state.config.dims
    overlay_cells, overlay_color = active_overlay
    mapped_overlay = map_overlay_cells(
        state.topology_policy,
        overlay_cells,
        allow_above_gravity=False,
    )
    cells: list[VisibleLayerCell] = []
    for coord4 in mapped_overlay:
        layer_value, cell3 = _map_coord_to_layer_cell3(coord4, dims4=dims4, basis=basis)
        if abs(layer_value - layer_index) >= 0.5:
            continue
        if _in_bounds_layer_cell(layer_index, cell3, basis):
            cells.append((cell3, overlay_color, True, True))
    return cells


def _piece_active_layer_cells(
    state: GameStateND,
    layer_index: int,
    basis: RenderBasis4D,
) -> list[VisibleLayerCell]:
    if state.current_piece is None:
        return []
    dims4 = state.config.dims
    piece_id = state.current_piece.shape.color_id
    cells: list[VisibleLayerCell] = []
    for coord in state.current_piece_cells_mapped(include_above=False):
        layer_value, cell3 = _map_coord_to_layer_cell3(coord, dims4=dims4, basis=basis)
        cell_layer = _layer_index_if_discrete(layer_value)
        if cell_layer is None or cell_layer != layer_index:
            continue
        if _in_bounds_layer_cell(layer_index, cell3, basis):
            cells.append((cell3, piece_id, True, False))
    return cells


def _helper_grid_marks_by_layer(
    state: GameStateND,
    basis: RenderBasis4D,
) -> dict[int, tuple[set[int], set[int], set[int]]]:
    dims4 = state.config.dims
    marks_by_layer: dict[int, list[set[int]]] = {}
    for coord in state.current_piece_cells_mapped(include_above=False):
        layer_value, cell3 = _map_coord_to_layer_cell3(coord, dims4=dims4, basis=basis)
        layer_idx = _layer_index_if_discrete(layer_value)
        cell3_i = _cell3_if_discrete(cell3)
        if layer_idx is None or cell3_i is None:
            continue
        if not _in_bounds_layer_cell(
            layer_idx, (float(cell3_i[0]), float(cell3_i[1]), float(cell3_i[2])), basis
        ):
            continue
        x, y, z = cell3_i
        entry = marks_by_layer.setdefault(layer_idx, [set(), set(), set()])
        entry[0].add(x)
        entry[0].add(x + 1)
        entry[1].add(y)
        entry[1].add(y + 1)
        entry[2].add(z)
        entry[2].add(z + 1)
    return {
        layer: (entry[0], entry[1], entry[2]) for layer, entry in marks_by_layer.items()
    }


def _draw_layer_grid_or_shadow(
    surface: pygame.Surface,
    dims3: Cell3,
    dims4: tuple[int, int, int, int],
    layer_index: int,
    basis: RenderBasis4D,
    view: LayerView3D,
    draw_rect: pygame.Rect,
    zoom: float,
    grid_mode: GridMode,
    helper_marks: tuple[set[int], set[int], set[int]] | None = None,
) -> None:
    center_px = (draw_rect.centerx, draw_rect.centery)
    marks = helper_marks if helper_marks is not None else (set(), set(), set())
    helper_cache_key = projection_helper_cache_key(
        prefix="4d-helper",
        dims=dims3,
        center_px=center_px,
        yaw_deg=view.yaw_deg,
        pitch_deg=view.pitch_deg,
        zoom=zoom,
        marks=marks,
        extras=_projection_extras(basis, dims4, layer_index),
    )
    draw_projected_grid_mode(
        surface=surface,
        dims=dims3,
        grid_mode=grid_mode,
        draw_full_grid=lambda: _draw_board_grid(
            surface, dims3, dims4, layer_index, basis, view, draw_rect, zoom
        ),
        project_raw=lambda raw: _project_raw_point(raw, dims3, view, center_px, zoom),
        transform_raw=lambda raw: _transform_raw_point(raw, dims3, view),
        helper_marks=helper_marks,
        helper_cache_key=helper_cache_key,
        frame_color=GRID_COLOR,
        inner_color=(52, 64, 95),
        frame_width=2,
        edge_width=2,
    )


def _layer_faces(
    state: GameStateND,
    layer_index: int,
    view: LayerView3D,
    center_px: Point2,
    dims3: Cell3,
    basis: RenderBasis4D,
    zoom: float,
    locked_by_layer: LockedLayerCells,
    active_overlay: ActiveOverlay4D | None = None,
) -> tuple[list[Face], list[Face]]:
    solid_faces: list[Face] = []
    overlay_faces: list[Face] = []
    for coord3, cell_id, is_active, is_overlay in _layer_cells(
        state,
        layer_index,
        locked_by_layer,
        basis,
        active_overlay,
    ):
        cell_faces = _build_cell_faces(
            cell=coord3,
            color=color_for_cell(cell_id, COLOR_MAP),
            view=view,
            center_px=center_px,
            dims3=dims3,
            zoom=zoom,
            active=is_active,
        )
        if is_overlay:
            overlay_faces.extend(cell_faces)
        else:
            solid_faces.extend(cell_faces)
    return solid_faces, overlay_faces


def _draw_translucent_faces(
    surface: pygame.Surface,
    faces: list[Face],
    *,
    fill_alpha: int,
    outline_alpha: int,
) -> None:
    if not faces:
        return
    faces.sort(key=lambda x: x[0], reverse=True)
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    for _depth, poly, color, active in faces:
        pygame.draw.polygon(overlay, (*color, fill_alpha), poly)
        border = (
            (255, 255, 255, outline_alpha)
            if active
            else (24, 24, 34, max(24, outline_alpha - 40))
        )
        pygame.draw.polygon(overlay, border, poly, 2 if active else 1)
    surface.blit(overlay, (0, 0))


def _draw_layer_cells(
    surface: pygame.Surface,
    *,
    state: GameStateND,
    layer_index: int,
    view: LayerView3D,
    center_px: Point2,
    dims3: Cell3,
    basis: RenderBasis4D,
    zoom: float,
    locked_by_layer: LockedLayerCells,
    active_overlay: ActiveOverlay4D | None,
    overlay_transparency: float,
) -> None:
    solid_faces, overlay_faces = _layer_faces(
        state,
        layer_index,
        view,
        center_px,
        dims3,
        basis,
        zoom,
        locked_by_layer,
        active_overlay=active_overlay,
    )
    locked_faces = [face for face in solid_faces if not face[3]]
    active_faces = [face for face in solid_faces if face[3]]
    if locked_faces:
        locked_alpha = _overlay_opacity_scale(overlay_transparency)
        _draw_translucent_faces(
            surface,
            locked_faces,
            fill_alpha=int(round(255 * locked_alpha)),
            outline_alpha=max(70, int(round(255 * min(1.0, locked_alpha + 0.12)))),
        )
    active_faces.sort(key=lambda x: x[0], reverse=True)
    for _depth, poly, color, active in active_faces:
        pygame.draw.polygon(surface, color, poly)
        border_col = (255, 255, 255) if active else (24, 24, 34)
        pygame.draw.polygon(surface, border_col, poly, 2 if active else 1)
    if overlay_faces:
        _draw_translucent_faces(
            surface,
            overlay_faces,
            fill_alpha=int(round(255 * _ASSIST_OVERLAY_OPACITY_SCALE)),
            outline_alpha=max(
                70, int(round(255 * min(1.0, _ASSIST_OVERLAY_OPACITY_SCALE + 0.12)))
            ),
        )


def _overlay_opacity_scale(overlay_transparency: float) -> float:
    # Settings store transparency; renderer needs opacity.
    clamped = max(0.0, min(1.0, float(overlay_transparency)))
    return 1.0 - clamped


def _draw_layer_clear_animation(
    surface: pygame.Surface,
    clear_anim: Optional[ClearAnimation4D],
    layer_index: int,
    view: LayerView3D,
    center_px: Point2,
    dims3: Cell3,
    dims4: tuple[int, int, int, int],
    basis: RenderBasis4D,
    zoom: float,
    overlay_transparency: float = 1.0,
) -> None:
    if clear_anim is None or not clear_anim.ghost_cells:
        return

    fade = 1.0 - clear_anim.progress
    if fade <= 0.0:
        return

    ghost_faces: list[Face] = []
    for coord4, base_color in clear_anim.ghost_cells:
        layer_value, cell3 = _map_coord_to_layer_cell3(coord4, dims4=dims4, basis=basis)
        if abs(layer_value - layer_index) >= 0.5:
            continue
        if not _in_bounds_layer_cell(layer_index, cell3, basis):
            continue
        glow_color = tuple(
            min(255, int(channel * (0.62 + 0.38 * fade) + 160 * fade))
            for channel in base_color
        )
        ghost_faces.extend(
            _build_cell_faces(
                cell=cell3,
                color=glow_color,
                view=view,
                center_px=center_px,
                dims3=dims3,
                zoom=zoom,
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


def _draw_layer_board(
    surface: pygame.Surface,
    state: GameStateND,
    view: LayerView3D,
    rect: pygame.Rect,
    layer_index: int,
    basis: RenderBasis4D,
    fonts: GfxFonts,
    grid_mode: GridMode,
    locked_by_layer: LockedLayerCells,
    helper_marks: tuple[set[int], set[int], set[int]] | None = None,
    clear_anim: Optional[ClearAnimation4D] = None,
    active_overlay: ActiveOverlay4D | None = None,
    overlay_transparency: float = 0.25,
) -> None:
    pygame.draw.rect(surface, (16, 20, 40), rect, border_radius=8)
    pygame.draw.rect(surface, LAYER_FRAME, rect, 2, border_radius=8)

    label = render_text_cached(
        font=fonts.hint_font,
        text=f"{basis.layer_axis_label} = {layer_index}",
        color=LAYER_LABEL,
    )
    surface.blit(label, (rect.x + 8, rect.y + 6))

    draw_rect = pygame.Rect(rect.x + 6, rect.y + 24, rect.width - 12, rect.height - 30)
    dims4 = state.config.dims
    dims3 = basis.dims3
    zoom = _fit_zoom(dims3, view, draw_rect) * view.zoom_scale
    zoom = max(8.0, min(170.0, zoom))
    _draw_layer_grid_or_shadow(
        surface,
        dims3,
        dims4,
        layer_index,
        basis,
        view,
        draw_rect,
        zoom,
        grid_mode,
        helper_marks,
    )

    center_px = (draw_rect.centerx, draw_rect.centery)
    _draw_layer_cells(
        surface,
        state=state,
        layer_index=layer_index,
        view=view,
        center_px=center_px,
        dims3=dims3,
        basis=basis,
        zoom=zoom,
        locked_by_layer=locked_by_layer,
        active_overlay=active_overlay,
        overlay_transparency=overlay_transparency,
    )
    _draw_layer_clear_animation(
        surface,
        clear_anim,
        layer_index,
        view,
        center_px,
        dims3,
        dims4,
        basis,
        zoom,
        overlay_transparency=overlay_transparency,
    )


@lru_cache(maxsize=32)
def _layer_grid_rect_specs(
    area_x: int,
    area_y: int,
    area_w: int,
    area_h: int,
    layer_count: int,
) -> tuple[tuple[int, int, int, int], ...]:
    if layer_count <= 0:
        return tuple()
    cols = max(1, math.ceil(math.sqrt(layer_count)))
    rows = max(1, math.ceil(layer_count / cols))

    cell_w = (area_w - (cols + 1) * LAYER_GAP) // cols
    cell_h = (area_h - (rows + 1) * LAYER_GAP) // rows
    specs: list[tuple[int, int, int, int]] = []
    idx = 0
    for row in range(rows):
        for col in range(cols):
            if idx >= layer_count:
                break
            x = area_x + LAYER_GAP + col * (cell_w + LAYER_GAP)
            y = area_y + LAYER_GAP + row * (cell_h + LAYER_GAP)
            specs.append((x, y, max(80, cell_w), max(80, cell_h)))
            idx += 1
    return tuple(specs)


def _layer_grid_rects(area: pygame.Rect, layer_count: int) -> list[pygame.Rect]:
    specs = _layer_grid_rect_specs(area.x, area.y, area.width, area.height, layer_count)
    return [pygame.Rect(x, y, w, h) for x, y, w, h in specs]


def _layer_rects_by_layer(
    *,
    area: pygame.Rect,
    layer_count: int,
) -> dict[int, pygame.Rect]:
    rects = _layer_grid_rects(area, layer_count)
    return {layer_index: rect for layer_index, rect in enumerate(rects)}


def _draw_side_panel(
    surface: pygame.Surface,
    state: GameStateND,
    view: LayerView3D,
    basis: RenderBasis4D,
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
        "View: basis-mapped 3D layer boards",
        f"Board dims: {basis.dims3}",
        f"Layer axis: {basis.layer_axis_label}",
        f"Layer count: {basis.layer_count}",
        f"Piece set: {piece_set_4d_label(state.config.piece_set_id)}",
        f"Exploration: {'ON' if state.config.exploration_mode else 'OFF'}",
        f"Challenge layers: {state.config.challenge_layers}",
        f"Fall: {rows_per_sec:.2f}/s",
        f"Grid: {grid_mode_label(grid_mode)}",
        f"Yaw: {view.yaw_deg:.1f}",
        f"Pitch: {view.pitch_deg:.1f}",
        f"XW: {view.xw_deg:.1f}",
        f"ZW: {view.zw_deg:.1f}",
        f"Zoom: {view.zoom_scale:.2f}",
    ]
    draw_unified_game_side_panel(
        surface,
        panel_rect=panel_rect,
        fonts=fonts,
        title="4D Tetris",
        score=state.score,
        lines_cleared=state.lines_cleared,
        speed_level=state.config.speed_level,
        dimension=4,
        include_exploration=bool(state.config.exploration_mode),
        data_lines=extra_state_lines,
        bot_lines=bot_lines,
        analysis_lines=analysis_lines,
        game_over=state.game_over,
        min_controls_h=150,
    )


def draw_game_frame(
    screen: pygame.Surface,
    state: GameStateND,
    view: LayerView3D,
    fonts: GfxFonts,
    grid_mode: GridMode,
    bot_lines: tuple[str, ...] = (),
    clear_anim: Optional[ClearAnimation4D] = None,
    active_overlay: ActiveOverlay4D | None = None,
    overlay_transparency: float = 0.25,
) -> None:
    draw_gradient_background(screen, BG_TOP, BG_BOTTOM)
    win_w, win_h = screen.get_size()

    panel_rect = pygame.Rect(
        win_w - SIDE_PANEL - MARGIN,
        MARGIN,
        SIDE_PANEL,
        win_h - 2 * MARGIN,
    )
    layers_rect = pygame.Rect(
        MARGIN,
        MARGIN,
        win_w - SIDE_PANEL - 3 * MARGIN,
        win_h - 2 * MARGIN,
    )
    screen.fill((14, 18, 36), layers_rect)
    pygame.draw.rect(screen, (14, 18, 36), layers_rect, border_radius=10)

    basis = _basis_for_view(view, state.config.dims)
    helper_marks_by_layer = (
        _helper_grid_marks_by_layer(state, basis)
        if grid_mode == GridMode.HELPER
        else {}
    )
    locked_by_layer = _locked_cells_by_layer(state, basis)
    layer_rect_by_layer = _layer_rects_by_layer(
        area=layers_rect,
        layer_count=basis.layer_count,
    )
    for layer_index in range(basis.layer_count):
        layer_rect = layer_rect_by_layer.get(layer_index)
        if layer_rect is None:
            continue
        _draw_layer_board(
            screen,
            state,
            view,
            layer_rect,
            layer_index,
            basis,
            fonts,
            grid_mode=grid_mode,
            locked_by_layer=locked_by_layer,
            helper_marks=helper_marks_by_layer.get(layer_index),
            clear_anim=clear_anim,
            active_overlay=active_overlay,
            overlay_transparency=overlay_transparency,
        )

    _draw_side_panel(
        screen,
        state,
        view,
        basis,
        panel_rect,
        fonts,
        grid_mode=grid_mode,
        bot_lines=bot_lines,
        overlay_transparency=overlay_transparency,
    )


def _reset_view(view: LayerView3D) -> None:
    view.yaw_deg = 32.0
    view.pitch_deg = -26.0
    view.xw_deg = 0.0
    view.zw_deg = 0.0
    view.zoom_scale = 1.0
    view.stop_animation()


def handle_view_key(
    key: int,
    view: LayerView3D,
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
            CAMERA_KEYS_4D,
            {
                "yaw_fine_neg": lambda: view.start_yaw_turn(-15.0),
                "yaw_neg": lambda: view.start_yaw_turn(-90.0),
                "yaw_pos": lambda: view.start_yaw_turn(90.0),
                "yaw_fine_pos": lambda: view.start_yaw_turn(15.0),
                "pitch_pos": lambda: view.start_pitch_turn(90.0),
                "pitch_neg": lambda: view.start_pitch_turn(-90.0),
                "view_xw_neg": lambda: view.start_xw_turn(-90.0),
                "view_xw_pos": lambda: view.start_xw_turn(90.0),
                "view_zw_neg": lambda: view.start_zw_turn(-90.0),
                "view_zw_pos": lambda: view.start_zw_turn(90.0),
                "zoom_in": lambda: setattr(
                    view, "zoom_scale", min(2.6, view.zoom_scale * 1.08)
                ),
                "zoom_out": lambda: setattr(
                    view, "zoom_scale", max(0.45, view.zoom_scale / 1.08)
                ),
                "reset": lambda: _reset_view(view),
                "overlay_alpha_dec": overlay_alpha_dec_handler,
                "overlay_alpha_inc": overlay_alpha_inc_handler,
                "cycle_projection": lambda: None,
            },
        )
        is not None
    )


def handle_view_keydown(event: pygame.event.Event, view: LayerView3D) -> bool:
    return handle_view_key(event.key, view)


def _collect_cleared_ghost_cells(
    state: GameStateND,
) -> tuple[tuple[tuple[int, ...], tuple[int, int, int]], ...]:
    ghost_cells: list[tuple[tuple[int, ...], tuple[int, int, int]]] = []
    for coord, cell_id in state.board.last_cleared_cells:
        if len(coord) != 4:
            continue
        ghost_cells.append((tuple(coord), color_for_cell(cell_id, COLOR_MAP)))
    return tuple(ghost_cells)


def spawn_clear_animation_if_needed(
    state: GameStateND,
    last_lines_cleared: int,
) -> tuple[Optional[ClearAnimation4D], int]:
    if state.lines_cleared == last_lines_cleared:
        return None, last_lines_cleared

    ghost_cells = _collect_cleared_ghost_cells(state)
    if not ghost_cells:
        return None, state.lines_cleared
    return ClearAnimation4D(ghost_cells=tuple(ghost_cells)), state.lines_cleared
