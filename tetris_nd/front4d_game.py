# tetris_nd/front4d_game.py
import math
import sys
from dataclasses import dataclass
from typing import List, Tuple

import pygame

from .frontend_nd import (
    build_config,
    create_initial_slice_state,
    create_initial_state,
    gravity_interval_ms_from_config,
    handle_game_keydown,
    init_fonts,
    run_menu,
    GfxFonts,
    SliceState,
)
from .game_nd import GameConfigND, GameStateND
from .keybindings import CONTROL_LINES_ND_4D


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

_CUBE_VERTS = [
    (-0.5, -0.5, -0.5),
    (0.5, -0.5, -0.5),
    (0.5, 0.5, -0.5),
    (-0.5, 0.5, -0.5),
    (-0.5, -0.5, 0.5),
    (0.5, -0.5, 0.5),
    (0.5, 0.5, 0.5),
    (-0.5, 0.5, 0.5),
]

_CUBE_FACES = [
    ([0, 1, 2, 3], 0.58),
    ([4, 5, 6, 7], 0.95),
    ([0, 3, 7, 4], 0.72),
    ([1, 2, 6, 5], 0.84),
    ([0, 1, 5, 4], 0.63),
    ([3, 2, 6, 7], 1.10),
]

_BOX_EDGES = [
    (0, 1), (1, 2), (2, 3), (3, 0),
    (4, 5), (5, 6), (6, 7), (7, 4),
    (0, 4), (1, 5), (2, 6), (3, 7),
]


