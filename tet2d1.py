# sandbox_main.py
from tetris_nd.board import BoardND
from tetris_nd.game2d import GameConfig, GameState, Action


def render_text_board(state: GameState) -> str:
    """
    Render a simple ASCII representation of the board + active piece.
    """
    w, h = state.config.width, state.config.height
    grid = [[0 for _ in range(w)] for _ in range(h)]

    # Locked cells
    for (x, y), cell_id in state.board.cells.items():
        if 0 <= x < w and 0 <= y < h:
            grid[y][x] = cell_id

    # Active piece
    if state.current_piece is not None:
        for (x, y) in state.current_piece.cells():
            if 0 <= x < w and 0 <= y < h:
                grid[y][x] = 9  # falling piece

    lines = []
    for y in range(h):
        line = "".join("." if cell == 0 else "#" for cell in grid[y])
        lines.append(line)
    return "\n".join(lines)


def main():
    cfg = GameConfig(width=10, height=20)
    board = BoardND((cfg.width, cfg.height))
    state = GameState(config=cfg, board=board)

    keymap = {
        "a": Action.MOVE_LEFT,
        "d": Action.MOVE_RIGHT,
        "s": Action.SOFT_DROP,
        "w": Action.ROTATE_CW,
        "e": Action.ROTATE_CCW,
        " ": Action.HARD_DROP,
        "": Action.NONE,  # just press Enter to advance gravity
    }

    step_idx = 0
    while not state.game_over:
        print("\033[H\033[J", end="")  # clear terminal (may not work in all consoles)
        print(f"Step: {step_idx}  Score: {state.score}  Lines: {state.lines_cleared}")
        print(render_text_board(state))
        print()
        print("Controls: a=left, d=right, s=down, w=rotCW, e=rotCCW, space=hard drop, Enter=wait, q=quit")
        cmd = input("Command: ")

        if cmd == "q":
            break

        action = keymap.get(cmd, Action.NONE)
        state.step(action)
        step_idx += 1

    print("Game over. Final score:", state.score)


if __name__ == "__main__":
    main()
