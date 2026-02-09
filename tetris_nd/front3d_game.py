# tetris_nd/front3d_game.py
import math
import random
import sys
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Tuple

import pygame

from .board import BoardND
from .game_nd import GameConfigND, GameStateND
from .keybindings import (
    CAMERA_KEYS_3D,
    CONTROL_LINES_3D_CAMERA,
    CONTROL_LINES_3D_GAME,
    KEYS_3D,
    SYSTEM_KEYS,
    key_matches,
)


MARGIN = 20
SIDE_PANEL = 360
BG_TOP = (18, 24, 50)
BG_BOTTOM = (6, 8, 20)
TEXT_COLOR = (230, 230, 230)
HIGHLIGHT_COLOR = (255, 215, 0)
GRID_COLOR = (75, 90, 125)

DEFAULT_GAME_SEED = 1337

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

# (indices, shade factor)
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
    except Exception:
        return GfxFonts(
            title_font=pygame.font.Font(None, 36),
            menu_font=pygame.font.Font(None, 24),
            hint_font=pygame.font.Font(None, 18),
            panel_font=pygame.font.Font(None, 17),
        )


def draw_gradient_background(surface: pygame.Surface,
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
class GameSettings3D:
    width: int = 6
    height: int = 18
    depth: int = 6
    speed_level: int = 1


class MenuAction(Enum):
    QUIT = auto()
    START_GAME = auto()
    SELECT_UP = auto()
    SELECT_DOWN = auto()
    VALUE_LEFT = auto()
    VALUE_RIGHT = auto()
    NO_OP = auto()


@dataclass
class MenuState:
    settings: GameSettings3D = field(default_factory=GameSettings3D)
    selected_index: int = 0
    running: bool = True
    start_game: bool = False


_MENU_FIELDS = [
    ("Board width", "width", 4, 12),
    ("Board height", "height", 12, 30),
    ("Board depth", "depth", 4, 12),
    ("Speed level", "speed_level", 1, 10),
]


def gather_menu_actions() -> List[MenuAction]:
    actions: List[MenuAction] = []
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            actions.append(MenuAction.QUIT)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                actions.append(MenuAction.QUIT)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                actions.append(MenuAction.START_GAME)
            elif event.key == pygame.K_UP:
                actions.append(MenuAction.SELECT_UP)
            elif event.key == pygame.K_DOWN:
                actions.append(MenuAction.SELECT_DOWN)
            elif event.key == pygame.K_LEFT:
                actions.append(MenuAction.VALUE_LEFT)
            elif event.key == pygame.K_RIGHT:
                actions.append(MenuAction.VALUE_RIGHT)
    if not actions:
        actions.append(MenuAction.NO_OP)
    return actions


def apply_menu_actions(state: MenuState, actions: List[MenuAction]) -> None:
    for action in actions:
        if action == MenuAction.NO_OP:
            continue
        if action == MenuAction.QUIT:
            state.running = False
            continue
        if action == MenuAction.START_GAME:
            state.start_game = True
            continue
        if action == MenuAction.SELECT_UP:
            state.selected_index = (state.selected_index - 1) % len(_MENU_FIELDS)
            continue
        if action == MenuAction.SELECT_DOWN:
            state.selected_index = (state.selected_index + 1) % len(_MENU_FIELDS)
            continue
        if action in (MenuAction.VALUE_LEFT, MenuAction.VALUE_RIGHT):
            _, attr_name, min_val, max_val = _MENU_FIELDS[state.selected_index]
            value = getattr(state.settings, attr_name)
            value = value - 1 if action == MenuAction.VALUE_LEFT else value + 1
            value = max(min_val, min(max_val, value))
            setattr(state.settings, attr_name, value)


def draw_menu(screen: pygame.Surface, fonts: GfxFonts, state: MenuState) -> None:
    draw_gradient_background(screen, BG_TOP, BG_BOTTOM)
    width, _ = screen.get_size()

    title = fonts.title_font.render("3D Tetris – Setup", True, TEXT_COLOR)
    subtitle = fonts.hint_font.render(
        "Use Up/Down to select, Left/Right to change, Enter to start.",
        True,
        (210, 210, 230),
    )
    screen.blit(title, ((width - title.get_width()) // 2, 60))
    screen.blit(subtitle, ((width - subtitle.get_width()) // 2, 108))

    panel_w = int(width * 0.62)
    panel_h = 280
    panel_x = (width - panel_w) // 2
    panel_y = 160

    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (0, 0, 0, 145), panel.get_rect(), border_radius=16)
    screen.blit(panel, (panel_x, panel_y))

    y = panel_y + 28
    for idx, (label, attr_name, _, _) in enumerate(_MENU_FIELDS):
        value = getattr(state.settings, attr_name)
        text = f"{label}: {value}"
        selected = idx == state.selected_index
        text_color = HIGHLIGHT_COLOR if selected else TEXT_COLOR
        surf = fonts.menu_font.render(text, True, text_color)
        rect = surf.get_rect(topleft=(panel_x + 36, y))
        if selected:
            hi_rect = rect.inflate(20, 10)
            hi = pygame.Surface(hi_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(hi, (255, 255, 255, 40), hi.get_rect(), border_radius=10)
            screen.blit(hi, hi_rect.topleft)
        screen.blit(surf, rect.topleft)
        y += 50

    hints = [
        "Esc = quit",
        "Projection modes are available during gameplay (P).",
    ]
    hy = panel_y + panel_h + 20
    for line in hints:
        surf = fonts.hint_font.render(line, True, (210, 210, 230))
        screen.blit(surf, ((width - surf.get_width()) // 2, hy))
        hy += surf.get_height() + 4


def run_menu(screen: pygame.Surface, fonts: GfxFonts) -> Optional[GameSettings3D]:
    clock = pygame.time.Clock()
    state = MenuState()

    while state.running and not state.start_game:
        _dt = clock.tick(60)
        actions = gather_menu_actions()
        apply_menu_actions(state, actions)
        draw_menu(screen, fonts, state)
        pygame.display.flip()

    if state.running and state.start_game:
        return state.settings
    return None


def gravity_interval_ms_from_config(cfg: GameConfigND) -> int:
    level = max(1, min(10, cfg.speed_level))
    return max(80, 1000 // level)


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
class Camera3D:
    # Default to the same angled preset used by 4D layer views.
    projection: ProjectionMode3D = ProjectionMode3D.ORTHOGRAPHIC
    yaw_deg: float = 32.0
    pitch_deg: float = -26.0
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

    def cycle_projection(self) -> None:
        if self.projection == ProjectionMode3D.PROJECTIVE:
            self.projection = ProjectionMode3D.ORTHOGRAPHIC
            self.auto_fit_once = True
        elif self.projection == ProjectionMode3D.ORTHOGRAPHIC:
            self.projection = ProjectionMode3D.PERSPECTIVE
        else:
            self.projection = ProjectionMode3D.PROJECTIVE


def build_config(settings: GameSettings3D) -> GameConfigND:
    return GameConfigND(
        dims=(settings.width, settings.height, settings.depth),
        gravity_axis=1,
        speed_level=settings.speed_level,
    )


def create_initial_state(cfg: GameConfigND) -> GameStateND:
    board = BoardND(cfg.dims)
    return GameStateND(config=cfg, board=board, rng=random.Random(DEFAULT_GAME_SEED))


def _world_center(cell: Tuple[int, int, int], dims: Tuple[int, int, int]) -> Tuple[float, float, float]:
    w, h, d = dims
    x = cell[0] - (w - 1) / 2.0
    y = -(cell[1] - (h - 1) / 2.0)
    z = cell[2] - (d - 1) / 2.0
    return x, y, z


def _raw_to_world(raw: Tuple[float, float, float], dims: Tuple[int, int, int]) -> Tuple[float, float, float]:
    w, h, d = dims
    x = raw[0] - (w - 1) / 2.0
    y = -(raw[1] - (h - 1) / 2.0)
    z = raw[2] - (d - 1) / 2.0
    return x, y, z


def _transform_point(world: Tuple[float, float, float], camera: Camera3D) -> Tuple[float, float, float]:
    x, y, z = world
    yaw = math.radians(camera.yaw_deg)
    pitch = math.radians(camera.pitch_deg)

    x1 = math.cos(yaw) * x + math.sin(yaw) * z
    z1 = -math.sin(yaw) * x + math.cos(yaw) * z
    y1 = y

    y2 = math.cos(pitch) * y1 - math.sin(pitch) * z1
    z2 = math.sin(pitch) * y1 + math.cos(pitch) * z1
    return x1, y2, z2


def _project_point(trans: Tuple[float, float, float],
                   camera: Camera3D,
                   center_px: Tuple[float, float]) -> Optional[Tuple[float, float]]:
    tx, ty, tz = trans
    cx, cy = center_px

    if camera.projection == ProjectionMode3D.ORTHOGRAPHIC:
        return cx + camera.zoom * tx, cy - camera.zoom * ty

    if camera.projection == ProjectionMode3D.PERSPECTIVE:
        zc = tz + camera.cam_dist
        if zc <= 0.08:
            return None
        return cx + camera.zoom * (tx / zc), cy - camera.zoom * (ty / zc)

    # Projective transform (default per RDS)
    denom = 1.0 + camera.projective_strength * (tz + camera.projective_bias)
    if denom <= 0.15:
        denom = 0.15
    return cx + camera.zoom * (tx / denom), cy - camera.zoom * (ty / denom)


def _draw_board_box(surface: pygame.Surface,
                    dims: Tuple[int, int, int],
                    camera: Camera3D,
                    board_rect: pygame.Rect) -> None:
    w, h, d = dims
    raw_corners = [
        (-0.5, -0.5, -0.5),
        (w - 0.5, -0.5, -0.5),
        (w - 0.5, h - 0.5, -0.5),
        (-0.5, h - 0.5, -0.5),
        (-0.5, -0.5, d - 0.5),
        (w - 0.5, -0.5, d - 0.5),
        (w - 0.5, h - 0.5, d - 0.5),
        (-0.5, h - 0.5, d - 0.5),
    ]

    center_px = (board_rect.centerx, board_rect.centery)
    projected: List[Optional[Tuple[float, float]]] = []
    for raw in raw_corners:
        world = _raw_to_world(raw, dims)
        trans = _transform_point(world, camera)
        projected.append(_project_point(trans, camera, center_px))

    for a, b in _BOX_EDGES:
        pa = projected[a]
        pb = projected[b]
        if pa is None or pb is None:
            continue
        pygame.draw.line(surface, GRID_COLOR, pa, pb, 1)


def _project_raw_point(raw: Tuple[float, float, float],
                       dims: Tuple[int, int, int],
                       camera: Camera3D,
                       center_px: Tuple[float, float]) -> Optional[Tuple[float, float]]:
    world = _raw_to_world(raw, dims)
    trans = _transform_point(world, camera)
    return _project_point(trans, camera, center_px)


def _draw_board_grid(surface: pygame.Surface,
                     dims: Tuple[int, int, int],
                     camera: Camera3D,
                     board_rect: pygame.Rect) -> None:
    """Draw full projected lattice (x/y/z lines), not just bounding edges."""
    center_px = (board_rect.centerx, board_rect.centery)
    grid_inner = (52, 64, 95)

    # y-axis lines
    for x in range(dims[0] + 1):
        xr = x - 0.5
        for z in range(dims[2] + 1):
            zr = z - 0.5
            p0 = _project_raw_point((xr, -0.5, zr), dims, camera, center_px)
            p1 = _project_raw_point((xr, dims[1] - 0.5, zr), dims, camera, center_px)
            if p0 is not None and p1 is not None:
                pygame.draw.line(surface, grid_inner, p0, p1, 1)

    # x-axis lines
    for y in range(dims[1] + 1):
        yr = y - 0.5
        for z in range(dims[2] + 1):
            zr = z - 0.5
            p0 = _project_raw_point((-0.5, yr, zr), dims, camera, center_px)
            p1 = _project_raw_point((dims[0] - 0.5, yr, zr), dims, camera, center_px)
            if p0 is not None and p1 is not None:
                pygame.draw.line(surface, grid_inner, p0, p1, 1)

    # z-axis lines
    for x in range(dims[0] + 1):
        xr = x - 0.5
        for y in range(dims[1] + 1):
            yr = y - 0.5
            p0 = _project_raw_point((xr, yr, -0.5), dims, camera, center_px)
            p1 = _project_raw_point((xr, yr, dims[2] - 0.5), dims, camera, center_px)
            if p0 is not None and p1 is not None:
                pygame.draw.line(surface, grid_inner, p0, p1, 1)

    # Emphasize outer frame.
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
    projected: List[Optional[Tuple[float, float]]] = [
        _project_raw_point(raw, dims, camera, center_px) for raw in raw_corners
    ]
    for a, b in _BOX_EDGES:
        pa = projected[a]
        pb = projected[b]
        if pa is not None and pb is not None:
            pygame.draw.line(surface, GRID_COLOR, pa, pb, 2)


def _build_cell_faces(cell: Tuple[int, int, int],
                      color: Tuple[int, int, int],
                      camera: Camera3D,
                      center_px: Tuple[float, float],
                      dims: Tuple[int, int, int],
                      active: bool) -> List[Tuple[float, List[Tuple[float, float]], Tuple[int, int, int], bool]]:
    center_world = _world_center(cell, dims)
    transformed: List[Tuple[float, float, float]] = []
    projected: List[Optional[Tuple[float, float]]] = []

    for ox, oy, oz in _CUBE_VERTS:
        world = (center_world[0] + ox, center_world[1] + oy, center_world[2] + oz)
        trans = _transform_point(world, camera)
        transformed.append(trans)
        projected.append(_project_point(trans, camera, center_px))

    if any(p is None for p in projected):
        return []

    items: List[Tuple[float, List[Tuple[float, float]], Tuple[int, int, int], bool]] = []
    for face_indices, shade_factor in _CUBE_FACES:
        poly = [projected[i] for i in face_indices]  # type: ignore[arg-type]
        avg_depth = sum(transformed[i][2] for i in face_indices) / 4.0
        face_color = _shade(color, shade_factor * (1.08 if active else 1.0))
        items.append((avg_depth, poly, face_color, active))
    return items


def _draw_board_3d(surface: pygame.Surface,
                   state: GameStateND,
                   camera: Camera3D,
                   board_rect: pygame.Rect,
                   show_grid: bool = True) -> None:
    dims = state.config.dims
    center_px = (board_rect.centerx, board_rect.centery)

    if show_grid:
        _draw_board_grid(surface, dims, camera, board_rect)

    cells: List[Tuple[Tuple[int, int, int], int, bool]] = []
    for coord, cell_id in state.board.cells.items():
        x, y, z = coord
        if 0 <= x < dims[0] and 0 <= y < dims[1] and 0 <= z < dims[2]:
            cells.append(((x, y, z), cell_id, False))

    if state.current_piece is not None:
        cell_id = state.current_piece.shape.color_id
        for coord in state.current_piece.cells():
            x, y, z = coord
            if 0 <= x < dims[0] and 0 <= y < dims[1] and 0 <= z < dims[2]:
                cells.append(((x, y, z), cell_id, True))

    faces: List[Tuple[float, List[Tuple[float, float]], Tuple[int, int, int], bool]] = []
    for coord, cell_id, active in cells:
        faces.extend(
            _build_cell_faces(
                cell=coord,
                color=_color_for_cell(cell_id),
                camera=camera,
                center_px=center_px,
                dims=dims,  # type: ignore[arg-type]
                active=active,
            )
        )

    # Draw far-to-near by camera-space depth.
    faces.sort(key=lambda x: x[0], reverse=True)

    for _depth, poly, color, active in faces:
        pygame.draw.polygon(surface, color, poly)
        border = (255, 255, 255) if active else (25, 25, 35)
        border_w = 2 if active else 1
        pygame.draw.polygon(surface, border, poly, border_w)


def _draw_side_panel(surface: pygame.Surface,
                     state: GameStateND,
                     camera: Camera3D,
                     panel_rect: pygame.Rect,
                     fonts: GfxFonts,
                     show_grid: bool) -> None:
    panel = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
    pygame.draw.rect(panel, (0, 0, 0, 140), panel.get_rect(), border_radius=12)
    surface.blit(panel, panel_rect.topleft)

    gravity_ms = gravity_interval_ms_from_config(state.config)
    rows_per_sec = 1000.0 / gravity_ms if gravity_ms > 0 else 0.0

    lines = [
        "3D Tetris",
        "",
        f"Dims: {state.config.dims}",
        f"Projection: {projection_label(camera.projection)}",
        f"Score: {state.score}",
        f"Layers: {state.lines_cleared}",
        f"Speed: {state.config.speed_level}",
        f"Fall: {rows_per_sec:.2f}/s",
        f"Grid: {'ON' if show_grid else 'OFF'}",
        "",
        f"Yaw: {camera.yaw_deg:.1f}",
        f"Pitch: {camera.pitch_deg:.1f}",
        f"Zoom: {camera.zoom:.1f}",
        "",
        *CONTROL_LINES_3D_GAME,
        "",
        *CONTROL_LINES_3D_CAMERA,
        " G          = toggle grid",
        "",
        "R = restart   M = menu",
        "Esc = quit",
    ]

    y = panel_rect.y + 16
    for line in lines:
        surf = fonts.panel_font.render(line, True, TEXT_COLOR)
        surface.blit(surf, (panel_rect.x + 14, y))
        y += surf.get_height() + 3

    if state.game_over:
        over = fonts.panel_font.render("GAME OVER", True, (255, 80, 80))
        surface.blit(over, (panel_rect.x + 14, y + 6))


def _auto_fit_orthographic_zoom(camera: Camera3D,
                                dims: Tuple[int, int, int],
                                board_rect: pygame.Rect) -> None:
    """
    One-shot fit so the entire board is visible for orthographic projection
    at the current yaw/pitch.
    """
    if not camera.auto_fit_once:
        return
    if camera.projection != ProjectionMode3D.ORTHOGRAPHIC:
        return

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
    transformed = [_transform_point(_raw_to_world(raw, dims), camera) for raw in raw_corners]
    min_x = min(t[0] for t in transformed)
    max_x = max(t[0] for t in transformed)
    min_y = min(t[1] for t in transformed)
    max_y = max(t[1] for t in transformed)
    span_x = max(0.01, max_x - min_x)
    span_y = max(0.01, max_y - min_y)
    fit_x = (board_rect.width - 18) / span_x
    fit_y = (board_rect.height - 18) / span_y
    camera.zoom = max(12.0, min(140.0, min(fit_x, fit_y)))
    camera.auto_fit_once = False


def draw_game_frame(screen: pygame.Surface,
                    state: GameStateND,
                    camera: Camera3D,
                    fonts: GfxFonts,
                    show_grid: bool) -> None:
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
    _draw_board_3d(screen, state, camera, board_rect, show_grid=show_grid)
    _draw_side_panel(screen, state, camera, panel_rect, fonts, show_grid=show_grid)


def handle_camera_keydown(event: pygame.event.Event, camera: Camera3D) -> bool:
    key = event.key
    if key_matches(CAMERA_KEYS_3D, "yaw_neg", key):
        camera.yaw_deg = (camera.yaw_deg - 5.0) % 360.0
        return True
    if key_matches(CAMERA_KEYS_3D, "yaw_pos", key):
        camera.yaw_deg = (camera.yaw_deg + 5.0) % 360.0
        return True
    if key_matches(CAMERA_KEYS_3D, "pitch_pos", key):
        camera.pitch_deg = min(89.0, camera.pitch_deg + 5.0)
        return True
    if key_matches(CAMERA_KEYS_3D, "pitch_neg", key):
        camera.pitch_deg = max(-89.0, camera.pitch_deg - 5.0)
        return True
    if key_matches(CAMERA_KEYS_3D, "zoom_in", key):
        camera.zoom = min(140.0, camera.zoom + 3.0)
        return True
    if key_matches(CAMERA_KEYS_3D, "zoom_out", key):
        camera.zoom = max(18.0, camera.zoom - 3.0)
        return True
    if key_matches(CAMERA_KEYS_3D, "reset", key):
        camera.reset()
        return True
    if key_matches(CAMERA_KEYS_3D, "cycle_projection", key):
        camera.cycle_projection()
        return True
    return False


def handle_game_keydown(event: pygame.event.Event,
                        state: GameStateND,
                        cfg: GameConfigND) -> str:
    key = event.key

    if key_matches(SYSTEM_KEYS, "quit", key):
        return "quit"
    if key_matches(SYSTEM_KEYS, "menu", key):
        return "menu"
    if key_matches(SYSTEM_KEYS, "restart", key):
        return "restart"
    if key == pygame.K_g:
        return "toggle_grid"

    if state.game_over:
        return "continue"

    if key_matches(KEYS_3D, "move_x_neg", key):
        state.try_move_axis(0, -1)
        return "continue"
    if key_matches(KEYS_3D, "move_x_pos", key):
        state.try_move_axis(0, 1)
        return "continue"
    if key_matches(KEYS_3D, "move_z_neg", key):
        state.try_move_axis(2, -1)
        return "continue"
    if key_matches(KEYS_3D, "move_z_pos", key):
        state.try_move_axis(2, 1)
        return "continue"
    if key_matches(KEYS_3D, "soft_drop", key):
        state.try_move_axis(cfg.gravity_axis, 1)
        return "continue"
    if key_matches(KEYS_3D, "hard_drop", key):
        state.hard_drop()
        return "continue"

    # x-y rotations
    if key_matches(KEYS_3D, "rotate_xy_pos", key):
        state.try_rotate(0, cfg.gravity_axis, 1)
        return "continue"
    if key_matches(KEYS_3D, "rotate_xy_neg", key):
        state.try_rotate(0, cfg.gravity_axis, -1)
        return "continue"

    # x-z rotations
    if key_matches(KEYS_3D, "rotate_xz_pos", key):
        state.try_rotate(0, 2, 1)
        return "continue"
    if key_matches(KEYS_3D, "rotate_xz_neg", key):
        state.try_rotate(0, 2, -1)
        return "continue"

    # y-z rotations
    if key_matches(KEYS_3D, "rotate_yz_pos", key):
        state.try_rotate(cfg.gravity_axis, 2, 1)
        return "continue"
    if key_matches(KEYS_3D, "rotate_yz_neg", key):
        state.try_rotate(cfg.gravity_axis, 2, -1)
        return "continue"

    return "continue"


def run_game_loop(screen: pygame.Surface,
                  cfg: GameConfigND,
                  fonts: GfxFonts) -> bool:
    state = create_initial_state(cfg)
    camera = Camera3D()
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

            if handle_camera_keydown(event, camera):
                continue

            result = handle_game_keydown(event, state, cfg)
            if result == "quit":
                return False
            if result == "menu":
                return True
            if result == "restart":
                state = create_initial_state(cfg)
                gravity_accumulator = 0
            if result == "toggle_grid":
                show_grid = not show_grid

        while not state.game_over and gravity_accumulator >= gravity_interval_ms:
            state.step_gravity()
            gravity_accumulator -= gravity_interval_ms

        draw_game_frame(screen, state, camera, fonts, show_grid=show_grid)
        pygame.display.flip()


def suggested_window_size(cfg: GameConfigND) -> Tuple[int, int]:
    board_w = int(max(560, cfg.dims[0] * 68))
    board_h = int(max(620, cfg.dims[1] * 30))
    return board_w + SIDE_PANEL + 3 * MARGIN, board_h + 2 * MARGIN


def run() -> None:
    pygame.init()
    fonts = init_fonts()

    running = True
    while running:
        pygame.display.set_caption("3D Tetris – Setup")
        menu_screen = pygame.display.set_mode((980, 720), pygame.RESIZABLE)
        settings = run_menu(menu_screen, fonts)
        if settings is None:
            break

        cfg = build_config(settings)
        win_w, win_h = suggested_window_size(cfg)
        pygame.display.set_caption("3D Tetris")
        game_screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)

        back_to_menu = run_game_loop(game_screen, cfg, fonts)
        if not back_to_menu:
            running = False

    pygame.quit()
    sys.exit()
