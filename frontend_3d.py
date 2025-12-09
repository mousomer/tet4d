# tetris_nd/frontend_pygame.py

import sys
import random
from dataclasses import dataclass, field
from typing import Optional, List, Callable
from enum import Enum, auto

import pygame

from tetris_nd.board import BoardND
from tetris_nd.game2d import GameConfig, GameState, Action
from tetris_nd.fx_game_3d import (
    GfxFonts,
    init_fonts,
    draw_menu,
    draw_game_frame,
    gravity_interval_ms_from_config,
    ViewSettings,
    ProjectionMode,
)


# ---------- Menu state & actions (logic, not drawing) ----------

@dataclass
class GameSettings:
    width: int = 10
    height: int = 20
    speed_level: int = 3  # 1..10, mapped to gravity interval (default 3)


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
    settings: GameSettings = field(default_factory=GameSettings)
    selected_index: int = 0  # 0=width, 1=height, 2=speed
    running: bool = True
    start_game: bool = False


# ---------- Menu logic helpers ----------

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

        elif action == MenuAction.START_GAME:
            state.start_game = True

        elif action == MenuAction.SELECT_UP:
            state.selected_index = (state.selected_index - 1) % 3

        elif action == MenuAction.SELECT_DOWN:
            state.selected_index = (state.selected_index + 1) % 3

        elif action == MenuAction.VALUE_LEFT:
            if state.selected_index == 0:
                state.settings.width = max(6, state.settings.width - 1)
            elif state.selected_index == 1:
                state.settings.height = max(12, state.settings.height - 1)
            elif state.selected_index == 2:
                state.settings.speed_level = max(1, state.settings.speed_level - 1)

        elif action == MenuAction.VALUE_RIGHT:
            if state.selected_index == 0:
                state.settings.width = min(16, state.settings.width + 1)
            elif state.selected_index == 1:
                state.settings.height = min(30, state.settings.height + 1)
            elif state.selected_index == 2:
                state.settings.speed_level = min(10, state.settings.speed_level + 1)


# ---------- Menu loop ----------

def run_menu(screen: pygame.Surface, fonts: GfxFonts) -> Optional[GameSettings]:
    """
    Intro screen where width, height, and speed_level can be set.
    Returns GameSettings if user starts the game, or None if user quits.
    """
    clock = pygame.time.Clock()
    state = MenuState()

    while state.running and not state.start_game:
        _dt = clock.tick(60)
        actions = gather_menu_actions()
        apply_menu_actions(state, actions)
        draw_menu(screen, fonts, state.settings, state.selected_index)
        pygame.display.flip()

    if state.start_game and state.running:
        return state.settings
    return None


# ---------- Game loop context & helpers ----------

@dataclass
class GameLoopContext:
    screen: pygame.Surface
    cfg: GameConfig
    fonts: GfxFonts
    view: ViewSettings
    state: GameState
    gravity_interval_ms: int
    gravity_accumulator: int = 0
    dt: int = 0
    exit_to_menu: bool = False
    exit_program: bool = False
    # UI interaction
    resizing_panel: bool = False
    resize_grip_active: bool = False
    mouse_down: bool = False


def create_initial_state(cfg: GameConfig) -> GameState:
    board = BoardND((cfg.width, cfg.height))
    return GameState(config=cfg, board=board)


def handle_game_keydown(event: pygame.event.Event,
                        ctx: GameLoopContext) -> bool:
    """
    Handle a single KEYDOWN event related to game logic (not view).
    Returns True if the event was consumed.
    """
    state = ctx.state
    cfg = ctx.cfg

    if event.key == pygame.K_ESCAPE:
        ctx.exit_program = True
        return True

    if event.key == pygame.K_m:
        ctx.exit_to_menu = True
        return True

    if event.key == pygame.K_r:
        # Restart game with same config
        new_state = create_initial_state(cfg)
        state.board = new_state.board
        state.current_piece = new_state.current_piece
        state.next_bag = new_state.next_bag
        state.rng = new_state.rng
        state.score = 0
        state.lines_cleared = 0
        state.game_over = False
        return True

    if state.game_over:
        # Don't react to movement keys when game over
        return True

    # Movement / rotation / drops
    if event.key == pygame.K_LEFT:
        state.try_move(-1, 0)
        return True
    if event.key == pygame.K_RIGHT:
        state.try_move(1, 0)
        return True
    if event.key == pygame.K_UP or event.key == pygame.K_x:
        state.try_rotate(+1)
        return True
    if event.key == pygame.K_z:
        state.try_rotate(-1)
        return True
    if event.key == pygame.K_SPACE:
        state.hard_drop()
        return True
    if event.key == pygame.K_DOWN:
        state.try_move(0, 1)
        return True

    return False


