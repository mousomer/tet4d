# tetris_nd/front4d_game.py
import math
import sys
from dataclasses import dataclass
from typing import Optional, Tuple

import pygame

from .frontend_nd import (
    build_config,
    create_initial_slice_state,
    create_initial_state,
    gravity_interval_ms_from_config,
    handle_game_keydown as handle_nd_game_keydown,
    init_fonts,
    piece_set_4d_label,
    run_menu,
    GfxFonts,
    SliceState,
)
from .game_nd import GameConfigND, GameStateND
from .game_loop_common import process_game_events
from .key_dispatch import dispatch_bound_action
from .keybindings import (
    CAMERA_KEYS_4D,
    CONTROL_LINES_4D_VIEW,
    CONTROL_LINES_ND_4D,
    initialize_keybinding_files,
)
from .projection3d import (
    Face,
    Cell3,
    Point2,
    build_cube_faces,
    color_for_cell,
    draw_projected_box_shadow,
    draw_gradient_background,
    draw_projected_lattice,
    fit_orthographic_zoom,
    interpolate_angle_deg,
    normalize_angle_deg,
    orthographic_point,
    raw_to_world,
    smoothstep01,
    transform_point,
)
from .runtime_helpers import advance_gravity, collect_cleared_ghost_cells, tick_animation


MARGIN = 16
LAYER_GAP = 12
SIDE_PANEL = 360
BG_TOP = (18, 24, 50)
BG_BOTTOM = (6, 8, 20)
TEXT_COLOR = (230, 230, 230)
GRID_COLOR = (75, 90, 125)
LAYER_FRAME = (90, 105, 145)
LAYER_ACTIVE = (255, 220, 110)
LAYER_LABEL = (210, 220, 245)

COLOR_MAP = {
    1: (0, 255, 255),
    2: (255, 255, 0),
    3: (160, 0, 240),
    4: (0, 255, 0),
    5: (255, 0, 0),
    6: (0, 0, 255),
    7: (255, 165, 0),
}


@dataclass
class LayerView3D:
    # Fixed camera for every w-layer board.
    yaw_deg: float = 32.0
    pitch_deg: float = -26.0
    zoom_scale: float = 1.0
    anim_axis: str | None = None
    anim_start: float = 0.0
    anim_target: float = 0.0
    anim_elapsed_ms: float = 0.0
    anim_duration_ms: float = 240.0

    def _start_turn(self, axis: str, target: float) -> None:
        self.anim_axis = axis
        self.anim_elapsed_ms = 0.0
        if axis == "yaw":
            self.anim_start = normalize_angle_deg(self.yaw_deg)
            self.anim_target = normalize_angle_deg(target)
        else:
            self.anim_start = self.pitch_deg
            self.anim_target = max(-89.0, min(89.0, target))

    def start_yaw_turn(self, delta_deg: float) -> None:
        self._start_turn("yaw", self.yaw_deg + delta_deg)

    def start_pitch_turn(self, delta_deg: float) -> None:
        self._start_turn("pitch", self.pitch_deg + delta_deg)

    def step_animation(self, dt_ms: float) -> None:
        if self.anim_axis is None:
            return
        self.anim_elapsed_ms += max(0.0, dt_ms)
        t = 1.0 if self.anim_duration_ms <= 0 else min(1.0, self.anim_elapsed_ms / self.anim_duration_ms)
        if self.anim_axis == "yaw":
            self.yaw_deg = interpolate_angle_deg(self.anim_start, self.anim_target, t)
        else:
            eased = smoothstep01(t)
            self.pitch_deg = self.anim_start + (self.anim_target - self.anim_start) * eased
        if t >= 1.0:
            if self.anim_axis == "yaw":
                self.yaw_deg = normalize_angle_deg(self.anim_target)
            else:
                self.pitch_deg = self.anim_target
            self.anim_axis = None


@dataclass
class ClearAnimation4D:
    ghost_cells: tuple[tuple[tuple[int, int, int, int], tuple[int, int, int]], ...]
    elapsed_ms: float = 0.0
    duration_ms: float = 380.0

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


def _transform_raw_point(raw: tuple[float, float, float],
                         dims: Cell3,
                         view: LayerView3D) -> tuple[float, float, float]:
    world = raw_to_world(raw, dims)
    return transform_point(world, view.yaw_deg, view.pitch_deg)


def _fit_zoom(dims: Cell3, view: LayerView3D, rect: pygame.Rect) -> float:
    base_zoom = fit_orthographic_zoom(
        dims=dims,
        yaw_deg=view.yaw_deg,
        pitch_deg=view.pitch_deg,
        rect=rect,
        pad_x=14,
        pad_y=24,
        min_zoom=8.0,
        max_zoom=120.0,
    )
    return max(8.0, min(170.0, base_zoom * view.zoom_scale))


