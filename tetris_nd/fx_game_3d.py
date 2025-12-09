# tetris_nd/gfx_pygame.py

from dataclasses import dataclass
from enum import Enum, auto
from typing import Tuple, Optional

import math
from math import sqrt
import pygame

from .game2d import GameState, GameConfig


# ---------- Visual config & colors ----------

CELL_SIZE_DEFAULT = 30          # default pixels per board cell
MARGIN = 20                     # outer margin for board
SIDE_PANEL = 200                # width for score / text / d-pad

BG_COLOR = (10, 10, 30)
GRID_COLOR = (40, 40, 80)
TEXT_COLOR = (230, 230, 230)
HIGHLIGHT_COLOR = (255, 215, 0)
# Border color for panel and board frames
BORDER_COLOR = (200, 200, 240)

# Tetromino-ish colors for IDs 1..7
COLOR_MAP = {
    1: (0, 255, 255),    # I - cyan
    2: (255, 255, 0),    # O - yellow
    3: (160, 0, 240),    # T - purple
    4: (0, 255, 0),      # S - green
    5: (255, 0, 0),      # Z - red
    6: (0, 0, 255),      # J - blue
    7: (255, 165, 0),    # L - orange
}


def color_for_cell(cell_id: int) -> Tuple[int, int, int]:
    if cell_id <= 0:
        return (0, 0, 0)
    return COLOR_MAP.get(cell_id, (200, 200, 200))


# ---------- Projection / view settings ----------

class ProjectionMode(Enum):
    TOP_DOWN = auto()
    ISOMETRIC = auto()


@dataclass
class ViewSettings:
    """
    View-only configuration: how to project logical board coords to screen.
    Independent of game rules / engine.
    """
    projection: ProjectionMode = ProjectionMode.TOP_DOWN
    cell_size: int = CELL_SIZE_DEFAULT  # zoom factor
    # Side panel width (resizable). Applies to both 2D and 3D views.
    panel_width: int = SIDE_PANEL
    # 3D view controls (used when projection != TOP_DOWN)
    # New projective camera parameters
    # Defaults chosen to mimic 2D when entering 3D (near top-down)
    yaw_deg: float = 0.0    # rotate around Z (turn left/right)
    pitch_deg: float = 89.0 # rotate around X (tilt up/down)
    roll_deg: float = 0.0   # rotate around Y (bank)
    fov_deg: float = 60.0   # field of view for perspective projection
    # If > 0, overrides fov_deg with explicit focal distance (in projection units)
    focal_dist: float = 0.0
    # Extrusion height factor for 3D box effect (relative to cell units)
    extrude_factor: float = 0.0
    # Camera distance (in world units along camera forward)
    cam_dist: float = 12.0
    # Camera-to-mid-grid translations in world units (relative to board center)
    cam_tx: float = 0.0
    cam_ty: float = 0.0
    cam_tz: float = 0.0
    # Screen-space panning in pixels
    pan_px_x: float = 0.0
    pan_px_y: float = 0.0
    # One-shot autofit to keep whole board in view when entering 3D/resetting
    auto_fit_3d: bool = True
    # Test mode flag (used by UI to display metrics)
    test_mode: bool = False
    # Internal cached board center (set by layout in 3D mode)
    _board_cx: float = 0.0
    _board_cy: float = 0.0
    # Backward-compat placeholders from older parametric oblique mode (unused now)
    azimuth_deg: float = 45.0
    vertical_squash: float = 0.5


# ---------- Fonts container ----------

@dataclass
class GfxFonts:
    title_font: pygame.font.Font
    menu_font: pygame.font.Font
    hint_font: pygame.font.Font
    panel_font: pygame.font.Font


def init_fonts() -> GfxFonts:
    """Initialize a set of fonts, with fallbacks."""
    try:
        title_font = pygame.font.SysFont("consolas", 36, bold=True)
        menu_font = pygame.font.SysFont("consolas", 24)
        hint_font = pygame.font.SysFont("consolas", 18)
        panel_font = pygame.font.SysFont("consolas", 18)
    except Exception:
        title_font = pygame.font.Font(None, 36)
        menu_font = pygame.font.Font(None, 24)
        hint_font = pygame.font.Font(None, 18)
        panel_font = pygame.font.Font(None, 18)
    return GfxFonts(title_font, menu_font, hint_font, panel_font)


# ---------- Misc helpers ----------

def draw_gradient_background(surface: pygame.Surface,
                             top_color: Tuple[int, int, int],
                             bottom_color: Tuple[int, int, int]) -> None:
    """Simple vertical gradient fill."""
    width, height = surface.get_size()
    for y in range(height):
        t = y / max(1, height - 1)
        r = int(top_color[0] * (1 - t) + bottom_color[0] * t)
        g = int(top_color[1] * (1 - t) + bottom_color[1] * t)
        b = int(top_color[2] * (1 - t) + bottom_color[2] * t)
        pygame.draw.line(surface, (r, g, b), (0, y), (width, y))


def draw_button_with_arrow(
    surface: pygame.Surface,
    center: Tuple[int, int],
    size: Tuple[int, int],
    direction: Optional[str],   # 'up', 'down', 'left', 'right', or None
    label: str,
    font: pygame.font.Font,
    bg_color: Tuple[int, int, int],
    border_color: Tuple[int, int, int],
) -> None:
    """
    Draw a rounded rectangular button with an optional arrow icon and a text label.
    Arrow is drawn as a white triangle; label is below the button.
    """
    w, h = size
    rect = pygame.Rect(0, 0, w, h)
    rect.center = center

    # Button background
    button_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(
        button_surf, (*bg_color, 200), button_surf.get_rect(), border_radius=10
    )
    pygame.draw.rect(
        button_surf, border_color, button_surf.get_rect(), width=2, border_radius=10
    )
    surface.blit(button_surf, rect.topleft)

    # Arrow icon
    if direction is not None:
        pad = min(w, h) // 4
        cx, cy = rect.center
        if direction == "up":
            points = [
                (cx, rect.top + pad),
                (rect.left + pad, rect.bottom - pad),
                (rect.right - pad, rect.bottom - pad),
            ]
        elif direction == "down":
            points = [
                (cx, rect.bottom - pad),
                (rect.left + pad, rect.top + pad),
                (rect.right - pad, rect.top + pad),
            ]
        elif direction == "left":
            points = [
                (rect.left + pad, cy),
                (rect.right - pad, rect.top + pad),
                (rect.right - pad, rect.bottom - pad),
            ]
        elif direction == "right":
            points = [
                (rect.right - pad, cy),
                (rect.left + pad, rect.top + pad),
                (rect.left + pad, rect.bottom - pad),
            ]
        else:
            points = []
        if points:
            pygame.draw.polygon(surface, (255, 255, 255), points)

    # Label under the button
    if label:
        text_surf = font.render(label, True, (230, 230, 230))
        text_rect = text_surf.get_rect()
        text_rect.centerx = rect.centerx
        text_rect.top = rect.bottom + 4
        surface.blit(text_surf, text_rect)


# ---------- Menu drawing ----------

