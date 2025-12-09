# sandbox_main.py
import time

from tetris_nd.board import BoardND
from tetris_nd.game2d import GameConfig, GameState, Action


def render_text_board(state: GameState) -> str:
    """
    Render a simple ASCII representation of the board + active piece.
    """
    w, h = state.config.width, state.config.height
    # Start with empty board
    grid = [[0 for _ in range(w)] for _ in range(h)]

    # Fill with locked cells
    for (x, y), cell_id in state.board.cells.items():
        if 0 <= x < w and 0 <= y < h:
            grid[y][x] = cell_id

    # Overlay active piece
    if state.current_piece is not None:
        for (x, y) in state.current_piece.cells():
            if 0 <= x < w and 0 <= y < h:
                grid[y][x] = 9  # distinguish falling piece

    # Convert to string
    lines = []
    for y in range(h):
        line = "".join("." if cell == 0 else "#" for cell in grid[y])
        lines.append(line)
    return "\n".join(lines)


def main():
    cfg = GameConfig(width=10, height=20)
    board = BoardND((cfg.width, cfg.height))
    state = GameState(config=cfg, board=board)

    tick = 0
    while not state.game_over and tick < 200:
        # For now: no user input, just gravity
        state.step(Action.NONE)
        print("\033[H\033[J", end="")  # clear terminal (ANSI hack)
        print(f"Tick: {tick}  Score: {state.score}  Lines: {state.lines_cleared}")
        print(render_text_board(state))
        time.sleep(0.1)
        tick += 1

    print("Game over. Final score:", state.score)


if __name__ == "__main__":
    main()
