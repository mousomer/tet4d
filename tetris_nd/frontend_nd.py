# tetris_nd/frontend_nd.py
import sys
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple

import pygame

from .board import BoardND
from .game_nd import GameConfigND, GameStateND
from .keybindings import (
    CONTROL_LINES_ND_3D,
    CONTROL_LINES_ND_4D,
    KEYS_3D,
    KEYS_4D,
    SLICE_KEYS_3D,
    SLICE_KEYS_4D,
    SYSTEM_KEYS,
    key_matches,
)
from .menu_keybinding_shortcuts import (
    apply_menu_binding_action,
    menu_binding_action_for_key,
    menu_binding_hint_line,
    menu_binding_status_color,
)


CELL_SIZE = 28
MARGIN = 20
SIDE_PANEL = 340

BG_COLOR = (10, 10, 30)
GRID_COLOR = (40, 40, 80)
TEXT_COLOR = (230, 230, 230)
HIGHLIGHT_COLOR = (255, 215, 0)

COLOR_MAP = {
    1: (0, 255, 255),
    2: (255, 255, 0),
    3: (160, 0, 240),
    4: (0, 255, 0),
    5: (255, 0, 0),
    6: (0, 0, 255),
    7: (255, 165, 0),
}

AXIS_NAMES = ["x", "y", "z", "w", "v", "u", "t", "s"]


def axis_name(axis: int) -> str:
    if 0 <= axis < len(AXIS_NAMES):
        return AXIS_NAMES[axis]
    return f"a{axis}"


def color_for_cell(cell_id: int) -> Tuple[int, int, int]:
    if cell_id <= 0:
        return (0, 0, 0)
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
class GameSettingsND:
    width: int = 10
    height: int = 20
    depth: int = 6
    fourth: int = 4
    speed_level: int = 1


class MenuAction(Enum):
    QUIT = auto()
    START_GAME = auto()
    SELECT_UP = auto()
    SELECT_DOWN = auto()
    VALUE_LEFT = auto()
    VALUE_RIGHT = auto()
    LOAD_BINDINGS = auto()
    SAVE_BINDINGS = auto()
    NO_OP = auto()


@dataclass
class MenuState:
    settings: GameSettingsND = field(default_factory=GameSettingsND)
    selected_index: int = 0
    running: bool = True
    start_game: bool = False
    bindings_status: str = ""
    bindings_status_error: bool = False


FieldSpec = Tuple[str, str, int, int]


def menu_fields_for_dimension(dimension: int) -> List[FieldSpec]:
    fields: List[FieldSpec] = [
        ("Board width", "width", 6, 16),
        ("Board height", "height", 12, 30),
    ]
    if dimension >= 3:
        fields.append(("Board depth (z)", "depth", 4, 12))
    if dimension >= 4:
        fields.append(("Board axis w", "fourth", 3, 10))
    fields.append(("Speed level", "speed_level", 1, 10))
    return fields


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
            else:
                binding_action = menu_binding_action_for_key(
                    event.key, MenuAction.LOAD_BINDINGS, MenuAction.SAVE_BINDINGS
                )
                if binding_action is not None:
                    actions.append(binding_action)
    if not actions:
        actions.append(MenuAction.NO_OP)
    return actions


def apply_menu_actions(state: MenuState,
                       actions: List[MenuAction],
                       dimension: int) -> None:
    fields = menu_fields_for_dimension(dimension)
    num_fields = len(fields)

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
            state.selected_index = (state.selected_index - 1) % num_fields
            continue

        if action == MenuAction.SELECT_DOWN:
            state.selected_index = (state.selected_index + 1) % num_fields
            continue

        if action not in (MenuAction.VALUE_LEFT, MenuAction.VALUE_RIGHT):
            apply_menu_binding_action(
                action, MenuAction.LOAD_BINDINGS, MenuAction.SAVE_BINDINGS, dimension, state
            )
            continue

        label, attr_name, min_val, max_val = fields[state.selected_index]
        del label
        current_val = getattr(state.settings, attr_name)
        if action == MenuAction.VALUE_LEFT:
            current_val -= 1
        else:
            current_val += 1
        current_val = max(min_val, min(max_val, current_val))
        setattr(state.settings, attr_name, current_val)