def _shade(color: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
    return (
        max(0, min(255, int(color[0] * factor))),
        max(0, min(255, int(color[1] * factor))),
        max(0, min(255, int(color[2] * factor))),
    )


def _color_for_cell(cell_id: int) -> Tuple[int, int, int]:
    if cell_id <= 0:
        return (200, 200, 200)
    return COLOR_MAP.get(cell_id, (200, 200, 200))


def _draw_gradient_background(surface: pygame.Surface,
                              top_color: Tuple[int, int, int],
                              bottom_color: Tuple[int, int, int]) -> None:
    width, height = surface.get_size()
    for y in range(height):
        t = y / max(1, height - 1)
        r = int(top_color[0] * (1 - t) + bottom_color[0] * t)
        g = int(top_color[1] * (1 - t) + bottom_color[1] * t)
        b = int(top_color[2] * (1 - t) + bottom_color[2] * t)
        pygame.draw.line(surface, (r, g, b), (0, y), (width, y))


@dataclass
class LayerView3D:
    # Fixed camera for every w-layer board.
    yaw_deg: float = 32.0
    pitch_deg: float = -26.0


def _raw_to_world(raw: Tuple[float, float, float], dims: Tuple[int, int, int]) -> Tuple[float, float, float]:
    w, h, d = dims
    x = raw[0] - (w - 1) / 2.0
    y = -(raw[1] - (h - 1) / 2.0)
    z = raw[2] - (d - 1) / 2.0
    return x, y, z


def _transform_point(world: Tuple[float, float, float], view: LayerView3D) -> Tuple[float, float, float]:
    x, y, z = world
    yaw = math.radians(view.yaw_deg)
    pitch = math.radians(view.pitch_deg)

    x1 = math.cos(yaw) * x + math.sin(yaw) * z
    z1 = -math.sin(yaw) * x + math.cos(yaw) * z
    y1 = y

    y2 = math.cos(pitch) * y1 - math.sin(pitch) * z1
    z2 = math.sin(pitch) * y1 + math.cos(pitch) * z1
    return x1, y2, z2


def _fit_zoom(dims: Tuple[int, int, int], view: LayerView3D, rect: pygame.Rect) -> float:
    raw_corners = [
        (-0.5, -0.5, -0.5),
        (dims[0] - 0.5, -0.5, -0.5),
        (dims[0] - 0.5, dims[1] - 0.5, -0.5),
        (-0.5, dims[1] - 0.5, -0.5),
        (-0.5, -0.5, dims[2] - 0.5),
        (dims[0] - 0.5, -0.5, dims[2] - 0.5),
        (dims[0] - 0.5, dims[1] - 0.5, dims[2] - 0.5),
        (-0.5, dims[1] - 0.5, dims[2] - 0.5),
    ]
    transformed = [_transform_point(_raw_to_world(c, dims), view) for c in raw_corners]
    min_x = min(t[0] for t in transformed)
    max_x = max(t[0] for t in transformed)
    min_y = min(t[1] for t in transformed)
    max_y = max(t[1] for t in transformed)
    span_x = max(0.01, max_x - min_x)
    span_y = max(0.01, max_y - min_y)
    zoom_x = (rect.width - 14) / span_x
    zoom_y = (rect.height - 24) / span_y
    return max(8.0, min(120.0, min(zoom_x, zoom_y)))


def _project_point(trans: Tuple[float, float, float],
                   center_px: Tuple[float, float],
                   zoom: float) -> Tuple[float, float]:
    tx, ty, _tz = trans
    cx, cy = center_px
    return cx + zoom * tx, cy - zoom * ty


def _project_raw_point(raw: Tuple[float, float, float],
                       dims: Tuple[int, int, int],
                       view: LayerView3D,
                       center_px: Tuple[float, float],
                       zoom: float) -> Tuple[float, float]:
    world = _raw_to_world(raw, dims)
    trans = _transform_point(world, view)
    return _project_point(trans, center_px, zoom)


def _draw_board_grid(surface: pygame.Surface,
                     dims: Tuple[int, int, int],
                     view: LayerView3D,
                     rect: pygame.Rect,
                     zoom: float) -> None:
    """Draw projected lattice grid using the same projection path as cubes."""
    center_px = (rect.centerx, rect.centery)
    grid_inner = (52, 64, 95)

    # y-axis lines
    for x in range(dims[0] + 1):
        xr = x - 0.5
        for z in range(dims[2] + 1):
            zr = z - 0.5
            p0 = _project_raw_point((xr, -0.5, zr), dims, view, center_px, zoom)
            p1 = _project_raw_point((xr, dims[1] - 0.5, zr), dims, view, center_px, zoom)
            pygame.draw.line(surface, grid_inner, p0, p1, 1)

    # x-axis lines
    for y in range(dims[1] + 1):
        yr = y - 0.5
        for z in range(dims[2] + 1):
            zr = z - 0.5
            p0 = _project_raw_point((-0.5, yr, zr), dims, view, center_px, zoom)
            p1 = _project_raw_point((dims[0] - 0.5, yr, zr), dims, view, center_px, zoom)
            pygame.draw.line(surface, grid_inner, p0, p1, 1)

    # z-axis lines
    for x in range(dims[0] + 1):
        xr = x - 0.5
        for y in range(dims[1] + 1):
            yr = y - 0.5
            p0 = _project_raw_point((xr, yr, -0.5), dims, view, center_px, zoom)
            p1 = _project_raw_point((xr, yr, dims[2] - 0.5), dims, view, center_px, zoom)
            pygame.draw.line(surface, grid_inner, p0, p1, 1)

    # Emphasize the outer box frame.
    raw_corners = [
        (-0.5, -0.5, -0.5),
        (dims[0] - 0.5, -0.5, -0.5),
        (dims[0] - 0.5, dims[1] - 0.5, -0.5),
        (-0.5, dims[1] - 0.5, -0.5),
        (-0.5, -0.5, dims[2] - 0.5),
        (dims[0] - 0.5, -0.5, dims[2] - 0.5),
        (dims[0] - 0.5, dims[1] - 0.5, dims[2] - 0.5),
        (-0.5, dims[1] - 0.5, dims[2] - 0.5),
    ]
    projected: List[Tuple[float, float]] = []
    for raw in raw_corners:
        projected.append(_project_raw_point(raw, dims, view, center_px, zoom))
    for a, b in _BOX_EDGES:
        pygame.draw.line(surface, GRID_COLOR, projected[a], projected[b], 2)


def _build_cell_faces(cell: Tuple[int, int, int],
                      color: Tuple[int, int, int],
                      view: LayerView3D,
                      center_px: Tuple[float, float],
                      dims: Tuple[int, int, int],
                      zoom: float,
                      active: bool) -> List[Tuple[float, List[Tuple[float, float]], Tuple[int, int, int], bool]]:
    transformed: List[Tuple[float, float, float]] = []
    projected: List[Tuple[float, float]] = []
    for ox, oy, oz in _CUBE_VERTS:
        raw = (cell[0] + ox, cell[1] + oy, cell[2] + oz)
        world = _raw_to_world(raw, dims)
        trans = _transform_point(world, view)
        transformed.append(trans)
        projected.append(_project_raw_point(raw, dims, view, center_px, zoom))

    items: List[Tuple[float, List[Tuple[float, float]], Tuple[int, int, int], bool]] = []
    for face_indices, shade_factor in _CUBE_FACES:
        poly = [projected[i] for i in face_indices]
        avg_depth = sum(transformed[i][2] for i in face_indices) / 4.0
        face_color = _shade(color, shade_factor * (1.08 if active else 1.0))
        items.append((avg_depth, poly, face_color, active))
    return items


def _layer_cells(state: GameStateND, w_layer: int) -> List[Tuple[Tuple[int, int, int], int, bool]]:
    dims = state.config.dims
    cells: List[Tuple[Tuple[int, int, int], int, bool]] = []

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


def _draw_layer_board(surface: pygame.Surface,
                      state: GameStateND,
                      view: LayerView3D,
                      rect: pygame.Rect,
                      w_layer: int,
                      active_w: int,
                      fonts: GfxFonts,
                      show_grid: bool) -> None:
    border = LAYER_ACTIVE if w_layer == active_w else LAYER_FRAME
    pygame.draw.rect(surface, (16, 20, 40), rect, border_radius=8)
    pygame.draw.rect(surface, border, rect, 2, border_radius=8)

    label = fonts.hint_font.render(f"w = {w_layer}", True, LAYER_LABEL)
    label_pos = (rect.x + 8, rect.y + 6)
    surface.blit(label, label_pos)

    draw_rect = pygame.Rect(rect.x + 6, rect.y + 24, rect.width - 12, rect.height - 30)
    dims3 = (state.config.dims[0], state.config.dims[1], state.config.dims[2])
    zoom = _fit_zoom(dims3, view, draw_rect)
    if show_grid:
        _draw_board_grid(surface, dims3, view, draw_rect, zoom)

    center_px = (draw_rect.centerx, draw_rect.centery)
    faces: List[Tuple[float, List[Tuple[float, float]], Tuple[int, int, int], bool]] = []
    for coord3, cell_id, is_active in _layer_cells(state, w_layer):
        faces.extend(
            _build_cell_faces(
                cell=coord3,
                color=_color_for_cell(cell_id),
                view=view,
                center_px=center_px,
                dims=dims3,
                zoom=zoom,
                active=is_active,
            )
        )
    faces.sort(key=lambda x: x[0], reverse=True)
    for _depth, poly, color, active in faces:
        pygame.draw.polygon(surface, color, poly)
        border_col = (255, 255, 255) if active else (24, 24, 34)
        pygame.draw.polygon(surface, border_col, poly, 2 if active else 1)


def _layer_grid_rects(area: pygame.Rect, layer_count: int) -> List[pygame.Rect]:
    if layer_count <= 0:
        return []
    cols = max(1, math.ceil(math.sqrt(layer_count)))
    rows = max(1, math.ceil(layer_count / cols))

    cell_w = (area.width - (cols + 1) * LAYER_GAP) // cols
    cell_h = (area.height - (rows + 1) * LAYER_GAP) // rows
    rects: List[pygame.Rect] = []
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
        " G          : toggle grid",
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
                    show_grid: bool) -> None:
    _draw_gradient_background(screen, BG_TOP, BG_BOTTOM)
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
        )

    _draw_side_panel(screen, state, slice_state, panel_rect, fonts, show_grid=show_grid)


def run_game_loop(screen: pygame.Surface, cfg: GameConfigND, fonts: GfxFonts) -> bool:
    state = create_initial_state(cfg)
    slice_state = create_initial_slice_state(cfg)
    view = LayerView3D()
    show_grid = True
    gravity_interval_ms = gravity_interval_ms_from_config(cfg)
    gravity_accumulator = 0
    clock = pygame.time.Clock()

    while True:
        dt = clock.tick(60)
        gravity_accumulator += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_g:
                show_grid = not show_grid
                continue

            result = handle_game_keydown(event, state, slice_state)
            if result == "quit":
                return False
            if result == "menu":
                return True
            if result == "restart":
                state = create_initial_state(cfg)
                slice_state = create_initial_slice_state(cfg)
                gravity_accumulator = 0

        while not state.game_over and gravity_accumulator >= gravity_interval_ms:
            state.step_gravity()
            gravity_accumulator -= gravity_interval_ms

        draw_game_frame(screen, state, slice_state, view, fonts, show_grid=show_grid)
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
