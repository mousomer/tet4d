# tetris_nd/front3d_game.py
import random
import sys
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Tuple

import pygame

from .board import BoardND
from .frontend_nd import dispatch_nd_gameplay_key, system_key_action
from .game_nd import GameConfigND, GameStateND
from .game_loop_common import process_game_events
from .key_dispatch import dispatch_bound_action
from .keybindings import (
    CAMERA_KEYS_3D,
    CONTROL_LINES_3D_CAMERA,
    CONTROL_LINES_3D_GAME,
    PROFILE_SMALL,
    active_key_profile,
    initialize_keybinding_files,
    keybinding_file_label,
    load_active_profile_bindings,
    set_active_key_profile,
)
from .menu_controls import FieldSpec, apply_menu_actions, gather_menu_actions
from .menu_keybinding_shortcuts import menu_binding_hint_line, menu_binding_status_color
from .menu_settings_state import load_menu_settings
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
from .runtime_helpers import advance_gravity, collect_cleared_ghost_cells, tick_animation


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
    except (pygame.error, OSError):
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
    active_profile: str = field(default_factory=active_key_profile)
    rebind_mode: bool = False
    rebind_index: int = 0
    rebind_targets: list[tuple[str, str]] = field(default_factory=list)


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

    rebind_target = "-"
    if state.rebind_targets:
        group, action_name = state.rebind_targets[state.rebind_index % len(state.rebind_targets)]
        rebind_target = f"{group}.{action_name}"

    hints = [
        "Esc = quit",
        menu_binding_hint_line(3),
        f"Profile: {state.active_profile}   [ / ] cycle   N new   Backspace delete custom",
        "F5 save settings   F9 load settings   F8 reset defaults",
        f"B rebind {'ON' if state.rebind_mode else 'OFF'}   target: {rebind_target}   Tab/` target",
        f"Profile file: {keybinding_file_label(3)}",
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
    set_ok, _ = set_active_key_profile(PROFILE_SMALL)
    if set_ok:
        load_active_profile_bindings()
    state = MenuState()
    ok, msg = load_menu_settings(state, 3, include_profile=False)
    if not ok:
        state.bindings_status = msg
        state.bindings_status_error = True

    while state.running and not state.start_game:
        _dt = clock.tick(60)
        actions = gather_menu_actions(state, 3)
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


def _collect_visible_cells(state: GameStateND) -> list[tuple[Cell3, int, bool]]:
    dims = state.config.dims
    cells: list[tuple[Cell3, int, bool]] = []

    for coord, cell_id in state.board.cells.items():
        x, y, z = coord
        if 0 <= x < dims[0] and 0 <= y < dims[1] and 0 <= z < dims[2]:
            cells.append(((x, y, z), cell_id, False))

    if state.current_piece is None:
        return cells

    piece_id = state.current_piece.shape.color_id
    for coord in state.current_piece.cells():
        x, y, z = coord
        if 0 <= x < dims[0] and 0 <= y < dims[1] and 0 <= z < dims[2]:
            cells.append(((x, y, z), piece_id, True))
    return cells


def _faces_for_cells(cells: list[tuple[Cell3, int, bool]],
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

    _draw_sorted_faces(
        surface,
        _faces_for_cells(_collect_visible_cells(state), camera, center_px, dims),
    )
    _draw_clear_animation(surface, clear_anim, camera, center_px, dims)


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
                        _cfg: GameConfigND | None = None) -> str:
    key = event.key

    system_action = system_key_action(key)
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

    dispatch_nd_gameplay_key(key, state)
    return "continue"


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
    show_grid: bool = True
    clear_anim: Optional[ClearAnimation3D] = None
    last_lines_cleared: int = 0
    gravity_accumulator: int = 0

    @classmethod
    def create(cls, cfg: GameConfigND) -> "LoopContext3D":
        state = create_initial_state(cfg)
        return cls(cfg=cfg, state=state, last_lines_cleared=state.lines_cleared)

    def keydown_handler(self, event: pygame.event.Event) -> str:
        if handle_camera_keydown(event, self.camera):
            return "continue"
        return handle_game_keydown(event, self.state)

    def on_restart(self) -> None:
        self.state = create_initial_state(self.cfg)
        self.gravity_accumulator = 0
        self.clear_anim = None
        self.last_lines_cleared = self.state.lines_cleared

    def on_toggle_grid(self) -> None:
        self.show_grid = not self.show_grid


def run_game_loop(screen: pygame.Surface,
                  cfg: GameConfigND,
                  fonts: GfxFonts) -> bool:
    loop = LoopContext3D.create(cfg)
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

        loop.camera.step_animation(dt)
        loop.clear_anim = tick_animation(loop.clear_anim, dt)

        draw_game_frame(
            screen,
            loop.state,
            loop.camera,
            fonts,
            show_grid=loop.show_grid,
            clear_anim=loop.clear_anim,
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