def _project_raw_point(raw: tuple[float, float, float],
                       dims: Cell3,
                       view: LayerView3D,
                       center_px: Point2,
                       zoom: float) -> Point2:
    trans = _transform_raw_point(raw, dims, view)
    return orthographic_point(trans, center_px, zoom)


def _draw_board_grid(surface: pygame.Surface,
                     dims: Cell3,
                     view: LayerView3D,
                     rect: pygame.Rect,
                     zoom: float) -> None:
    center_px = (rect.centerx, rect.centery)
    draw_projected_lattice(
        surface,
        dims,
        lambda raw: _project_raw_point(raw, dims, view, center_px, zoom),
        inner_color=(52, 64, 95),
        frame_color=GRID_COLOR,
        frame_width=2,
    )


def _build_cell_faces(cell: Cell3,
                      color: tuple[int, int, int],
                      view: LayerView3D,
                      center_px: Point2,
                      dims: Cell3,
                      zoom: float,
                      active: bool) -> list[Face]:
    return build_cube_faces(
        cell=cell,
        color=color,
        project_raw=lambda raw: _project_raw_point(raw, dims, view, center_px, zoom),
        transform_raw=lambda raw: _transform_raw_point(raw, dims, view),
        active=active,
    )


def _layer_cells(state: GameStateND, w_layer: int) -> list[tuple[Cell3, int, bool]]:
    dims = state.config.dims
    cells: list[tuple[Cell3, int, bool]] = []

    for coord, cell_id in state.board.cells.items():
        x, y, z, w = coord
        if w != w_layer:
            continue
        if 0 <= x < dims[0] and 0 <= y < dims[1] and 0 <= z < dims[2]:
            cells.append(((x, y, z), cell_id, False))

    if state.current_piece is not None:
        piece_id = state.current_piece.shape.color_id
        for coord in state.current_piece.cells():
            x, y, z, w = coord
            if w != w_layer:
                continue
            if 0 <= x < dims[0] and 0 <= y < dims[1] and 0 <= z < dims[2]:
                cells.append(((x, y, z), piece_id, True))
    return cells


def _draw_layer_grid_or_shadow(surface: pygame.Surface,
                               dims3: Cell3,
                               view: LayerView3D,
                               draw_rect: pygame.Rect,
                               zoom: float,
                               show_grid: bool) -> None:
    center_px = (draw_rect.centerx, draw_rect.centery)
    if show_grid:
        _draw_board_grid(surface, dims3, view, draw_rect, zoom)
        return
    draw_projected_box_shadow(
        surface,
        dims3,
        project_raw=lambda raw: _project_raw_point(raw, dims3, view, center_px, zoom),
        transform_raw=lambda raw: _transform_raw_point(raw, dims3, view),
    )


def _layer_faces(state: GameStateND,
                 w_layer: int,
                 view: LayerView3D,
                 center_px: Point2,
                 dims3: Cell3,
                 zoom: float) -> list[Face]:
    faces: list[Face] = []
    for coord3, cell_id, is_active in _layer_cells(state, w_layer):
        faces.extend(
            _build_cell_faces(
                cell=coord3,
                color=color_for_cell(cell_id, COLOR_MAP),
                view=view,
                center_px=center_px,
                dims=dims3,
                zoom=zoom,
                active=is_active,
            )
        )
    return faces


def _draw_layer_clear_animation(surface: pygame.Surface,
                                clear_anim: Optional[ClearAnimation4D],
                                w_layer: int,
                                view: LayerView3D,
                                center_px: Point2,
                                dims3: Cell3,
                                zoom: float) -> None:
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
                dims=dims3,
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