def _draw_menu_header(screen: pygame.Surface, fonts: GfxFonts) -> None:
    width, _ = screen.get_size()
    title_text = "4D Tetris – Setup"
    subtitle_text = "Use Up/Down to select, Left/Right to change, Enter to start, Esc to quit."

    title_surf = fonts.title_font.render(title_text, True, TEXT_COLOR)
    subtitle_surf = fonts.hint_font.render(subtitle_text, True, (200, 200, 220))

    title_x = (width - title_surf.get_width()) // 2
    screen.blit(title_surf, (title_x, 60))

    subtitle_x = (width - subtitle_surf.get_width()) // 2
    screen.blit(subtitle_surf, (subtitle_x, 60 + title_surf.get_height() + 10))


def _draw_menu_settings_panel(screen: pygame.Surface,
                              fonts: GfxFonts,
                              width: int,
                              height: int,
                              settings,
                              selected_index: int) -> Tuple[int, int, int, int]:
    """
    Draw the glass panel with width/height/speed settings.
    Returns (panel_x, panel_y, panel_w, panel_h).
    """
    panel_w = int(width * 0.6)
    panel_h = 220
    panel_x = (width - panel_w) // 2
    panel_y = 160

    # Semi-transparent dark panel
    panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel_surf, (0, 0, 0, 140),
                     panel_surf.get_rect(), border_radius=16)
    screen.blit(panel_surf, (panel_x, panel_y))

    # Settings list inside panel
    labels = [
        f"Board width:   {settings.width}",
        f"Board height:  {settings.height}",
        f"Speed level:   {settings.speed_level}   (1 = slow, 10 = fast)",
    ]

    option_y = panel_y + 30
    option_x = panel_x + 40

    for i, text in enumerate(labels):
        is_selected = (i == selected_index)
        txt_color = TEXT_COLOR if not is_selected else HIGHLIGHT_COLOR

        text_surf = fonts.menu_font.render(text, True, txt_color)
        text_rect = text_surf.get_rect(topleft=(option_x, option_y))

        if is_selected:
            # Soft highlight bar behind selected option
            highlight_rect = text_rect.inflate(20, 10)
            highlight_surf = pygame.Surface(highlight_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(
                highlight_surf,
                (255, 255, 255, 40),
                highlight_surf.get_rect(),
                border_radius=10,
            )
            screen.blit(highlight_surf, highlight_rect.topleft)

        screen.blit(text_surf, text_rect.topleft)
        option_y += text_surf.get_height() + 18

    return panel_x, panel_y, panel_w, panel_h


def _draw_menu_dpad_and_commands(screen: pygame.Surface,
                                 fonts: GfxFonts,
                                 panel_x: int,
                                 panel_y: int,
                                 panel_w: int,
                                 panel_h: int) -> None:
    """Draw small D-pad and Enter/Esc buttons under the settings panel."""
    width, _ = screen.get_size()

    # D-pad
    dpad_center_y = panel_y + panel_h + 60
    dpad_center_x = width // 2
    dpad_offset = 50
    button_size = (36, 36)

    up_color = (80, 140, 255)
    down_color = (80, 200, 140)
    side_color = (255, 190, 80)
    border = (240, 240, 255)

    draw_button_with_arrow(
        screen,
        (dpad_center_x, dpad_center_y - dpad_offset),
        button_size,
        "up",
        "Up",
        fonts.hint_font,
        up_color,
        border,
    )
    draw_button_with_arrow(
        screen,
        (dpad_center_x, dpad_center_y + dpad_offset),
        button_size,
        "down",
        "Down",
        fonts.hint_font,
        down_color,
        border,
    )
    draw_button_with_arrow(
        screen,
        (dpad_center_x - dpad_offset, dpad_center_y),
        button_size,
        "left",
        "Left",
        fonts.hint_font,
        side_color,
        border,
    )
    draw_button_with_arrow(
        screen,
        (dpad_center_x + dpad_offset, dpad_center_y),
        button_size,
        "right",
        "Right",
        fonts.hint_font,
        side_color,
        border,
    )

    # Enter / Esc buttons
    cmd_y = dpad_center_y + dpad_offset + 50
    cmd_spacing = 140
    cmd_size = (100, 32)
    cmd_color = (100, 100, 160)
    cmd_border = (230, 230, 255)

    draw_button_with_arrow(
        screen,
        (dpad_center_x - cmd_spacing // 2, cmd_y),
        cmd_size,
        None,
        "Enter = Start",
        fonts.hint_font,
        cmd_color,
        cmd_border,
    )
    draw_button_with_arrow(
        screen,
        (dpad_center_x + cmd_spacing // 2, cmd_y),
        cmd_size,
        None,
        "Esc = Quit",
        fonts.hint_font,
        cmd_color,
        cmd_border,
    )


def draw_menu(screen: pygame.Surface,
              fonts: GfxFonts,
              settings,
              selected_index: int) -> None:
    """Top-level menu draw call."""
    draw_gradient_background(screen, (15, 15, 60), (2, 2, 20))
    width, height = screen.get_size()

    _draw_menu_header(screen, fonts)
    panel_x, panel_y, panel_w, panel_h = _draw_menu_settings_panel(
        screen, fonts, width, height, settings, selected_index
    )
    _draw_menu_dpad_and_commands(screen, fonts, panel_x, panel_y, panel_w, panel_h)


# ---------- Gravity function (used for HUD only) ----------

def gravity_interval_ms_from_config(cfg: GameConfig) -> int:
    """
    Map speed_level to a gravity interval in milliseconds.
    speed_level = 1  -> slow  (1000 ms)
    speed_level = 10 -> fast  (~100 ms)
    """
    base_ms = 1000
    level = max(1, min(10, cfg.speed_level))
    interval = base_ms // level
    return max(80, interval)


# ---------- Game projection & layout ----------

def compute_game_layout(screen: pygame.Surface,
                        cfg: GameConfig,
                        view: ViewSettings) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """
    Compute offsets for board and side panel based on current window size.
    Returns (board_offset, panel_offset).

    board_offset is a base origin for projection (roughly "board center/upper-left").
    """
    window_w, window_h = screen.get_size()
    # The hints panel is fixed at top-right with width view.panel_width (resizable).
    # The board occupies the remaining left area within margins.
    if view.projection == ProjectionMode.TOP_DOWN:
        board_px_w = cfg.width * view.cell_size
        board_px_h = cfg.height * view.cell_size

        avail_w = max(10, window_w - view.panel_width - 2 * MARGIN)
        avail_h = max(10, window_h - 2 * MARGIN)

        # Center the board within the available left area
        board_x = int(MARGIN + (avail_w - board_px_w) / 2)
        board_y = int(MARGIN + (avail_h - board_px_h) / 2)
        board_offset = (board_x, board_y)

        # Panel anchored to top-right
        panel_offset = (window_w - view.panel_width - MARGIN, MARGIN)
        return board_offset, panel_offset
    else:
        # Auto-fit the 3D projected board footprint into available area
        avail_w = max(10, window_w - view.panel_width - 2 * MARGIN)
        avail_h = max(10, window_h - 2 * MARGIN)

        # Helper: project a world point using current camera params
        def proj_point(pt3, s, ox=0.0, oy=0.0) -> Tuple[float, float]:
            wx, wy, wz = pt3
            # Translate world so board center is at origin, then apply user camera translations
            cx_b = cfg.width * 0.5
            cy_b = cfg.height * 0.5
            wx = wx - cx_b - getattr(view, 'cam_tx', 0.0)
            wy = wy - cy_b - getattr(view, 'cam_ty', 0.0)
            wz = wz - getattr(view, 'cam_tz', 0.0)
            yaw = math.radians(view.yaw_deg)
            pitch = math.radians(view.pitch_deg)
            roll = math.radians(view.roll_deg)
            cz, sz = math.cos(yaw), math.sin(yaw)
            cx, sx_ = math.cos(pitch), math.sin(pitch)
            cy, sy_ = math.cos(roll), math.sin(roll)
            r00, r01, r02 = cz, -sz, 0.0
            r10, r11, r12 = sz,  cz, 0.0
            r20, r21, r22 = 0.0, 0.0, 1.0
            t00 = r00
            t01 = r01
            t02 = r02
            t10 = cx * r10 - sx_ * r20
            t11 = cx * r11 - sx_ * r21
            t12 = cx * r12 - sx_ * r22
            t20 = sx_ * r10 + cx * r20
            t21 = sx_ * r11 + cx * r21
            t22 = sx_ * r12 + cx * r22
            R00 =  cy * t00 + sy_ * t02
            R01 =  cy * t01 + sy_ * t12
            R02 =  cy * t02 + sy_ * t22
            R10 =  t10
            R11 =  t11
            R12 =  t12
            R20 = -sy_ * t00 + cy * t02
            R21 = -sy_ * t01 + cy * t12
            R22 = -sy_ * t02 + cy * t22
            rx = R00 * wx + R01 * wy + R02 * wz
            ry = R10 * wx + R11 * wy + R12 * wz
            rz = R20 * wx + R21 * wy + R22 * wz
            # Focal distance overrides FOV if provided
            if getattr(view, 'focal_dist', 0.0) and view.focal_dist > 0.0:
                f = max(0.01, float(view.focal_dist))
            else:
                fov = max(10.0, min(150.0, view.fov_deg))
                f = 1.0 / math.tan(math.radians(fov) * 0.5)
            zc = max(0.1, rz + max(0.5, view.cam_dist))
            px = ox + s * f * (rx / zc)
            py = oy + s * f * (-ry / zc)
            return px, py

        # Cache board center for downstream projection helpers (drawing)
        view._board_cx = cfg.width * 0.5
        view._board_cy = cfg.height * 0.5

        # Project the 8 extreme corners of the board prism
        h = max(0.0, view.extrude_factor)
        w, hh = cfg.width, cfg.height
        corners = [
            (0.0, 0.0, 0.0), (w, 0.0, 0.0), (w, hh, 0.0), (0.0, hh, 0.0),
            (0.0, 0.0, h),   (w, 0.0, h),   (w, hh, h),   (0.0, hh, h),
        ]
        # Start from current size, compute bbox
        s = max(8, view.cell_size)
        pts = [proj_point(c, s) for c in corners]
        minx = min(p[0] for p in pts)
        maxx = max(p[0] for p in pts)
        miny = min(p[1] for p in pts)
        maxy = max(p[1] for p in pts)
        bbox_w = maxx - minx
        bbox_h = maxy - miny

        if view.auto_fit_3d:
            # Compute fit scale and update view once, then lock it
            if bbox_w > 0 and bbox_h > 0:
                scale_fit = min(avail_w / bbox_w, avail_h / bbox_h)
            else:
                scale_fit = 1.0
            new_size = int(max(8, min(64, s * scale_fit)))
            if new_size != view.cell_size:
                view.cell_size = new_size
                s = new_size
                pts = [proj_point(c, s) for c in corners]
                minx = min(p[0] for p in pts)
                maxx = max(p[0] for p in pts)
                miny = min(p[1] for p in pts)
                maxy = max(p[1] for p in pts)
                bbox_w = maxx - minx
                bbox_h = maxy - miny
            view.auto_fit_3d = False

        # Compute offset to center within available area plus margins; add user panning
        base_x = MARGIN + (avail_w - bbox_w) / 2.0
        base_y = MARGIN + (avail_h - bbox_h) / 2.0
        # Shift so that current bbox min corner aligns at base; include pan
        board_x = int(base_x - minx + view.pan_px_x)
        board_y = int(base_y - miny + view.pan_px_y)
        board_offset = (board_x, board_y)

        # Panel anchored to top-right
        panel_offset = (window_w - view.panel_width - MARGIN, MARGIN)
        return board_offset, panel_offset


def _project_cell(coord: Tuple[int, int],
                  board_offset: Tuple[int, int],
                  view: ViewSettings) -> Tuple[float, float, float]:
    """
    Project a logical cell (x, y) to screen coordinates + depth.
    Note: this is view-only; engine doesn't know/care about this.
    """
    x, y = coord
    ox, oy = board_offset
    s = view.cell_size

    if view.projection == ProjectionMode.TOP_DOWN:
        # Classic 2D: simple grid
        sx = ox + x * s
        sy = oy + y * s
        depth = y  # depth for sorting (higher y = in front)
    else:
        # Projective 3D: compute projected center of the cell for reference and depth.
        # Define world center at (x+0.5, y+0.5, h/2), then translate by board center and user camera translations.
        h = max(0.0, view.extrude_factor)
        wx = x + 0.5
        wy = y + 0.5
        wz = h * 0.5
        # Apply world translation by camera translations (board-centering handled in draw via cached values)
        # Note: _project_cell is used only for depth sorting reference; for precise drawing we use _draw_persp_cell.
        wx = wx - getattr(view, 'cam_tx', 0.0)
        wy = wy - getattr(view, 'cam_ty', 0.0)
        wz = wz - getattr(view, 'cam_tz', 0.0)

        # Build rotation matrix R = Rz(yaw) * Rx(pitch) * Ry(roll)
        yaw = math.radians(view.yaw_deg)
        pitch = math.radians(view.pitch_deg)
        roll = math.radians(view.roll_deg)

        cz, sz = math.cos(yaw), math.sin(yaw)
        cx, sx_ = math.cos(pitch), math.sin(pitch)
        cy, sy_ = math.cos(roll), math.sin(roll)

        # Rotation matrices
        # Rz
        r00, r01, r02 = cz, -sz, 0.0
        r10, r11, r12 = sz,  cz, 0.0
        r20, r21, r22 = 0.0, 0.0, 1.0
        # Rx * Rz
        t00 = r00
        t01 = r01
        t02 = r02
        t10 = cx * r10 - sx_ * r20
        t11 = cx * r11 - sx_ * r21
        t12 = cx * r12 - sx_ * r22
        t20 = sx_ * r10 + cx * r20
        t21 = sx_ * r11 + cx * r21
        t22 = sx_ * r12 + cx * r22
        # Ry * (Rx * Rz)
        R00 =  cy * t00 + sy_ * t02
        R01 =  cy * t01 + sy_ * t12
        R02 =  cy * t02 + sy_ * t22
        R10 =  t10
        R11 =  t11
        R12 =  t12
        R20 = -sy_ * t00 + cy * t02
        R21 = -sy_ * t01 + cy * t12
        R22 = -sy_ * t02 + cy * t22

        # Rotate
        rx = R00 * wx + R01 * wy + R02 * wz
        ry = R10 * wx + R11 * wy + R12 * wz
        rz = R20 * wx + R21 * wy + R22 * wz

        # Perspective projection parameters
        if getattr(view, 'focal_dist', 0.0) and view.focal_dist > 0.0:
            f = max(0.01, float(view.focal_dist))
        else:
            fov = max(10.0, min(150.0, view.fov_deg))
            f = 1.0 / math.tan(math.radians(fov) * 0.5)
        cam_dist = max(0.5, view.cam_dist)  # relative distance in world units
        zc = rz + cam_dist
        zc = max(0.1, zc)
        scale = view.cell_size

        sx = ox + scale * f * (rx / zc)
        sy = oy + scale * f * (-ry / zc)
        # Use negative depth so ascending sort draws far objects first
        depth = -zc
    return sx, sy, depth


# ---------- Game drawing primitives ----------

def draw_board(surface: pygame.Surface,
               state: GameState,
               cfg: GameConfig,
               board_offset: Tuple[int, int],
               view: ViewSettings) -> None:
    """
    Draw grid, locked cells, and active piece using the chosen projection.
    """
    if view.projection == ProjectionMode.TOP_DOWN:
        _draw_board_grid_flat(surface, cfg, board_offset, view)

    # Build occupancy set to allow face merging (hide internal faces between adjacent cells)
    occupied = set()
    for (x, y) in state.board.cells.keys():
        if 0 <= x < cfg.width and 0 <= y < cfg.height:
            occupied.add((x, y))
    if state.current_piece is not None:
        for (x, y) in state.current_piece.cells():
            if 0 <= x < cfg.width and 0 <= y < cfg.height:
                occupied.add((x, y))

    # Collect all items with depth for correct drawing order
    # For TOP_DOWN we keep projected screen coords; for 3D we keep logical (x,y)
    draw_items = []

    # Locked cells
    for (x, y), cell_id in state.board.cells.items():
        if 0 <= x < cfg.width and 0 <= y < cfg.height:
            if view.projection == ProjectionMode.TOP_DOWN:
                sx, sy, depth = _project_cell((x, y), board_offset, view)
                draw_items.append((depth, cell_id, sx, sy, False, True, True, True))
            else:
                _cx, _cy, depth = _project_cell((x, y), board_offset, view)
                show_left = ((x - 1, y) not in occupied)
                show_right = ((x + 1, y) not in occupied)
                show_front = ((x, y + 1) not in occupied)
                draw_items.append((depth, cell_id, x, y, False, show_left, show_right, show_front))

    # Active piece (slightly in front: depth + 0.5)
    if state.current_piece is not None:
        piece_color = state.current_piece.shape.color_id
        for (x, y) in state.current_piece.cells():
            if 0 <= x < cfg.width and 0 <= y < cfg.height:
                if view.projection == ProjectionMode.TOP_DOWN:
                    sx, sy, depth = _project_cell((x, y), board_offset, view)
                    draw_items.append((depth + 0.5, piece_color, sx, sy, True, True, True, True))
                else:
                    _cx, _cy, depth = _project_cell((x, y), board_offset, view)
                    show_left = ((x - 1, y) not in occupied)
                    show_right = ((x + 1, y) not in occupied)
                    show_front = ((x, y + 1) not in occupied)
                    draw_items.append((depth + 0.5, piece_color, x, y, True, show_left, show_right, show_front))

    # Sort by depth and draw
    draw_items.sort(key=lambda t: t[0])

    for _, cell_id, a, b, is_active, show_left, show_right, show_front in draw_items:
        color = color_for_cell(cell_id)
        if view.projection == ProjectionMode.TOP_DOWN:
            _draw_flat_cell(surface, a, b, view.cell_size, color, outline=is_active)
        else:
            _draw_persp_cell(surface, int(a), int(b), view.cell_size, color, outline=is_active,
                             view=view, board_offset=board_offset,
                             show_left=show_left, show_right=show_right, show_front=show_front)


def _compute_board_bbox_3d(cfg: GameConfig,
                           view: ViewSettings,
                           board_offset: Tuple[int, int]) -> Tuple[int, int, int, int]:
    """Compute screen-space bbox of the projected board prism in 3D."""
    ox, oy = board_offset
    s = view.cell_size
    w, hh = cfg.width, cfg.height
    h = max(0.0, view.extrude_factor)
    corners = [
        (0.0, 0.0, 0.0), (w, 0.0, 0.0), (w, hh, 0.0), (0.0, hh, 0.0),
        (0.0, 0.0, h),   (w, 0.0, h),   (w, hh, h),   (0.0, hh, h),
    ]

    # Rotation R = Rz(yaw) * Rx(pitch) * Ry(roll)
    yaw = math.radians(view.yaw_deg)
    pitch = math.radians(view.pitch_deg)
    roll = math.radians(view.roll_deg)
    cz, sz = math.cos(yaw), math.sin(yaw)
    cx, sx_ = math.cos(pitch), math.sin(pitch)
    cy, sy_ = math.cos(roll), math.sin(roll)
    r00, r01, r02 = cz, -sz, 0.0
    r10, r11, r12 = sz,  cz, 0.0
    r20, r21, r22 = 0.0, 0.0, 1.0
    t00 = r00
    t01 = r01
    t02 = r02
    t10 = cx * r10 - sx_ * r20
    t11 = cx * r11 - sx_ * r21
    t12 = cx * r12 - sx_ * r22
    t20 = sx_ * r10 + cx * r20
    t21 = sx_ * r11 + cx * r21
    t22 = sx_ * r12 + cx * r22
    R00 =  cy * t00 + sy_ * t02
    R01 =  cy * t01 + sy_ * t12
    R02 =  cy * t02 + sy_ * t22
    R10 =  t10
    R11 =  t11
    R12 =  t12
    R20 = -sy_ * t00 + cy * t02
    R21 = -sy_ * t01 + cy * t12
    R22 = -sy_ * t02 + cy * t22

    fov = max(10.0, min(150.0, view.fov_deg))
    f = 1.0 / math.tan(math.radians(fov) * 0.5)
    cam_dist = max(0.5, view.cam_dist)

    xs: list[float] = []
    ys: list[float] = []
    for wx, wy, wz in corners:
        rx = R00 * wx + R01 * wy + R02 * wz
        ry = R10 * wx + R11 * wy + R12 * wz
        rz = R20 * wx + R21 * wy + R22 * wz
        zc = max(0.1, rz + cam_dist)
        px = ox + s * f * (rx / zc)
        py = oy + s * f * (-ry / zc)
        xs.append(px)
        ys.append(py)

    minx = int(min(xs))
    maxx = int(max(xs))
    miny = int(min(ys))
    maxy = int(max(ys))
    return minx, miny, maxx - minx, maxy - miny


def _draw_board_grid_flat(surface: pygame.Surface,
                          cfg: GameConfig,
                          board_offset: Tuple[int, int],
                          view: ViewSettings) -> None:
    """Draw the flat grid background (only for TOP_DOWN)."""
    ox, oy = board_offset
    w, h = cfg.width, cfg.height
    s = view.cell_size

    # Board background rectangle
    board_rect = pygame.Rect(ox, oy, w * s, h * s)
    pygame.draw.rect(surface, (20, 20, 50), board_rect)

    # Grid lines
    for x in range(w + 1):
        x_px = ox + x * s
        pygame.draw.line(surface, GRID_COLOR, (x_px, oy), (x_px, oy + h * s))
    for y in range(h + 1):
        y_px = oy + y * s
        pygame.draw.line(surface, GRID_COLOR, (ox, y_px), (ox + w * s, y_px))

    # Outline around the game grid
    pygame.draw.rect(surface, BORDER_COLOR, board_rect, 2)


def _draw_flat_cell(surface: pygame.Surface,
                    sx: float,
                    sy: float,
                    s: int,
                    color: Tuple[int, int, int],
                    outline: bool) -> None:
    rect = pygame.Rect(int(sx) + 1, int(sy) + 1, s - 2, s - 2)
    pygame.draw.rect(surface, color, rect)
    if outline:
        pygame.draw.rect(surface, (255, 255, 255), rect, 2)


def _draw_persp_cell(surface: pygame.Surface,
                     x: int,
                     y: int,
                     s: int,
                     color: Tuple[int, int, int],
                     outline: bool,
                     view: ViewSettings,
                     board_offset: Tuple[int, int],
                     show_left: bool = True,
                     show_right: bool = True,
                     show_front: bool = True) -> None:
    """
    Draw a 3D-looking box using the current parametric projection.
    The center of the cell is at (sx, sy). Top is a parallelogram spanned by half-basis vectors.
    """
    ox, oy = board_offset
    # World cube corners for cell at (x,y), unit size in X,Y and height h in Z
    h = max(0.0, view.extrude_factor)
    # 8 vertices (bottom z=0, top z=h)
    # Order: (x0,y0,z0): (x, y, z)
    verts = [
        (x,     y,     0.0),
        (x+1.0, y,     0.0),
        (x+1.0, y+1.0, 0.0),
        (x,     y+1.0, 0.0),
        (x,     y,     h),
        (x+1.0, y,     h),
        (x+1.0, y+1.0, h),
        (x,     y+1.0, h),
    ]

    # Rotation R = Rz(yaw) * Rx(pitch) * Ry(roll)
    yaw = math.radians(view.yaw_deg)
    pitch = math.radians(view.pitch_deg)
    roll = math.radians(view.roll_deg)
    cz, sz = math.cos(yaw), math.sin(yaw)
    cx, sx_ = math.cos(pitch), math.sin(pitch)
    cy, sy_ = math.cos(roll), math.sin(roll)
    r00, r01, r02 = cz, -sz, 0.0
    r10, r11, r12 = sz,  cz, 0.0
    r20, r21, r22 = 0.0, 0.0, 1.0
    t00 = r00
    t01 = r01
    t02 = r02
    t10 = cx * r10 - sx_ * r20
    t11 = cx * r11 - sx_ * r21
    t12 = cx * r12 - sx_ * r22
    t20 = sx_ * r10 + cx * r20
    t21 = sx_ * r11 + cx * r21
    t22 = sx_ * r12 + cx * r22
    R00 =  cy * t00 + sy_ * t02
    R01 =  cy * t01 + sy_ * t12
    R02 =  cy * t02 + sy_ * t22
    R10 =  t10
    R11 =  t11
    R12 =  t12
    R20 = -sy_ * t00 + cy * t02
    R21 = -sy_ * t01 + cy * t12
    R22 = -sy_ * t02 + cy * t22

    if getattr(view, 'focal_dist', 0.0) and view.focal_dist > 0.0:
        f = max(0.01, float(view.focal_dist))
    else:
        fov = max(10.0, min(150.0, view.fov_deg))
        f = 1.0 / math.tan(math.radians(fov) * 0.5)
    cam_dist = max(0.5, view.cam_dist)
    scale = s

    # Project helper
    def proj(pt):
        wx, wy, wz = pt
        # Translate by board center and camera translations
        cx_b = getattr(view, '_board_cx', 0.0)
        cy_b = getattr(view, '_board_cy', 0.0)
        wx = wx - cx_b - getattr(view, 'cam_tx', 0.0)
        wy = wy - cy_b - getattr(view, 'cam_ty', 0.0)
        wz = wz - getattr(view, 'cam_tz', 0.0)
        rx = R00 * wx + R01 * wy + R02 * wz
        ry = R10 * wx + R11 * wy + R12 * wz
        rz = R20 * wx + R21 * wy + R22 * wz
        zc = max(0.1, rz + cam_dist)
        px = ox + scale * f * (rx / zc)
        py = oy + scale * f * (-ry / zc)
        return (px, py)

    p = [proj(v) for v in verts]

    # Define faces as lists of vertex indices
    # Top (z=h): 4,5,6,7
    # X-min face (neighbor at x-1 hides it): [0,3,7,4]
    # X-max face (neighbor at x+1 hides it): [1,2,6,5]
    # Y-max face (neighbor at y+1 hides it): [2,3,7,6]
    top_face = [4, 5, 6, 7]
    right_face = [1, 2, 6, 5]   # x+1
    left_face = [0, 3, 7, 4]    # x
    front_face = [2, 3, 7, 6]   # y+1

    # Slight shade variations for fake depth
    def _mul_color(c, factor):
        return tuple(max(0, min(255, int(ch * factor))) for ch in c)

    top_color = _mul_color(color, 1.1)
    left_color = _mul_color(color, 0.7)
    right_color = _mul_color(color, 0.5)
    front_color = _mul_color(color, 0.6)

    # Utility: snap polygon points to integer pixels consistently to avoid hairline seams
    def _snap(points):
        return [(int(round(px)), int(round(py))) for (px, py) in points]

    # Draw side faces first (only if exposed)
    if show_left:
        pygame.draw.polygon(surface, left_color, _snap([p[i] for i in left_face]))
    if show_right:
        pygame.draw.polygon(surface, right_color, _snap([p[i] for i in right_face]))
    if show_front:
        pygame.draw.polygon(surface, front_color, _snap([p[i] for i in front_face]))

    # Draw top face
    pygame.draw.polygon(surface, top_color, _snap([p[i] for i in top_face]))

    if outline:
        pygame.draw.polygon(surface, (255, 255, 255), _snap([p[i] for i in top_face]), 1)
        if show_left:
            pygame.draw.polygon(surface, (255, 255, 255), _snap([p[i] for i in left_face]), 1)
        if show_right:
            pygame.draw.polygon(surface, (255, 255, 255), _snap([p[i] for i in right_face]), 1)
        if show_front:
            pygame.draw.polygon(surface, (255, 255, 255), _snap([p[i] for i in front_face]), 1)


# ---------- Side panel drawing ----------

def _draw_side_panel_text(surface: pygame.Surface,
                          state: GameState,
                          cfg: GameConfig,
                          view: ViewSettings,
                          panel_offset: Tuple[int, int],
                          fonts: GfxFonts) -> int:
    """Draw the textual part of the side panel. Returns the current y after text."""
    px, py = panel_offset
    gravity_ms = gravity_interval_ms_from_config(cfg)
    rows_per_sec = 1000.0 / gravity_ms if gravity_ms > 0 else 0.0
    # Requirement: instructions window must remain unchanged in 3D view.
    # Keep the same label as in 2D to avoid changing instructions content.
    view_name = "Top-down"

    is_3d = (view.projection != ProjectionMode.TOP_DOWN)
    lines = [
        "4D Tetris – 3D view" if is_3d else "4D Tetris – 2D mode",
        "",
        f"Score: {state.score}",
        f"Lines: {state.lines_cleared}",
        f"Speed level: {cfg.speed_level}",
        f"Fall: {rows_per_sec:.2f} rows/s",
        "",
        f"View: {'3D' if is_3d else view_name}",
        f"Zoom: {view.cell_size}px",
        "",
        "Controls:",
        " Left / Right : move",
        " Up / X       : rot CW",
        " Z            : rot CCW",
        " Down         : soft drop",
        " SPACE        : hard drop",
        "",
        "M: back to menu",
        "V: toggle 2D/3D",
        "+ / - : zoom",
    ]

    # Append 3D camera hints and live values only in 3D mode
    if is_3d:
        # Decide which lens parameter is active
        lens_label = "Focal" if getattr(view, 'focal_dist', 0.0) and view.focal_dist > 0.0 else "FOV"
        lens_value = f"{view.focal_dist:.2f}" if lens_label == "Focal" else f"{view.fov_deg:.1f}°"
        lines += [
            "",
            "3D Camera:",
            f" Yaw (J/L): {view.yaw_deg:.1f}°",
            f" Pitch (I/K): {view.pitch_deg:.1f}°",
            f" Roll (U/O): {view.roll_deg:.1f}°",
            f" {lens_label} ([ ] or ; '): {lens_value}",
            f" CamDist (Q/E): {view.cam_dist:.2f}",
            f" Cam XYZ (Shift+W/S, A/D, Q/E): ({view.cam_tx:.2f}, {view.cam_ty:.2f}, {view.cam_tz:.2f})",
            f" Pan (W/A/S/D px): ({int(view.pan_px_x)}, {int(view.pan_px_y)})",
            f" Extrude (,/.): {view.extrude_factor:.2f}",
            f" Zoom (+/-): {view.cell_size}px",
            " 0     : reset camera",
        ]

        # Show 2D↔3D grid distance metric (RMS / Max in pixels)
        try:
            rms_px, max_px = compute_grid_distance_2d_3d(surface, cfg, state, view)
            lines += [
                "",
                f"2D↔3D grid distance: RMS {rms_px:.1f}px, Max {max_px:.1f}px",
            ]
        except Exception:
            lines += ["", "2D↔3D grid distance: n/a"]

    # Test mode metrics (random grid)
    if getattr(view, 'test_mode', False):
        # Compute minimal gap in current mode and in default 3D/2D for comparison
        try:
            min_gap_cur = compute_min_gap_pixels(surface, cfg, state, view)
            # Build a default-3D mimic-2D preset to compare against 2D too
            # Also compute 2D min gap
            from copy import deepcopy
            v2d = deepcopy(view)
            v2d.projection = ProjectionMode.TOP_DOWN
            min_gap_2d = compute_min_gap_pixels(surface, cfg, state, v2d)

            v3d_def = deepcopy(view)
            v3d_def.projection = ProjectionMode.ISOMETRIC
            v3d_def.yaw_deg = 0.0
            v3d_def.pitch_deg = 89.0
            v3d_def.roll_deg = 0.0
            v3d_def.fov_deg = 60.0
            v3d_def.extrude_factor = 0.0
            v3d_def.cam_dist = 12.0
            # Avoid layout mutating original; disable autofit for metric
            v3d_def.auto_fit_3d = False
            min_gap_3ddef = compute_min_gap_pixels(surface, cfg, state, v3d_def)
            lines += [
                "",
                f"Test mode: min gap (cur): {min_gap_cur}px",
                f"Min gap 2D: {min_gap_2d}px | 3D default: {min_gap_3ddef}px",
            ]
        except Exception:
            # Be robust; skip metrics on error
            lines += ["", "Test mode: metric unavailable"]

    lines += [
        "Esc: quit",
        "R: restart",
    ]

    # Ensure all text stays inside the panel rectangle bounds by wrapping and clipping.
    # Panel geometry
    window_w, window_h = surface.get_size()
    panel_x = px
    panel_y = py
    panel_w = view.panel_width
    panel_h = max(10, window_h - 2 * MARGIN)

    # Padding inside panel for text
    PAD = 8
    max_text_w = max(10, panel_w - 2 * PAD)
    x = panel_x + PAD
    y = panel_y + PAD
    bottom_y = panel_y + panel_h - PAD

    def wrap_line(text: str) -> list[str]:
        if text == "":
            return [""]
        words = text.split(" ")
        lines_acc: list[str] = []
        cur = ""
        for w in words:
            test = (cur + (" " if cur else "") + w)
            if fonts.panel_font.size(test)[0] <= max_text_w:
                cur = test
            else:
                if cur:
                    lines_acc.append(cur)
                # If a single word is longer than max width, hard-cut it
                while fonts.panel_font.size(w)[0] > max_text_w and len(w) > 1:
                    # binary search is overkill; cut progressively
                    cut = len(w)
                    while cut > 1 and fonts.panel_font.size(w[:cut])[0] > max_text_w:
                        cut -= 1
                    lines_acc.append(w[:cut])
                    w = w[cut:]
                cur = w
        lines_acc.append(cur)
        return lines_acc

    for line in lines:
        for wrapped in wrap_line(line):
            if y >= bottom_y:
                # No more vertical space; stop rendering further lines
                return y
            surf = fonts.panel_font.render(wrapped, True, TEXT_COLOR)
            # Clip last line if it would overrun bottom
            if y + surf.get_height() > bottom_y:
                # Skip drawing if it would overflow; alternatively, draw ellipsis
                ell = fonts.panel_font.render("…", True, TEXT_COLOR)
                if y + ell.get_height() <= bottom_y:
                    surface.blit(ell, (x, y))
                    y += ell.get_height() + 4
                return y
            surface.blit(surf, (x, y))
            y += surf.get_height() + 4
    return y


def _draw_side_panel_dpad(surface: pygame.Surface,
                          start_y: int,
                          panel_offset: Tuple[int, int],
                          fonts: GfxFonts,
                          view: ViewSettings) -> int:
    """Draw a mini D-pad inside the side panel. Returns new y."""
    px, _ = panel_offset
    dpad_center_x = px + int(getattr(view, 'panel_width', SIDE_PANEL)) // 2
    dpad_center_y = start_y + 35
    g_button_size = (24, 24)
    g_offset = 26

    pad_bg = (60, 90, 150)
    pad_border = (230, 230, 255)

    draw_button_with_arrow(
        surface,
        (dpad_center_x, dpad_center_y - g_offset),
        g_button_size,
        "up",
        "",
        fonts.hint_font,
        pad_bg,
        pad_border,
    )
    draw_button_with_arrow(
        surface,
        (dpad_center_x, dpad_center_y + g_offset),
        g_button_size,
        "down",
        "",
        fonts.hint_font,
        pad_bg,
        pad_border,
    )
    draw_button_with_arrow(
        surface,
        (dpad_center_x - g_offset, dpad_center_y),
        g_button_size,
        "left",
        "",
        fonts.hint_font,
        pad_bg,
        pad_border,
    )
    draw_button_with_arrow(
        surface,
        (dpad_center_x + g_offset, dpad_center_y),
        g_button_size,
        "right",
        "",
        fonts.hint_font,
        pad_bg,
        pad_border,
    )

    return dpad_center_y + g_offset + 20


def draw_side_panel(surface: pygame.Surface,
                    state: GameState,
                    cfg: GameConfig,
                    view: ViewSettings,
                    panel_offset: Tuple[int, int],
                    fonts: GfxFonts) -> None:
    """Top-level side panel draw."""
    y_after_text = _draw_side_panel_text(surface, state, cfg, view, panel_offset, fonts)
    y_after_dpad = _draw_side_panel_dpad(surface, y_after_text, panel_offset, fonts, view)

    # Game over message below D-pad (if needed)
    if state.game_over:
        px, py = panel_offset
        # Panel geometry and padding like in text block
        window_w, window_h = surface.get_size()
        panel_x = px
        panel_y = py
        panel_w = view.panel_width
        panel_h = max(10, window_h - 2 * MARGIN)
        PAD = 8
        max_text_w = max(10, panel_w - 2 * PAD)
        x = panel_x + PAD
        y = y_after_dpad + 10
        bottom_y = panel_y + panel_h - PAD

        def blit_wrapped(msg: str, color: Tuple[int, int, int]) -> None:
            nonlocal y
            # Simple wrapper using same logic as above
            def wrap_line(text: str) -> list[str]:
                if text == "":
                    return [""]
                words = text.split(" ")
                lines_acc: list[str] = []
                cur = ""
                for w in words:
                    test = (cur + (" " if cur else "") + w)
                    if fonts.panel_font.size(test)[0] <= max_text_w:
                        cur = test
                    else:
                        if cur:
                            lines_acc.append(cur)
                        while fonts.panel_font.size(w)[0] > max_text_w and len(w) > 1:
                            cut = len(w)
                            while cut > 1 and fonts.panel_font.size(w[:cut])[0] > max_text_w:
                                cut -= 1
                            lines_acc.append(w[:cut])
                            w = w[cut:]
                        cur = w
                lines_acc.append(cur)
                return lines_acc

            for wrapped in wrap_line(msg):
                if y >= bottom_y:
                    return
                surf = fonts.panel_font.render(wrapped, True, color)
                if y + surf.get_height() > bottom_y:
                    # draw ellipsis if possible
                    ell = fonts.panel_font.render("…", True, color)
                    if y + ell.get_height() <= bottom_y:
                        surface.blit(ell, (x, y))
                        y += ell.get_height() + 4
                    return
                surface.blit(surf, (x, y))
                y += surf.get_height() + 4

        blit_wrapped("GAME OVER", (255, 80, 80))
        blit_wrapped("Press R to restart", (255, 200, 200))


# ---------- Game frame drawing ----------

def draw_game_frame(screen: pygame.Surface,
                    cfg: GameConfig,
                    state: GameState,
                    view: ViewSettings,
                    fonts: GfxFonts) -> None:
    """Single call to draw the whole game frame."""
    screen.fill(BG_COLOR)
    board_offset, panel_offset = compute_game_layout(screen, cfg, view)
    # Draw game board
    draw_board(screen, state, cfg, board_offset, view)

    # Draw board outline in 3D using projected bbox
    if view.projection != ProjectionMode.TOP_DOWN:
        bx, by, bw, bh = _compute_board_bbox_3d(cfg, view, board_offset)
        pygame.draw.rect(screen, BORDER_COLOR, pygame.Rect(bx, by, bw, bh), 2)

    # Draw side panel contents
    draw_side_panel(screen, state, cfg, view, panel_offset, fonts)

    # Draw side panel outline (fixed at top-right)
    window_w, window_h = screen.get_size()
    px, py = panel_offset
    panel_rect = pygame.Rect(px, MARGIN, view.panel_width, max(10, window_h - 2 * MARGIN))
    pygame.draw.rect(screen, BORDER_COLOR, panel_rect, 2)


# ---------- Test/metrics helpers ----------

def compute_min_gap_pixels(surface: pygame.Surface,
                           cfg: GameConfig,
                           state: GameState,
                           view: ViewSettings) -> int:
    """
    Approximate minimal pixel distance between projected top-face footprints
    of any two occupied cells in the current view. Returns integer pixels.
    Uses AABBs of top faces for efficiency. Overlap/touch returns 0.
    """
    # Compute layout to get board_offset
    board_offset, _ = compute_game_layout(surface, cfg, view)
    ox, oy = board_offset
    s = view.cell_size

    # Collect occupied logical cells (locked + active piece)
    occupied = []
    for (x, y), _cid in state.board.cells.items():
        if 0 <= x < cfg.width and 0 <= y < cfg.height:
            occupied.append((x, y))
    if state.current_piece is not None:
        for (x, y) in state.current_piece.cells():
            if 0 <= x < cfg.width and 0 <= y < cfg.height:
                occupied.append((x, y))

    if len(occupied) < 2:
        return 0

    rects: list[Tuple[float, float, float, float]] = []  # (x0,y0,x1,y1)

    if view.projection == ProjectionMode.TOP_DOWN:
        for (x, y) in occupied:
            x0 = ox + x * s + 1
            y0 = oy + y * s + 1
            x1 = x0 + (s - 2)
            y1 = y0 + (s - 2)
            rects.append((x0, y0, x1, y1))
    else:
        # 3D: project top face vertices for each cell
        h = max(0.0, view.extrude_factor)

        # Precompute rotation and projection params (same as _draw_persp_cell)
        yaw = math.radians(view.yaw_deg)
        pitch = math.radians(view.pitch_deg)
        roll = math.radians(view.roll_deg)
        cz, sz = math.cos(yaw), math.sin(yaw)
        cx, sx_ = math.cos(pitch), math.sin(pitch)
        cy, sy_ = math.cos(roll), math.sin(roll)
        r00, r01, r02 = cz, -sz, 0.0
        r10, r11, r12 = sz,  cz, 0.0
        r20, r21, r22 = 0.0, 0.0, 1.0
        t00 = r00
        t01 = r01
        t02 = r02
        t10 = cx * r10 - sx_ * r20
        t11 = cx * r11 - sx_ * r21
        t12 = cx * r12 - sx_ * r22
        t20 = sx_ * r10 + cx * r20
        t21 = sx_ * r11 + cx * r21
        t22 = sx_ * r12 + cx * r22
        R00 =  cy * t00 + sy_ * t02
        R01 =  cy * t01 + sy_ * t12
        R02 =  cy * t02 + sy_ * t22
        R10 =  t10
        R11 =  t11
        R12 =  t12
        R20 = -sy_ * t00 + cy * t02
        R21 = -sy_ * t01 + cy * t12
        R22 = -sy_ * t02 + cy * t22

        fov = max(10.0, min(150.0, view.fov_deg))
        f = 1.0 / math.tan(math.radians(fov) * 0.5)
        cam_dist = max(0.5, view.cam_dist)

        # Translate by board center and camera translations
        cx_b = getattr(view, '_board_cx', cfg.width * 0.5)
        cy_b = getattr(view, '_board_cy', cfg.height * 0.5)

        def proj(wx: float, wy: float, wz: float) -> Tuple[float, float]:
            wx = wx - cx_b - getattr(view, 'cam_tx', 0.0)
            wy = wy - cy_b - getattr(view, 'cam_ty', 0.0)
            wz = wz - getattr(view, 'cam_tz', 0.0)
            rx = R00 * wx + R01 * wy + R02 * wz
            ry = R10 * wx + R11 * wy + R12 * wz
            rz = R20 * wx + R21 * wy + R22 * wz
            zc = max(0.1, rz + cam_dist)
            px = ox + s * f * (rx / zc)
            py = oy + s * f * (-ry / zc)
            return px, py

        for (x, y) in occupied:
            # top face vertices 4,5,6,7 from _draw_persp_cell order
            verts = [
                (x + 0.0, y + 0.0, h),
                (x + 1.0, y + 0.0, h),
                (x + 1.0, y + 1.0, h),
                (x + 0.0, y + 1.0, h),
            ]
            pts = [proj(wx, wy, wz) for (wx, wy, wz) in verts]
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            rects.append((min(xs), min(ys), max(xs), max(ys)))

    # Compute minimal distance between all rectangle pairs
    min_d = float('inf')
    n = len(rects)
    for i in range(n):
        ax0, ay0, ax1, ay1 = rects[i]
        for j in range(i + 1, n):
            bx0, by0, bx1, by1 = rects[j]
            dx = 0.0
            if ax1 < bx0:
                dx = bx0 - ax1
            elif bx1 < ax0:
                dx = ax0 - bx1
            else:
                dx = 0.0
            dy = 0.0
            if ay1 < by0:
                dy = by0 - ay1
            elif by1 < ay0:
                dy = ay0 - by1
            else:
                dy = 0.0
            d = sqrt(dx * dx + dy * dy)
            if d < min_d:
                min_d = d

    if min_d == float('inf'):
        return 0
    return int(round(min_d))


def compute_grid_distance_2d_3d(surface: pygame.Surface,
                                cfg: GameConfig,
                                state: GameState,
                                view: ViewSettings) -> Tuple[float, float]:
    """
    Compute RMS and max pixel displacement between 2D and current 3D projections
    of the top-face centroids for all occupied cells (locked + active).
    Returns (rms_px, max_px). If fewer than 1 occupied, returns (0,0).
    """
    # Layout and basic params
    board_offset_3d, _ = compute_game_layout(surface, cfg, view)
    ox3, oy3 = board_offset_3d
    # Build a 2D view clone for 2D centroids
    from copy import deepcopy
    v2d = deepcopy(view)
    v2d.projection = ProjectionMode.TOP_DOWN
    board_offset_2d, _ = compute_game_layout(surface, cfg, v2d)
    ox2, oy2 = board_offset_2d
    s = view.cell_size

    # Occupied cells
    occ: list[Tuple[int, int]] = []
    for (x, y), _cid in state.board.cells.items():
        if 0 <= x < cfg.width and 0 <= y < cfg.height:
            occ.append((x, y))
    if state.current_piece is not None:
        for (x, y) in state.current_piece.cells():
            if 0 <= x < cfg.width and 0 <= y < cfg.height:
                occ.append((x, y))

    if not occ:
        return (0.0, 0.0)

    # Precompute 3D projection params (same as elsewhere), including board center & cam translations
    yaw = math.radians(view.yaw_deg)
    pitch = math.radians(view.pitch_deg)
    roll = math.radians(view.roll_deg)
    cz, sz = math.cos(yaw), math.sin(yaw)
    cx, sx_ = math.cos(pitch), math.sin(pitch)
    cy, sy_ = math.cos(roll), math.sin(roll)
    r00, r01, r02 = cz, -sz, 0.0
    r10, r11, r12 = sz,  cz, 0.0
    r20, r21, r22 = 0.0, 0.0, 1.0
    t00 = r00
    t01 = r01
    t02 = r02
    t10 = cx * r10 - sx_ * r20
    t11 = cx * r11 - sx_ * r21
    t12 = cx * r12 - sx_ * r22
    t20 = sx_ * r10 + cx * r20
    t21 = sx_ * r11 + cx * r21
    t22 = sx_ * r12 + cx * r22
    R00 =  cy * t00 + sy_ * t02
    R01 =  cy * t01 + sy_ * t12
    R02 =  cy * t02 + sy_ * t22
    R10 =  t10
    R11 =  t11
    R12 =  t12
    R20 = -sy_ * t00 + cy * t02
    R21 = -sy_ * t01 + cy * t12
    R22 = -sy_ * t02 + cy * t22
    if getattr(view, 'focal_dist', 0.0) and view.focal_dist > 0.0:
        f = max(0.01, float(view.focal_dist))
    else:
        fov = max(10.0, min(150.0, view.fov_deg))
        f = 1.0 / math.tan(math.radians(fov) * 0.5)
    cam_dist = max(0.5, view.cam_dist)
    cx_b = getattr(view, '_board_cx', cfg.width * 0.5)
    cy_b = getattr(view, '_board_cy', cfg.height * 0.5)
    h = max(0.0, view.extrude_factor)

    def proj3d_center(x: int, y: int) -> Tuple[float, float]:
        wx = (x + 0.5) - cx_b - getattr(view, 'cam_tx', 0.0)
        wy = (y + 0.5) - cy_b - getattr(view, 'cam_ty', 0.0)
        wz = (h) - getattr(view, 'cam_tz', 0.0)  # top face centroid at z=h
        rx = R00 * wx + R01 * wy + R02 * wz
        ry = R10 * wx + R11 * wy + R12 * wz
        rz = R20 * wx + R21 * wy + R22 * wz
        zc = max(0.1, rz + cam_dist)
        px = ox3 + s * f * (rx / zc)
        py = oy3 + s * f * (-ry / zc)
        return px, py

    # Accumulate distances
    import math as _m
    sum_sq = 0.0
    max_d = 0.0
    n = 0
    for (x, y) in occ:
        c2x = ox2 + x * s + 0.5 * s
        c2y = oy2 + y * s + 0.5 * s
        c3x, c3y = proj3d_center(x, y)
        dx = c3x - c2x
        dy = c3y - c2y
        d = _m.hypot(dx, dy)
        sum_sq += d * d
        if d > max_d:
            max_d = d
        n += 1
    if n == 0:
        return (0.0, 0.0)
    rms = (sum_sq / n) ** 0.5
    return (rms, max_d)