def handle_view_keydown(event: pygame.event.Event,
                        ctx: GameLoopContext) -> bool:
    """
    Handle key presses that only affect the view (projection / zoom).
    Returns True if the event was consumed.
    """
    view = ctx.view

    if event.key == pygame.K_v:
        # Toggle projection mode
        if view.projection == ProjectionMode.TOP_DOWN:
            # Enter 3D but mimic 2D by default; keep instructions unchanged.
            view.projection = ProjectionMode.ISOMETRIC
            view.yaw_deg = 0.0
            view.pitch_deg = 89.0
            view.roll_deg = 0.0
            view.fov_deg = 60.0
            view.extrude_factor = 0.0
            view.cam_dist = 12.0
            view.pan_px_x = 0.0
            view.pan_px_y = 0.0
            view.auto_fit_3d = True
        else:
            view.projection = ProjectionMode.TOP_DOWN
        return True

    # Zoom out
    if event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
        view.cell_size = max(12, view.cell_size - 2)
        return True

    # Zoom in (both + and = often map here)
    if event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
        view.cell_size = min(64, view.cell_size + 2)
        return True

    # 3D projective camera parameters (when in ISOMETRIC/3D mode)
    # Yaw (J/L)
    if event.key == pygame.K_j:
        view.yaw_deg = (view.yaw_deg - 5.0) % 360.0
        view.projection = ProjectionMode.ISOMETRIC
        return True
    if event.key == pygame.K_l:
        view.yaw_deg = (view.yaw_deg + 5.0) % 360.0
        view.projection = ProjectionMode.ISOMETRIC
        return True

    # Pitch (I/K)
    if event.key == pygame.K_i:
        view.pitch_deg = max(-89.0, min(89.0, view.pitch_deg + 5.0))
        view.projection = ProjectionMode.ISOMETRIC
        return True
    if event.key == pygame.K_k:
        view.pitch_deg = max(-89.0, min(89.0, view.pitch_deg - 5.0))
        view.projection = ProjectionMode.ISOMETRIC
        return True

    # Roll (U/O)
    if event.key == pygame.K_u:
        view.roll_deg = (view.roll_deg - 5.0) % 360.0
        view.projection = ProjectionMode.ISOMETRIC
        return True
    if event.key == pygame.K_o:
        view.roll_deg = (view.roll_deg + 5.0) % 360.0
        view.projection = ProjectionMode.ISOMETRIC
        return True

    # FOV ([ and ])
    if event.key == pygame.K_LEFTBRACKET:
        view.fov_deg = max(20.0, view.fov_deg - 5.0)
        view.projection = ProjectionMode.ISOMETRIC
        return True
    if event.key == pygame.K_RIGHTBRACKET:
        view.fov_deg = min(120.0, view.fov_deg + 5.0)
        view.projection = ProjectionMode.ISOMETRIC
        return True

    # Extrusion height (, and .)
    if event.key == pygame.K_COMMA:
        view.extrude_factor = max(0.0, view.extrude_factor - 0.05)
        return True
    if event.key == pygame.K_PERIOD:
        view.extrude_factor = min(1.5, view.extrude_factor + 0.05)
        return True

    # Reset preset (0 key): pleasant 3D preset
    if event.key in (pygame.K_0, pygame.K_KP0):
        view.yaw_deg = 35.0
        view.pitch_deg = 25.0
        view.roll_deg = 0.0
        view.fov_deg = 60.0
        view.extrude_factor = 0.6
        view.cam_dist = 6.0
        view.pan_px_x = 0.0
        view.pan_px_y = 0.0
        view.auto_fit_3d = True
        view.projection = ProjectionMode.ISOMETRIC
        return True

    # Camera distance (Q/E)
    if event.key == pygame.K_q:
        view.cam_dist = max(0.5, view.cam_dist - 0.5)
        view.projection = ProjectionMode.ISOMETRIC
        return True
    if event.key == pygame.K_e:
        view.cam_dist = min(20.0, view.cam_dist + 0.5)
        view.projection = ProjectionMode.ISOMETRIC
        return True

    # Pan (WASD)
    if event.key == pygame.K_a:
        view.pan_px_x -= 20
        return True
    if event.key == pygame.K_d:
        view.pan_px_x += 20
        return True
    if event.key == pygame.K_w:
        view.pan_px_y -= 20
        return True
    if event.key == pygame.K_s:
        view.pan_px_y += 20
        return True

    # Test mode toggle (T) and repopulate (Y)
    if event.key == pygame.K_t:
        view.test_mode = not getattr(view, 'test_mode', False)
        if view.test_mode:
            populate_random_grid(ctx, density=0.6)
        else:
            # When leaving test mode, clear board and restart game state
            new_state = create_initial_state(ctx.cfg)
            ctx.state = new_state
        return True

    if event.key == pygame.K_y:
        if getattr(view, 'test_mode', False):
            populate_random_grid(ctx, density=0.6)
            return True

    return False