def _draw_layer_board(surface: pygame.Surface,
                      state: GameStateND,
                      view: LayerView3D,
                      rect: pygame.Rect,
                      w_layer: int,
                      active_w: int,
                      fonts: GfxFonts,
                      show_grid: bool,
                      clear_anim: Optional[ClearAnimation4D] = None) -> None:
    border = LAYER_ACTIVE if w_layer == active_w else LAYER_FRAME
    pygame.draw.rect(surface, (16, 20, 40), rect, border_radius=8)
    pygame.draw.rect(surface, border, rect, 2, border_radius=8)

    label = fonts.hint_font.render(f"w = {w_layer}", True, LAYER_LABEL)
    label_pos = (rect.x + 8, rect.y + 6)
    surface.blit(label, label_pos)

    draw_rect = pygame.Rect(rect.x + 6, rect.y + 24, rect.width - 12, rect.height - 30)
    dims3 = (state.config.dims[0], state.config.dims[1], state.config.dims[2])
    zoom = _fit_zoom(dims3, view, draw_rect)
    _draw_layer_grid_or_shadow(surface, dims3, view, draw_rect, zoom, show_grid)

    center_px = (draw_rect.centerx, draw_rect.centery)
    faces = _layer_faces(state, w_layer, view, center_px, dims3, zoom)
    faces.sort(key=lambda x: x[0], reverse=True)
    for _depth, poly, color, active in faces:
        pygame.draw.polygon(surface, color, poly)
        border_col = (255, 255, 255) if active else (24, 24, 34)
        pygame.draw.polygon(surface, border_col, poly, 2 if active else 1)
    _draw_layer_clear_animation(surface, clear_anim, w_layer, view, center_px, dims3, zoom)


def _layer_grid_rects(area: pygame.Rect, layer_count: int) -> list[pygame.Rect]:
    if layer_count <= 0:
        return []
    cols = max(1, math.ceil(math.sqrt(layer_count)))
    rows = max(1, math.ceil(layer_count / cols))

    cell_w = (area.width - (cols + 1) * LAYER_GAP) // cols
    cell_h = (area.height - (rows + 1) * LAYER_GAP) // rows
    rects: list[pygame.Rect] = []
    idx = 0
    for row in range(rows):
        for col in range(cols):
            if idx >= layer_count:
                break
            x = area.x + LAYER_GAP + col * (cell_w + LAYER_GAP)
            y = area.y + LAYER_GAP + row * (cell_h + LAYER_GAP)
            rects.append(pygame.Rect(x, y, max(80, cell_w), max(80, cell_h)))
            idx += 1
    return rects


def _draw_side_panel(surface: pygame.Surface,
                     state: GameStateND,
                     slice_state: SliceState,
                     panel_rect: pygame.Rect,
                     fonts: GfxFonts,
                     show_grid: bool) -> None:
    panel = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
    pygame.draw.rect(panel, (0, 0, 0, 140), panel.get_rect(), border_radius=12)
    surface.blit(panel, panel_rect.topleft)

    gravity_ms = gravity_interval_ms_from_config(state.config)
    rows_per_sec = 1000.0 / gravity_ms if gravity_ms > 0 else 0.0
    z_slice = slice_state.axis_values.get(2, 0)
    w_slice = slice_state.axis_values.get(3, 0)
    max_z = state.config.dims[2] - 1
    max_w = state.config.dims[3] - 1

    lines = [
        "4D Tetris",
        "View: multiple 3D w-layers",
        "",
        f"Dims: {state.config.dims}",
        f"Piece set: {piece_set_4d_label(state.config.piece_set_4d)}",
        f"Score: {state.score}",
        f"Cleared: {state.lines_cleared}",
        f"Speed: {state.config.speed_level}",
        f"Fall: {rows_per_sec:.2f}/s",
        f"Grid: {'ON' if show_grid else 'OFF'}",
        "",
        f"Active z slice: {z_slice}/{max_z}",
        f"Active w layer: {w_slice}/{max_w}",
        "",
        *CONTROL_LINES_ND_4D,
        "",
        *CONTROL_LINES_4D_VIEW,
    ]

    y = panel_rect.y + 14
    for line in lines:
        surf = fonts.panel_font.render(line, True, TEXT_COLOR)
        surface.blit(surf, (panel_rect.x + 12, y))
        y += surf.get_height() + 3

    if state.game_over:
        over = fonts.panel_font.render("GAME OVER", True, (255, 80, 80))
        surface.blit(over, (panel_rect.x + 12, y + 8))


def draw_game_frame(screen: pygame.Surface,
                    state: GameStateND,
                    slice_state: SliceState,
                    view: LayerView3D,
                    fonts: GfxFonts,
                    show_grid: bool,
                    clear_anim: Optional[ClearAnimation4D] = None) -> None:
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
            show_grid=show_grid,
            clear_anim=clear_anim,
        )

    _draw_side_panel(screen, state, slice_state, panel_rect, fonts, show_grid=show_grid)


def _reset_view(view: LayerView3D) -> None:
    view.yaw_deg = 32.0
    view.pitch_deg = -26.0
    view.zoom_scale = 1.0
    view.anim_axis = None
    view.anim_elapsed_ms = 0.0


