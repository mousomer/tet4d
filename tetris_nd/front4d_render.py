from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

import pygame

from .control_helper import control_groups_for_dimension
from .frontend_nd import (
    GfxFonts,
    SliceState,
    gravity_interval_ms_from_config,
    piece_set_4d_label,
)
from .game_nd import GameStateND
from .key_dispatch import dispatch_bound_action
from .keybindings import CAMERA_KEYS_4D
from .panel_utils import draw_game_side_panel
from .projection3d import (
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
from .project_config import project_constant_float, project_constant_int
from .runtime_helpers import collect_cleared_ghost_cells
from .score_analyzer import hud_analysis_lines
from .grid_mode_render import draw_projected_grid_mode
from .text_render_cache import render_text_cached
from .topology import map_overlay_cells
from .view_controls import YawPitchTurnAnimator
from .view_modes import GridMode, grid_mode_label


MARGIN = project_constant_int(("rendering", "4d", "margin"), 16, min_value=0, max_value=400)
LAYER_GAP = project_constant_int(("rendering", "4d", "layer_gap"), 12, min_value=0, max_value=200)
SIDE_PANEL = project_constant_int(("rendering", "4d", "side_panel"), 360, min_value=180, max_value=960)
BG_TOP = (18, 24, 50)
BG_BOTTOM = (6, 8, 20)
TEXT_COLOR = (230, 230, 230)
GRID_COLOR = (75, 90, 125)
LAYER_FRAME = (90, 105, 145)
LAYER_ACTIVE = (255, 220, 110)
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

ActiveOverlay4D = tuple[tuple[tuple[float, float, float, float], ...], int]
LockedLayerCells = dict[int, tuple[tuple[tuple[float, float, float], int, bool], ...]]


@dataclass
class LayerView3D(YawPitchTurnAnimator):
    # Fixed camera for every w-layer board.
    zoom_scale: float = 1.0
    xw_deg: float = 0.0
    zw_deg: float = 0.0
    hyper_animating: bool = False
    hyper_start_xw: float = 0.0
    hyper_target_xw: float = 0.0
    hyper_start_zw: float = 0.0
    hyper_target_zw: float = 0.0
    hyper_elapsed_ms: float = 0.0

    def _start_hyper_turn(self, *, xw_delta_deg: float = 0.0, zw_delta_deg: float = 0.0) -> None:
        self.hyper_animating = True
        self.hyper_elapsed_ms = 0.0
        self.hyper_start_xw = normalize_angle_deg(self.xw_deg)
        self.hyper_start_zw = normalize_angle_deg(self.zw_deg)
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
        self.xw_deg = interpolate_angle_deg(self.hyper_start_xw, self.hyper_target_xw, eased)
        self.zw_deg = interpolate_angle_deg(self.hyper_start_zw, self.hyper_target_zw, eased)
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


def _world_w_for_layer(w_layer: int, dims4: tuple[int, int, int, int]) -> float:
    return float(w_layer) - (float(dims4[3]) - 1.0) * 0.5


def _apply_hyper_view_turns(
    *,
    world_xyz: tuple[float, float, float],
    world_w: float,
    view: LayerView3D,
) -> tuple[float, float, float]:
    x, y, z = world_xyz
    w = world_w

    if abs(view.xw_deg) > 1e-6:
        theta_xw = math.radians(view.xw_deg)
        cos_t = math.cos(theta_xw)
        sin_t = math.sin(theta_xw)
        x, w = (x * cos_t - w * sin_t), (x * sin_t + w * cos_t)

    if abs(view.zw_deg) > 1e-6:
        theta_zw = math.radians(view.zw_deg)
        cos_t = math.cos(theta_zw)
        sin_t = math.sin(theta_zw)
        z, w = (z * cos_t - w * sin_t), (z * sin_t + w * cos_t)

    return x, y, z


def _transform_raw_point(
    raw: tuple[float, float, float],
    dims3: Cell3,
    dims4: tuple[int, int, int, int],
    w_layer: int,
    view: LayerView3D,
) -> tuple[float, float, float]:
    world_xyz = raw_to_world(raw, dims3)
    world_w = _world_w_for_layer(w_layer, dims4)
    hyper_xyz = _apply_hyper_view_turns(world_xyz=world_xyz, world_w=world_w, view=view)
    return transform_point(hyper_xyz, view.yaw_deg, view.pitch_deg)


def _fit_zoom(
    dims3: Cell3,
    dims4: tuple[int, int, int, int],
    w_layer: int,
    view: LayerView3D,
    rect: pygame.Rect,
) -> float:
    transformed = [
        _transform_raw_point(raw, dims3, dims4, w_layer, view)
        for raw in box_raw_corners(dims3)
    ]
    max_abs_x = max(max(abs(point[0]) for point in transformed), 0.01)
    max_abs_y = max(max(abs(point[1]) for point in transformed), 0.01)
    fit_x = max(1.0, rect.width - 14.0) / (2.0 * max_abs_x)
    fit_y = max(1.0, rect.height - 24.0) / (2.0 * max_abs_y)
    base_zoom = min(fit_x, fit_y)
    return max(8.0, min(120.0, base_zoom))


def _projection_extras(
    view: LayerView3D,
    dims4: tuple[int, int, int, int],
    w_layer: int,
) -> tuple[object, ...]:
    return (
        round(view.xw_deg, 3),
        round(view.zw_deg, 3),
        int(w_layer),
        int(dims4[3]),
    )


def _project_raw_point(
    raw: tuple[float, float, float],
    dims3: Cell3,
    dims4: tuple[int, int, int, int],
    w_layer: int,
    view: LayerView3D,
    center_px: Point2,
    zoom: float,
) -> Point2:
    trans = _transform_raw_point(raw, dims3, dims4, w_layer, view)
    return orthographic_point(trans, center_px, zoom)


def _draw_board_grid(
    surface: pygame.Surface,
    dims3: Cell3,
    dims4: tuple[int, int, int, int],
    w_layer: int,
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
        extras=_projection_extras(view, dims4, w_layer),
    )
    draw_projected_lattice(
        surface,
        dims3,
        lambda raw: _project_raw_point(raw, dims3, dims4, w_layer, view, center_px, zoom),
        inner_color=(52, 64, 95),
        frame_color=GRID_COLOR,
        frame_width=2,
        cache_key=cache_key,
    )


def _build_cell_faces(
    cell: Cell3,
    color: tuple[int, int, int],
    view: LayerView3D,
    center_px: Point2,
    dims3: Cell3,
    dims4: tuple[int, int, int, int],
    w_layer: int,
    zoom: float,
    active: bool,
) -> list[Face]:
    return build_cube_faces(
        cell=cell,
        color=color,
        project_raw=lambda raw: _project_raw_point(raw, dims3, dims4, w_layer, view, center_px, zoom),
        transform_raw=lambda raw: _transform_raw_point(raw, dims3, dims4, w_layer, view),
        active=active,
    )


def _layer_cells(
    state: GameStateND,
    w_layer: int,
    locked_by_layer: LockedLayerCells,
    active_overlay: ActiveOverlay4D | None = None,
) -> list[tuple[tuple[float, float, float], int, bool]]:
    return [*locked_by_layer.get(w_layer, ()), *_layer_active_cells(state, w_layer, active_overlay)]


def _locked_cells_by_layer(state: GameStateND) -> LockedLayerCells:
    dims = state.config.dims
    cells_by_layer: dict[int, list[tuple[tuple[float, float, float], int, bool]]] = {}
    for coord, cell_id in state.board.cells.items():
        x, y, z, w = coord
        if 0 <= x < dims[0] and 0 <= y < dims[1] and 0 <= z < dims[2]:
            cells_by_layer.setdefault(w, []).append(((float(x), float(y), float(z)), cell_id, False))
    return {layer: tuple(cells) for layer, cells in cells_by_layer.items()}


def _layer_active_cells(
    state: GameStateND,
    w_layer: int,
    active_overlay: ActiveOverlay4D | None,
) -> list[tuple[tuple[float, float, float], int, bool]]:
    if active_overlay is not None:
        return _overlay_active_layer_cells(state, w_layer, active_overlay)
    return _piece_active_layer_cells(state, w_layer)


def _overlay_active_layer_cells(
    state: GameStateND,
    w_layer: int,
    active_overlay: ActiveOverlay4D,
) -> list[tuple[tuple[float, float, float], int, bool]]:
    dims = state.config.dims
    overlay_cells, overlay_color = active_overlay
    mapped_overlay = map_overlay_cells(
        state.topology_policy,
        overlay_cells,
        allow_above_gravity=False,
    )
    cells: list[tuple[tuple[float, float, float], int, bool]] = []
    for x, y, z, w in mapped_overlay:
        if abs(w - w_layer) >= 0.5:
            continue
        if 0.0 <= x < dims[0] and 0.0 <= y < dims[1] and 0.0 <= z < dims[2]:
            cells.append(((x, y, z), overlay_color, True))
    return cells


def _piece_active_layer_cells(state: GameStateND, w_layer: int) -> list[tuple[tuple[float, float, float], int, bool]]:
    if state.current_piece is None:
        return []
    dims = state.config.dims
    piece_id = state.current_piece.shape.color_id
    cells: list[tuple[tuple[float, float, float], int, bool]] = []
    for coord in state.current_piece_cells_mapped(include_above=False):
        x, y, z, w = coord
        if w != w_layer:
            continue
        if 0 <= x < dims[0] and 0 <= y < dims[1] and 0 <= z < dims[2]:
            cells.append(((float(x), float(y), float(z)), piece_id, True))
    return cells


def _helper_grid_marks_by_layer(state: GameStateND) -> dict[int, tuple[set[int], set[int], set[int]]]:
    dims = state.config.dims
    marks_by_layer: dict[int, list[set[int]]] = {}
    for x, y, z, w in state.current_piece_cells_mapped(include_above=False):
        if not (0 <= x < dims[0] and 0 <= y < dims[1] and 0 <= z < dims[2] and 0 <= w < dims[3]):
            continue
        entry = marks_by_layer.setdefault(w, [set(), set(), set()])
        entry[0].add(x)
        entry[0].add(x + 1)
        entry[1].add(y)
        entry[1].add(y + 1)
        entry[2].add(z)
        entry[2].add(z + 1)
    return {layer: (entry[0], entry[1], entry[2]) for layer, entry in marks_by_layer.items()}


def _draw_layer_grid_or_shadow(
    surface: pygame.Surface,
    dims3: Cell3,
    dims4: tuple[int, int, int, int],
    w_layer: int,
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
        extras=_projection_extras(view, dims4, w_layer),
    )
    draw_projected_grid_mode(
        surface=surface,
        dims=dims3,
        grid_mode=grid_mode,
        draw_full_grid=lambda: _draw_board_grid(surface, dims3, dims4, w_layer, view, draw_rect, zoom),
        project_raw=lambda raw: _project_raw_point(raw, dims3, dims4, w_layer, view, center_px, zoom),
        transform_raw=lambda raw: _transform_raw_point(raw, dims3, dims4, w_layer, view),
        helper_marks=helper_marks,
        helper_cache_key=helper_cache_key,
        frame_color=GRID_COLOR,
        inner_color=(52, 64, 95),
        frame_width=2,
        edge_width=2,
    )


def _layer_faces(
    state: GameStateND,
    w_layer: int,
    view: LayerView3D,
    center_px: Point2,
    dims3: Cell3,
    dims4: tuple[int, int, int, int],
    zoom: float,
    locked_by_layer: LockedLayerCells,
    active_overlay: ActiveOverlay4D | None = None,
) -> list[Face]:
    faces: list[Face] = []
    for coord3, cell_id, is_active in _layer_cells(
        state,
        w_layer,
        locked_by_layer,
        active_overlay,
    ):
        faces.extend(
            _build_cell_faces(
                cell=coord3,
                color=color_for_cell(cell_id, COLOR_MAP),
                view=view,
                center_px=center_px,
                dims3=dims3,
                dims4=dims4,
                w_layer=w_layer,
                zoom=zoom,
                active=is_active,
            )
        )
    return faces


def _draw_layer_clear_animation(
    surface: pygame.Surface,
    clear_anim: Optional[ClearAnimation4D],
    w_layer: int,
    view: LayerView3D,
    center_px: Point2,
    dims3: Cell3,
    dims4: tuple[int, int, int, int],
    zoom: float,
) -> None:
    if clear_anim is None or not clear_anim.ghost_cells:
        return

    fade = 1.0 - clear_anim.progress
    if fade <= 0.0:
        return

    ghost_faces: list[Face] = []
    for coord4, base_color in clear_anim.ghost_cells:
        x, y, z, w = coord4
        if w != w_layer:
            continue
        if not (0 <= x < dims3[0] and 0 <= y < dims3[1] and 0 <= z < dims3[2]):
            continue
        glow_color = tuple(
            min(255, int(channel * (0.62 + 0.38 * fade) + 160 * fade))
            for channel in base_color
        )
        ghost_faces.extend(
            _build_cell_faces(
                cell=(x, y, z),
                color=glow_color,
                view=view,
                center_px=center_px,
                dims3=dims3,
                dims4=dims4,
                w_layer=w_layer,
                zoom=zoom,
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


def _draw_layer_board(
    surface: pygame.Surface,
    state: GameStateND,
    view: LayerView3D,
    rect: pygame.Rect,
    w_layer: int,
    active_w: int,
    fonts: GfxFonts,
    grid_mode: GridMode,
    locked_by_layer: LockedLayerCells,
    helper_marks: tuple[set[int], set[int], set[int]] | None = None,
    clear_anim: Optional[ClearAnimation4D] = None,
    active_overlay: ActiveOverlay4D | None = None,
) -> None:
    border = LAYER_ACTIVE if w_layer == active_w else LAYER_FRAME
    pygame.draw.rect(surface, (16, 20, 40), rect, border_radius=8)
    pygame.draw.rect(surface, border, rect, 2, border_radius=8)

    label = render_text_cached(
        font=fonts.hint_font,
        text=f"w = {w_layer}",
        color=LAYER_LABEL,
    )
    surface.blit(label, (rect.x + 8, rect.y + 6))

    draw_rect = pygame.Rect(rect.x + 6, rect.y + 24, rect.width - 12, rect.height - 30)
    dims4 = state.config.dims
    dims3 = (dims4[0], dims4[1], dims4[2])
    zoom = _fit_zoom(dims3, dims4, w_layer, view, draw_rect) * view.zoom_scale
    zoom = max(8.0, min(170.0, zoom))
    _draw_layer_grid_or_shadow(surface, dims3, dims4, w_layer, view, draw_rect, zoom, grid_mode, helper_marks)

    center_px = (draw_rect.centerx, draw_rect.centery)
    faces = _layer_faces(
        state,
        w_layer,
        view,
        center_px,
        dims3,
        dims4,
        zoom,
        locked_by_layer,
        active_overlay=active_overlay,
    )
    faces.sort(key=lambda x: x[0], reverse=True)
    for _depth, poly, color, active in faces:
        pygame.draw.polygon(surface, color, poly)
        border_col = (255, 255, 255) if active else (24, 24, 34)
        pygame.draw.polygon(surface, border_col, poly, 2 if active else 1)
    _draw_layer_clear_animation(surface, clear_anim, w_layer, view, center_px, dims3, dims4, zoom)


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


def _draw_side_panel(
    surface: pygame.Surface,
    state: GameStateND,
    slice_state: SliceState,
    panel_rect: pygame.Rect,
    fonts: GfxFonts,
    grid_mode: GridMode,
    bot_lines: tuple[str, ...] = (),
) -> None:
    gravity_ms = gravity_interval_ms_from_config(state.config)
    rows_per_sec = 1000.0 / gravity_ms if gravity_ms > 0 else 0.0
    z_slice = slice_state.axis_values.get(2, 0)
    w_slice = slice_state.axis_values.get(3, 0)
    max_z = state.config.dims[2] - 1
    max_w = state.config.dims[3] - 1
    analysis_lines = hud_analysis_lines(state.last_score_analysis)
    low_priority_lines = [*bot_lines, *([""] if bot_lines and analysis_lines else []), *analysis_lines]

    lines = (
        "4D Tetris",
        "View: multiple 3D w-layers",
        "",
        f"Dims: {state.config.dims}",
        f"Piece set: {piece_set_4d_label(state.config.piece_set_id)}",
        f"Score: {state.score}",
        f"Cleared: {state.lines_cleared}",
        f"Speed: {state.config.speed_level}",
        f"Exploration: {'ON' if state.config.exploration_mode else 'OFF'}",
        f"Challenge layers: {state.config.challenge_layers}",
        f"Fall: {rows_per_sec:.2f}/s",
        f"Score mod: x{state.score_multiplier:.2f}",
        f"Grid: {grid_mode_label(grid_mode)}",
        "",
        f"Active z slice: {z_slice}/{max_z}",
        f"Active w layer: {w_slice}/{max_w}",
    )

    draw_game_side_panel(
        surface,
        panel_rect=panel_rect,
        fonts=fonts,
        header_lines=lines,
        control_groups=control_groups_for_dimension(4),
        low_priority_lines=tuple(low_priority_lines),
        game_over=state.game_over,
        min_controls_h=150,
    )


def draw_game_frame(
    screen: pygame.Surface,
    state: GameStateND,
    slice_state: SliceState,
    view: LayerView3D,
    fonts: GfxFonts,
    grid_mode: GridMode,
    bot_lines: tuple[str, ...] = (),
    clear_anim: Optional[ClearAnimation4D] = None,
    active_overlay: ActiveOverlay4D | None = None,
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
    pygame.draw.rect(screen, (14, 18, 36), layers_rect, border_radius=10)

    active_w = slice_state.axis_values.get(3, state.config.dims[3] // 2)
    helper_marks_by_layer = _helper_grid_marks_by_layer(state) if grid_mode == GridMode.HELPER else {}
    locked_by_layer = _locked_cells_by_layer(state)
    layer_rects = _layer_grid_rects(layers_rect, state.config.dims[3])
    for w_layer, layer_rect in enumerate(layer_rects):
        _draw_layer_board(
            screen,
            state,
            view,
            layer_rect,
            w_layer,
            active_w,
            fonts,
            grid_mode=grid_mode,
            locked_by_layer=locked_by_layer,
            helper_marks=helper_marks_by_layer.get(w_layer),
            clear_anim=clear_anim,
            active_overlay=active_overlay,
        )

    _draw_side_panel(screen, state, slice_state, panel_rect, fonts, grid_mode=grid_mode, bot_lines=bot_lines)


def _reset_view(view: LayerView3D) -> None:
    view.yaw_deg = 32.0
    view.pitch_deg = -26.0
    view.xw_deg = 0.0
    view.zw_deg = 0.0
    view.zoom_scale = 1.0
    view.stop_animation()


def handle_view_key(key: int, view: LayerView3D) -> bool:
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
                "zoom_in": lambda: setattr(view, "zoom_scale", min(2.6, view.zoom_scale * 1.08)),
                "zoom_out": lambda: setattr(view, "zoom_scale", max(0.45, view.zoom_scale / 1.08)),
                "reset": lambda: _reset_view(view),
                "cycle_projection": lambda: None,
            },
        )
        is not None
    )


def handle_view_keydown(event: pygame.event.Event, view: LayerView3D) -> bool:
    return handle_view_key(event.key, view)


def spawn_clear_animation_if_needed(
    state: GameStateND,
    last_lines_cleared: int,
) -> tuple[Optional[ClearAnimation4D], int]:
    if state.lines_cleared == last_lines_cleared:
        return None, last_lines_cleared

    ghost_cells = collect_cleared_ghost_cells(
        state,
        expected_coord_len=4,
        color_for_cell=lambda cell_id: color_for_cell(cell_id, COLOR_MAP),
    )
    if not ghost_cells:
        return None, state.lines_cleared
    return ClearAnimation4D(ghost_cells=tuple(ghost_cells)), state.lines_cleared
