# tetris_nd/front3d_game.py
import random
import sys
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Tuple

import pygame

from .board import BoardND
from .game_nd import GameConfigND, GameStateND
from .game_loop_common import process_game_events
from .key_dispatch import dispatch_bound_action, match_bound_action
from .keybindings import (
    CAMERA_KEYS_3D,
    CONTROL_LINES_3D_CAMERA,
    CONTROL_LINES_3D_GAME,
    KEYS_3D,
    SYSTEM_KEYS,
    initialize_keybinding_files,
)
from .menu_controls import FieldSpec, apply_menu_actions, gather_menu_actions
from .menu_keybinding_shortcuts import menu_binding_hint_line, menu_binding_status_color
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
    perspective_point,
    projective_point,
    raw_to_world,
    smoothstep01,
    transform_point,
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

@dataclass
class GameSettings3D:
    width: int = 6
    height: int = 18
    depth: int = 6
    speed_level: int = 1


@dataclass
class MenuState:
    settings: GameSettings3D = field(default_factory=GameSettings3D)
    selected_index: int = 0
    running: bool = True
    start_game: bool = False
    bindings_status: str = ""
    bindings_status_error: bool = False


_MENU_FIELDS: list[FieldSpec] = [
    ("Board width", "width", 4, 12),
    ("Board height", "height", 12, 30),
    ("Board depth", "depth", 4, 12),
    ("Speed level", "speed_level", 1, 10),
]


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
        menu_binding_hint_line(3),
        "Projection modes are available during gameplay (P).",
    ]
    hy = panel_y + panel_h + 20
    for line in hints:
        surf = fonts.hint_font.render(line, True, (210, 210, 230))
        screen.blit(surf, ((width - surf.get_width()) // 2, hy))
        hy += surf.get_height() + 4

    if state.bindings_status:
        status_color = menu_binding_status_color(state.bindings_status_error)
        status = fonts.hint_font.render(state.bindings_status, True, status_color)
        screen.blit(status, ((width - status.get_width()) // 2, hy))


def run_menu(screen: pygame.Surface, fonts: GfxFonts) -> Optional[GameSettings3D]:
    clock = pygame.time.Clock()
    state = MenuState()

    while state.running and not state.start_game:
        _dt = clock.tick(60)
        actions = gather_menu_actions()
        apply_menu_actions(state, actions, _MENU_FIELDS, 3)
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
    anim_axis: str | None = None
    anim_start: float = 0.0
    anim_target: float = 0.0
    anim_elapsed_ms: float = 0.0
    anim_duration_ms: float = 240.0

    def reset(self) -> None:
        self.projection = ProjectionMode3D.ORTHOGRAPHIC
        self.yaw_deg = 32.0
        self.pitch_deg = -26.0
        self.zoom = 52.0
        self.cam_dist = 6.5
        self.auto_fit_once = True
        self.anim_axis = None
        self.anim_elapsed_ms = 0.0

    def cycle_projection(self) -> None:
        if self.projection == ProjectionMode3D.PROJECTIVE:
            self.projection = ProjectionMode3D.ORTHOGRAPHIC
            self.auto_fit_once = True
        elif self.projection == ProjectionMode3D.ORTHOGRAPHIC:
            self.projection = ProjectionMode3D.PERSPECTIVE
        else:
            self.projection = ProjectionMode3D.PROJECTIVE

    def _start_turn(self, axis: str, target: float) -> None:
        self.anim_axis = axis
        self.anim_elapsed_ms = 0.0
        if axis == "yaw":
            self.anim_start = normalize_angle_deg(self.yaw_deg)
            self.anim_target = normalize_angle_deg(target)
        else:
            self.anim_start = self.pitch_deg
            self.anim_target = max(-89.0, min(89.0, target))
        self.auto_fit_once = True

    def start_yaw_turn(self, delta_deg: float) -> None:
        self._start_turn("yaw", self.yaw_deg + delta_deg)

    def start_pitch_turn(self, delta_deg: float) -> None:
        self._start_turn("pitch", self.pitch_deg + delta_deg)

    def is_animating(self) -> bool:
        return self.anim_axis is not None

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


def build_config(settings: GameSettings3D) -> GameConfigND:
    return GameConfigND(
        dims=(settings.width, settings.height, settings.depth),
        gravity_axis=1,
        speed_level=settings.speed_level,
    )


def create_initial_state(cfg: GameConfigND) -> GameStateND:
    board = BoardND(cfg.dims)
    return GameStateND(config=cfg, board=board, rng=random.Random(DEFAULT_GAME_SEED))


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


def _draw_board_3d(surface: pygame.Surface,
                   state: GameStateND,
                   camera: Camera3D,
                   board_rect: pygame.Rect,
                   show_grid: bool = True,
                   clear_anim: Optional[ClearAnimation3D] = None) -> None:
    dims = state.config.dims
    center_px = (board_rect.centerx, board_rect.centery)

    if show_grid:
        _draw_board_grid(surface, dims, camera, board_rect)
    else:
        draw_projected_box_shadow(
            surface,
            dims,
            project_raw=lambda raw: _project_raw_point(raw, dims, camera, center_px),
            transform_raw=lambda raw: _transform_raw_point(raw, dims, camera),
        )

    cells: list[tuple[Cell3, int, bool]] = []
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

    # Draw far-to-near by camera-space depth.
    faces.sort(key=lambda x: x[0], reverse=True)

    for _depth, poly, color, active in faces:
        pygame.draw.polygon(surface, color, poly)
        border = (255, 255, 255) if active else (25, 25, 35)
        border_w = 2 if active else 1
        pygame.draw.polygon(surface, border, poly, border_w)

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
                    show_grid: bool,
                    clear_anim: Optional[ClearAnimation3D] = None) -> None:
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
        show_grid=show_grid,
        clear_anim=clear_anim,
    )
    _draw_side_panel(screen, state, camera, panel_rect, fonts, show_grid=show_grid)


def handle_camera_keydown(event: pygame.event.Event, camera: Camera3D) -> bool:
    key = event.key
    return (
        dispatch_bound_action(
            key,
            CAMERA_KEYS_3D,
            {
                "yaw_neg": lambda: camera.start_yaw_turn(-90.0),
                "yaw_pos": lambda: camera.start_yaw_turn(90.0),
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


def handle_game_keydown(event: pygame.event.Event,
                        state: GameStateND,
                        cfg: GameConfigND) -> str:
    key = event.key

    system_action = match_bound_action(
        key,
        SYSTEM_KEYS,
        ("quit", "menu", "restart", "toggle_grid"),
    )
    if system_action == "quit":
        return "quit"
    if system_action == "menu":
        return "menu"
    if system_action == "restart":
        return "restart"
    if system_action == "toggle_grid":
        return "toggle_grid"

    if state.game_over:
        return "continue"

    dispatch_bound_action(
        key,
        KEYS_3D,
        {
            "move_x_neg": lambda: state.try_move_axis(0, -1),
            "move_x_pos": lambda: state.try_move_axis(0, 1),
            "move_z_neg": lambda: state.try_move_axis(2, -1),
            "move_z_pos": lambda: state.try_move_axis(2, 1),
            "soft_drop": lambda: state.try_move_axis(cfg.gravity_axis, 1),
            "hard_drop": state.hard_drop,
            "rotate_xy_pos": lambda: state.try_rotate(0, cfg.gravity_axis, 1),
            "rotate_xy_neg": lambda: state.try_rotate(0, cfg.gravity_axis, -1),
            "rotate_xz_pos": lambda: state.try_rotate(0, 2, 1),
            "rotate_xz_neg": lambda: state.try_rotate(0, 2, -1),
            "rotate_yz_pos": lambda: state.try_rotate(cfg.gravity_axis, 2, 1),
            "rotate_yz_neg": lambda: state.try_rotate(cfg.gravity_axis, 2, -1),
        },
    )

    return "continue"


def run_game_loop(screen: pygame.Surface,
                  cfg: GameConfigND,
                  fonts: GfxFonts) -> bool:
    state = create_initial_state(cfg)
    camera = Camera3D()
    show_grid = True
    clear_anim: Optional[ClearAnimation3D] = None
    last_lines_cleared = state.lines_cleared
    gravity_interval_ms = gravity_interval_ms_from_config(cfg)
    gravity_accumulator = 0
    clock = pygame.time.Clock()

    while True:
        dt = clock.tick(60)
        gravity_accumulator += dt

        def on_restart() -> None:
            nonlocal state, gravity_accumulator, clear_anim, last_lines_cleared
            state = create_initial_state(cfg)
            gravity_accumulator = 0
            clear_anim = None
            last_lines_cleared = state.lines_cleared

        def on_toggle_grid() -> None:
            nonlocal show_grid
            show_grid = not show_grid

        def keydown_handler(event: pygame.event.Event) -> str:
            if handle_camera_keydown(event, camera):
                return "continue"
            return handle_game_keydown(event, state, cfg)

        decision = process_game_events(
            keydown_handler=keydown_handler,
            on_restart=on_restart,
            on_toggle_grid=on_toggle_grid,
        )
        if decision == "quit":
            return False
        if decision == "menu":
            return True

        while not state.game_over and gravity_accumulator >= gravity_interval_ms:
            state.step_gravity()
            gravity_accumulator -= gravity_interval_ms

        if state.lines_cleared != last_lines_cleared:
            ghost_cells: list[tuple[Cell3, tuple[int, int, int]]] = []
            for coord, cell_id in state.board.last_cleared_cells:
                if len(coord) != 3:
                    continue
                x, y, z = coord
                ghost_cells.append(((x, y, z), color_for_cell(cell_id, COLOR_MAP)))
            if ghost_cells:
                clear_anim = ClearAnimation3D(ghost_cells=tuple(ghost_cells))
            else:
                clear_anim = None
            last_lines_cleared = state.lines_cleared

        camera.step_animation(dt)

        if clear_anim is not None:
            clear_anim.step(dt)
            if clear_anim.done:
                clear_anim = None

        draw_game_frame(
            screen,
            state,
            camera,
            fonts,
            show_grid=show_grid,
            clear_anim=clear_anim,
        )
        pygame.display.flip()


def suggested_window_size(cfg: GameConfigND) -> Tuple[int, int]:
    board_w = int(max(560, cfg.dims[0] * 68))
    board_h = int(max(620, cfg.dims[1] * 30))
    return board_w + SIDE_PANEL + 3 * MARGIN, board_h + 2 * MARGIN


def run() -> None:
    pygame.init()
    initialize_keybinding_files()
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