def handle_view_keydown(event: pygame.event.Event, view: LayerView3D) -> bool:
    key = event.key

    return (
        dispatch_bound_action(
            key,
            CAMERA_KEYS_4D,
            {
                "yaw_neg": lambda: view.start_yaw_turn(-90.0),
                "yaw_pos": lambda: view.start_yaw_turn(90.0),
                "pitch_pos": lambda: view.start_pitch_turn(90.0),
                "pitch_neg": lambda: view.start_pitch_turn(-90.0),
                "zoom_in": lambda: setattr(view, "zoom_scale", min(2.6, view.zoom_scale * 1.08)),
                "zoom_out": lambda: setattr(view, "zoom_scale", max(0.45, view.zoom_scale / 1.08)),
                "reset": lambda: _reset_view(view),
                "cycle_projection": lambda: None,
            },
        )
        is not None
    )


def _spawn_clear_animation_if_needed(state: GameStateND,
                                     last_lines_cleared: int) -> tuple[Optional[ClearAnimation4D], int]:
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


@dataclass
class LoopContext4D:
    cfg: GameConfigND
    state: GameStateND
    slice_state: SliceState
    view: LayerView3D
    show_grid: bool = True
    clear_anim: Optional[ClearAnimation4D] = None
    last_lines_cleared: int = 0
    gravity_accumulator: int = 0

    @classmethod
    def create(cls, cfg: GameConfigND) -> "LoopContext4D":
        state = create_initial_state(cfg)
        return cls(
            cfg=cfg,
            state=state,
            slice_state=create_initial_slice_state(cfg),
            view=LayerView3D(),
            last_lines_cleared=state.lines_cleared,
        )

    def keydown_handler(self, event: pygame.event.Event) -> str:
        if handle_view_keydown(event, self.view):
            return "continue"
        return handle_nd_game_keydown(event, self.state, self.slice_state)

    def on_restart(self) -> None:
        self.state = create_initial_state(self.cfg)
        self.slice_state = create_initial_slice_state(self.cfg)
        self.gravity_accumulator = 0
        self.clear_anim = None
        self.last_lines_cleared = self.state.lines_cleared

    def on_toggle_grid(self) -> None:
        self.show_grid = not self.show_grid


def run_game_loop(screen: pygame.Surface, cfg: GameConfigND, fonts: GfxFonts) -> bool:
    loop = LoopContext4D.create(cfg)
    gravity_interval_ms = gravity_interval_ms_from_config(cfg)
    clock = pygame.time.Clock()

    while True:
        dt = clock.tick(60)
        loop.gravity_accumulator += dt

        decision = process_game_events(
            keydown_handler=loop.keydown_handler,
            on_restart=loop.on_restart,
            on_toggle_grid=loop.on_toggle_grid,
        )
        if decision == "quit":
            return False
        if decision == "menu":
            return True

        loop.gravity_accumulator = advance_gravity(
            loop.state,
            loop.gravity_accumulator,
            gravity_interval_ms,
        )

        new_clear_anim, loop.last_lines_cleared = _spawn_clear_animation_if_needed(
            loop.state,
            loop.last_lines_cleared,
        )
        if new_clear_anim is not None:
            loop.clear_anim = new_clear_anim

        loop.view.step_animation(dt)
        loop.clear_anim = tick_animation(loop.clear_anim, dt)

        draw_game_frame(
            screen,
            loop.state,
            loop.slice_state,
            loop.view,
            fonts,
            show_grid=loop.show_grid,
            clear_anim=loop.clear_anim,
        )
        pygame.display.flip()


def suggested_window_size(cfg: GameConfigND) -> Tuple[int, int]:
    layers = cfg.dims[3]
    cols = max(1, math.ceil(math.sqrt(layers)))
    rows = max(1, math.ceil(layers / cols))
    board_w = cols * 250 + (cols + 1) * LAYER_GAP
    board_h = rows * 230 + (rows + 1) * LAYER_GAP
    return max(1200, board_w + SIDE_PANEL + 3 * MARGIN), max(760, board_h + 2 * MARGIN)


def run() -> None:
    pygame.init()
    initialize_keybinding_files()
    fonts = init_fonts()

    running = True
    while running:
        pygame.display.set_caption("4D Tetris – Setup")
        menu_screen = pygame.display.set_mode((900, 680), pygame.RESIZABLE)
        settings = run_menu(menu_screen, fonts, 4)
        if settings is None:
            break

        cfg = build_config(settings, 4)
        win_w, win_h = suggested_window_size(cfg)
        pygame.display.set_caption("4D Tetris")
        game_screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)

        back_to_menu = run_game_loop(game_screen, cfg, fonts)
        if not back_to_menu:
            running = False

    pygame.quit()
    sys.exit()