def handle_mouse_events(event: pygame.event.Event, ctx: GameLoopContext) -> bool:
    """Handle mouse events for panel resizing and potential future interactions."""
    view = ctx.view
    screen = ctx.screen
    window_w, window_h = screen.get_size()

    # Panel geometry: anchored top-right
    panel_left_x = window_w - view.panel_width - 20  # MARGIN from gfx
    grip_width = 8
    grip_rect = pygame.Rect(panel_left_x - grip_width//2, 0, grip_width, window_h)

    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        ctx.mouse_down = True
        if grip_rect.collidepoint(event.pos):
            ctx.resizing_panel = True
            return True

    if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
        ctx.mouse_down = False
        ctx.resizing_panel = False
        return False

    if event.type == pygame.MOUSEMOTION and ctx.resizing_panel:
        mx, _ = event.pos
        # Compute new panel width so that left edge follows mouse x
        new_width = max(160, min(480, window_w - 20 - mx))  # clamp; MARGIN=20
        if new_width != view.panel_width:
            view.panel_width = new_width
        return True

    return False


def step_events(ctx: GameLoopContext) -> None:
    """
    Process pygame events. Uses a list of key handlers to keep logic modular.
    """
    key_handlers: List[Callable[[pygame.event.Event, GameLoopContext], bool]] = [
        handle_view_keydown,
        handle_game_keydown,
    ]

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            ctx.exit_program = True
            return

        if event.type == pygame.KEYDOWN:
            for handler in key_handlers:
                if handler(event, ctx):
                    break
        elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
            if handle_mouse_events(event, ctx):
                # consume; continue processing other events
                pass

        if ctx.exit_program or ctx.exit_to_menu:
            return


def step_gravity(ctx: GameLoopContext) -> None:
    """
    Apply gravity based on elapsed time and game config.
    """
    ctx.gravity_accumulator += ctx.dt
    if not ctx.state.game_over and ctx.gravity_accumulator >= ctx.gravity_interval_ms:
        ctx.gravity_accumulator = 0
        ctx.state.step(Action.NONE)


def step_draw(ctx: GameLoopContext) -> None:
    """
    Draw a single frame.
    """
    draw_game_frame(ctx.screen, ctx.cfg, ctx.state, ctx.view, ctx.fonts)
    pygame.display.flip()


def run_game_loop(screen: pygame.Surface,
                  cfg: GameConfig,
                  fonts: GfxFonts,
                  view: ViewSettings) -> bool:
    """
    Run a single game session.
    Returns:
        True  -> user wants to go back to menu
        False -> user wants to quit the program
    """
    state = create_initial_state(cfg)
    ctx = GameLoopContext(
        screen=screen,
        cfg=cfg,
        fonts=fonts,
        view=view,
        state=state,
        gravity_interval_ms=gravity_interval_ms_from_config(cfg),
    )

    clock = pygame.time.Clock()
    frame_steps: List[Callable[[GameLoopContext], None]] = [
        step_events,
        step_gravity,
        step_draw,
    ]

    while not ctx.exit_program and not ctx.exit_to_menu:
        ctx.dt = clock.tick(60)

        for step in frame_steps:
            step(ctx)
            if ctx.exit_program or ctx.exit_to_menu:
                break

    if ctx.exit_program:
        return False
    return True


# ---------- Main run ----------

def run():
    pygame.init()
    fonts = init_fonts()
    view = ViewSettings()  # start in top-down, default zoom

    running = True
    while running:
        # --- MENU ---
        pygame.display.set_caption("4D Tetris – Setup")
        menu_screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
        settings = run_menu(menu_screen, fonts)
        if settings is None:
            break  # user quit from menu

        # --- GAME ---
        cfg = GameConfig(
            width=settings.width,
            height=settings.height,
            gravity_axis=1,
            speed_level=settings.speed_level,
        )

        # Initial suggested window size; user can resize afterwards
        board_px_w = cfg.width * view.cell_size
        board_px_h = cfg.height * view.cell_size
        window_w = board_px_w + view.panel_width + 3 * 20  # panel + margins (matches gfx)
        window_h = board_px_h + 2 * 20

        pygame.display.set_caption("4D Tetris (2D prototype)")
        game_screen = pygame.display.set_mode((window_w, window_h), pygame.RESIZABLE)

        back_to_menu = run_game_loop(game_screen, cfg, fonts, view)
        if not back_to_menu:
            running = False


# ---------- Test helpers ----------

def populate_random_grid(ctx: GameLoopContext, density: float = 0.6) -> None:
    """Fill the board with random blocks for visual testing. density in [0,1]."""
    width, height = ctx.cfg.width, ctx.cfg.height
    ctx.state.board.cells.clear()
    rng = random.Random(12345)
    for y in range(height):
        for x in range(width):
            if rng.random() < density:
                ctx.state.board.cells[(x, y)] = rng.randint(1, 7)
    # Disable active piece to keep the board static
    ctx.state.current_piece = None


if __name__ == "__main__":
    run()