def draw_menu(screen: pygame.Surface,
              fonts: GfxFonts,
              state: MenuState,
              dimension: int) -> None:
    draw_gradient_background(screen, (15, 15, 60), (2, 2, 20))
    width, _ = screen.get_size()
    fields = menu_fields_for_dimension(dimension)

    title_text = f"{dimension}D Tetris – Setup"
    subtitle_text = "Use Up/Down to select, Left/Right to change, Enter to start."

    title_surf = fonts.title_font.render(title_text, True, TEXT_COLOR)
    subtitle_surf = fonts.hint_font.render(subtitle_text, True, (200, 200, 220))

    title_x = (width - title_surf.get_width()) // 2
    screen.blit(title_surf, (title_x, 60))
    subtitle_x = (width - subtitle_surf.get_width()) // 2
    screen.blit(subtitle_surf, (subtitle_x, 108))

    panel_w = int(width * 0.65)
    panel_h = 90 + len(fields) * 44
    panel_x = (width - panel_w) // 2
    panel_y = 160

    panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel_surf, (0, 0, 0, 140),
                     panel_surf.get_rect(), border_radius=16)
    screen.blit(panel_surf, (panel_x, panel_y))

    y = panel_y + 28
    for idx, (label, attr_name, _, _) in enumerate(fields):
        value = getattr(state.settings, attr_name)
        text = f"{label}: {value}"
        selected = (idx == state.selected_index)
        txt_color = HIGHLIGHT_COLOR if selected else TEXT_COLOR
        text_surf = fonts.menu_font.render(text, True, txt_color)
        text_rect = text_surf.get_rect(topleft=(panel_x + 36, y))
        if selected:
            highlight_rect = text_rect.inflate(20, 10)
            highlight_surf = pygame.Surface(highlight_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(highlight_surf, (255, 255, 255, 40),
                             highlight_surf.get_rect(), border_radius=10)
            screen.blit(highlight_surf, highlight_rect.topleft)
        screen.blit(text_surf, text_rect.topleft)
        y += 44

    hint_lines = [
        "Esc = quit",
        menu_binding_hint_line(dimension),
        "Controls are shown in-game on the side panel.",
    ]
    hint_y = panel_y + panel_h + 24
    for line in hint_lines:
        surf = fonts.hint_font.render(line, True, (210, 210, 230))
        hint_x = (width - surf.get_width()) // 2
        screen.blit(surf, (hint_x, hint_y))
        hint_y += surf.get_height() + 4

    if state.bindings_status:
        status_color = menu_binding_status_color(state.bindings_status_error)
        status_surf = fonts.hint_font.render(state.bindings_status, True, status_color)
        status_x = (width - status_surf.get_width()) // 2
        screen.blit(status_surf, (status_x, hint_y))


def run_menu(screen: pygame.Surface,
             fonts: GfxFonts,
             dimension: int) -> Optional[GameSettingsND]:
    clock = pygame.time.Clock()
    state = MenuState()

    while state.running and not state.start_game:
        _dt = clock.tick(60)
        actions = gather_menu_actions()
        apply_menu_actions(state, actions, dimension)
        draw_menu(screen, fonts, state, dimension)
        pygame.display.flip()

    if state.start_game and state.running:
        return state.settings
    return None


def build_config(settings: GameSettingsND, dimension: int) -> GameConfigND:
    dims = [settings.width, settings.height]
    if dimension >= 3:
        dims.append(settings.depth)
    if dimension >= 4:
        dims.append(settings.fourth)
    return GameConfigND(
        dims=tuple(dims),
        gravity_axis=1,
        speed_level=settings.speed_level,
    )


def gravity_interval_ms_from_config(cfg: GameConfigND) -> int:
    base_ms = 1000
    interval = base_ms // max(1, min(10, cfg.speed_level))
    return max(80, interval)


def create_initial_state(cfg: GameConfigND) -> GameStateND:
    board = BoardND(cfg.dims)
    return GameStateND(config=cfg, board=board)


@dataclass
class SliceState:
    axis_values: Dict[int, int] = field(default_factory=dict)


def create_initial_slice_state(cfg: GameConfigND) -> SliceState:
    values: Dict[int, int] = {}
    for axis, size in enumerate(cfg.dims):
        if axis in (0, cfg.gravity_axis):
            continue
        values[axis] = size // 2
    return SliceState(axis_values=values)


def coord_visible_in_slice(coord: Tuple[int, ...], slice_state: SliceState) -> bool:
    for axis, value in slice_state.axis_values.items():
        if coord[axis] != value:
            return False
    return True


def adjust_slice_axis(slice_state: SliceState,
                      cfg: GameConfigND,
                      axis: int,
                      delta: int) -> None:
    if axis not in slice_state.axis_values:
        return
    size = cfg.dims[axis]
    curr = slice_state.axis_values[axis]
    curr = max(0, min(size - 1, curr + delta))
    slice_state.axis_values[axis] = curr


def _draw_cell(surface: pygame.Surface,
               x: int,
               y: int,
               cell_id: int,
               board_offset: Tuple[int, int],
               outline: bool = False) -> None:
    ox, oy = board_offset
    rect = pygame.Rect(
        ox + x * CELL_SIZE + 1,
        oy + y * CELL_SIZE + 1,
        CELL_SIZE - 2,
        CELL_SIZE - 2,
    )
    pygame.draw.rect(surface, color_for_cell(cell_id), rect)
    if outline:
        pygame.draw.rect(surface, (255, 255, 255), rect, 2)


def compute_game_layout(screen: pygame.Surface,
                        cfg: GameConfigND) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    window_w, window_h = screen.get_size()
    board_px_w = cfg.dims[0] * CELL_SIZE
    board_px_h = cfg.dims[cfg.gravity_axis] * CELL_SIZE

    board_x = max(MARGIN, (window_w - SIDE_PANEL - board_px_w) // 2)
    board_y = max(MARGIN, (window_h - board_px_h) // 2)
    board_offset = (board_x, board_y)
    panel_offset = (board_x + board_px_w + MARGIN, board_y)
    return board_offset, panel_offset


def draw_board(surface: pygame.Surface,
               state: GameStateND,
               slice_state: SliceState,
               board_offset: Tuple[int, int]) -> None:
    cfg = state.config
    w = cfg.dims[0]
    h = cfg.dims[cfg.gravity_axis]
    ox, oy = board_offset

    board_rect = pygame.Rect(ox, oy, w * CELL_SIZE, h * CELL_SIZE)
    pygame.draw.rect(surface, (20, 20, 50), board_rect)

    for gx in range(w + 1):
        x_px = ox + gx * CELL_SIZE
        pygame.draw.line(surface, GRID_COLOR, (x_px, oy), (x_px, oy + h * CELL_SIZE))
    for gy in range(h + 1):
        y_px = oy + gy * CELL_SIZE
        pygame.draw.line(surface, GRID_COLOR, (ox, y_px), (ox + w * CELL_SIZE, y_px))

    for coord, cell_id in state.board.cells.items():
        x = coord[0]
        y = coord[cfg.gravity_axis]
        if 0 <= x < w and 0 <= y < h and coord_visible_in_slice(coord, slice_state):
            _draw_cell(surface, x, y, cell_id, board_offset)

    if state.current_piece is not None:
        color_id = state.current_piece.shape.color_id
        for coord in state.current_piece.cells():
            x = coord[0]
            y = coord[cfg.gravity_axis]
            if (
                0 <= x < w
                and 0 <= y < h
                and coord_visible_in_slice(coord, slice_state)
            ):
                _draw_cell(surface, x, y, color_id, board_offset, outline=True)


def control_lines_for_dimension(dimension: int) -> List[str]:
    if dimension >= 4:
        return list(CONTROL_LINES_ND_4D)
    if dimension == 3:
        return list(CONTROL_LINES_ND_3D)
    return [
        "Controls:",
        " Left/Right : move x",
        " Down       : soft drop",
        " Space      : hard drop",
        " Up/X       : rotate x-y +",
        " Z          : rotate x-y -",
        " R          : restart",
        " M          : menu",
        " Esc        : quit",
    ]


def draw_side_panel(surface: pygame.Surface,
                    state: GameStateND,
                    slice_state: SliceState,
                    panel_offset: Tuple[int, int],
                    fonts: GfxFonts) -> None:
    cfg = state.config
    px, py = panel_offset
    gravity_ms = gravity_interval_ms_from_config(cfg)
    rows_per_sec = 1000.0 / gravity_ms if gravity_ms > 0 else 0.0

    lines = [
        f"{cfg.ndim}D Tetris",
        "",
        f"Dims: {cfg.dims}",
        f"Gravity axis: {axis_name(cfg.gravity_axis)}",
        f"Score: {state.score}",
        f"Cleared: {state.lines_cleared}",
        f"Speed level: {cfg.speed_level}",
        f"Fall: {rows_per_sec:.2f} / sec",
        "",
        "Active slice:",
    ]
    for axis, value in sorted(slice_state.axis_values.items()):
        lines.append(f" {axis_name(axis)} = {value} / {cfg.dims[axis] - 1}")
    lines.append("")
    lines.extend(control_lines_for_dimension(cfg.ndim))

    y = py
    for line in lines:
        surf = fonts.panel_font.render(line, True, TEXT_COLOR)
        surface.blit(surf, (px, y))
        y += surf.get_height() + 3

    if state.game_over:
        y += 8
        over = fonts.panel_font.render("GAME OVER", True, (255, 80, 80))
        surface.blit(over, (px, y))
        y += over.get_height() + 3
        hint = fonts.panel_font.render("Press R to restart", True, (255, 200, 200))
        surface.blit(hint, (px, y))


def draw_game_frame(screen: pygame.Surface,
                    state: GameStateND,
                    slice_state: SliceState,
                    fonts: GfxFonts) -> None:
    screen.fill(BG_COLOR)
    board_offset, panel_offset = compute_game_layout(screen, state.config)
    draw_board(screen, state, slice_state, board_offset)
    draw_side_panel(screen, state, slice_state, panel_offset, fonts)


def handle_game_keydown(event: pygame.event.Event,
                        state: GameStateND,
                        slice_state: SliceState) -> str:
    cfg = state.config
    ndim = cfg.ndim
    key = event.key

    if key_matches(SYSTEM_KEYS, "quit", key):
        return "quit"
    if key_matches(SYSTEM_KEYS, "menu", key):
        return "menu"
    if key_matches(SYSTEM_KEYS, "restart", key):
        return "restart"

    if ndim >= 3:
        if key_matches(SLICE_KEYS_3D, "slice_z_neg", key):
            adjust_slice_axis(slice_state, cfg, axis=2, delta=-1)
            return "continue"
        if key_matches(SLICE_KEYS_3D, "slice_z_pos", key):
            adjust_slice_axis(slice_state, cfg, axis=2, delta=1)
            return "continue"
    if ndim >= 4:
        if key_matches(SLICE_KEYS_4D, "slice_w_neg", key):
            adjust_slice_axis(slice_state, cfg, axis=3, delta=-1)
            return "continue"
        if key_matches(SLICE_KEYS_4D, "slice_w_pos", key):
            adjust_slice_axis(slice_state, cfg, axis=3, delta=1)
            return "continue"

    if state.game_over:
        return "continue"

    if ndim >= 4:
        gameplay_keys = KEYS_4D
    else:
        gameplay_keys = KEYS_3D

    if key_matches(gameplay_keys, "move_x_neg", key):
        state.try_move_axis(0, -1)
        return "continue"
    if key_matches(gameplay_keys, "move_x_pos", key):
        state.try_move_axis(0, 1)
        return "continue"
    if key_matches(gameplay_keys, "soft_drop", key):
        state.try_move_axis(cfg.gravity_axis, 1)
        return "continue"
    if key_matches(gameplay_keys, "hard_drop", key):
        state.hard_drop()
        return "continue"
    if key_matches(gameplay_keys, "rotate_xy_pos", key):
        state.try_rotate(0, cfg.gravity_axis, 1)
        return "continue"
    if key_matches(gameplay_keys, "rotate_xy_neg", key):
        state.try_rotate(0, cfg.gravity_axis, -1)
        return "continue"

    if ndim >= 3:
        if key_matches(gameplay_keys, "move_z_neg", key):
            state.try_move_axis(2, -1)
            return "continue"
        if key_matches(gameplay_keys, "move_z_pos", key):
            state.try_move_axis(2, 1)
            return "continue"
        if key_matches(gameplay_keys, "rotate_xz_pos", key):
            state.try_rotate(0, 2, 1)
            return "continue"
        if key_matches(gameplay_keys, "rotate_xz_neg", key):
            state.try_rotate(0, 2, -1)
            return "continue"
        if key_matches(gameplay_keys, "rotate_yz_pos", key):
            state.try_rotate(cfg.gravity_axis, 2, 1)
            return "continue"
        if key_matches(gameplay_keys, "rotate_yz_neg", key):
            state.try_rotate(cfg.gravity_axis, 2, -1)
            return "continue"

    if ndim >= 4:
        if key_matches(gameplay_keys, "move_w_neg", key):
            state.try_move_axis(3, -1)
            return "continue"
        if key_matches(gameplay_keys, "move_w_pos", key):
            state.try_move_axis(3, 1)
            return "continue"
        if key_matches(gameplay_keys, "rotate_xw_pos", key):
            state.try_rotate(0, 3, 1)
            return "continue"
        if key_matches(gameplay_keys, "rotate_xw_neg", key):
            state.try_rotate(0, 3, -1)
            return "continue"
        if key_matches(gameplay_keys, "rotate_yw_pos", key):
            state.try_rotate(cfg.gravity_axis, 3, 1)
            return "continue"
        if key_matches(gameplay_keys, "rotate_yw_neg", key):
            state.try_rotate(cfg.gravity_axis, 3, -1)
            return "continue"
        if key_matches(gameplay_keys, "rotate_zw_pos", key):
            state.try_rotate(2, 3, 1)
            return "continue"
        if key_matches(gameplay_keys, "rotate_zw_neg", key):
            state.try_rotate(2, 3, -1)
            return "continue"

    return "continue"


def run_game_loop(screen: pygame.Surface,
                  cfg: GameConfigND,
                  fonts: GfxFonts) -> bool:
    state = create_initial_state(cfg)
    slice_state = create_initial_slice_state(cfg)
    gravity_interval_ms = gravity_interval_ms_from_config(cfg)
    gravity_accumulator = 0
    clock = pygame.time.Clock()

    while True:
        dt = clock.tick(60)
        gravity_accumulator += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
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

        draw_game_frame(screen, state, slice_state, fonts)
        pygame.display.flip()


def suggested_window_size(cfg: GameConfigND) -> Tuple[int, int]:
    board_px_w = cfg.dims[0] * CELL_SIZE
    board_px_h = cfg.dims[cfg.gravity_axis] * CELL_SIZE
    window_w = board_px_w + SIDE_PANEL + 3 * MARGIN
    window_h = board_px_h + 2 * MARGIN
    return max(window_w, 900), max(window_h, 640)


def run_dimension(dimension: int) -> None:
    if dimension not in (3, 4):
        raise ValueError("dimension must be 3 or 4")

    pygame.init()
    fonts = init_fonts()

    running = True
    while running:
        pygame.display.set_caption(f"{dimension}D Tetris – Setup")
        menu_screen = pygame.display.set_mode((900, 680), pygame.RESIZABLE)
        settings = run_menu(menu_screen, fonts, dimension)
        if settings is None:
            break

        cfg = build_config(settings, dimension)
        win_w, win_h = suggested_window_size(cfg)
        pygame.display.set_caption(f"{dimension}D Tetris")
        game_screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)

        back_to_menu = run_game_loop(game_screen, cfg, fonts)
        if not back_to_menu:
            running = False

    pygame.quit()
    sys.exit()
