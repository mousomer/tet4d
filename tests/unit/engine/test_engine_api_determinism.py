from __future__ import annotations

from tet4d.engine import api


def _snapshot_2d(state: api.GameState2D) -> tuple[object, ...]:
    piece = state.current_piece
    piece_sig = None
    if piece is not None:
        piece_sig = (piece.shape.name, tuple(piece.pos), int(piece.rotation))
    bag_sig = tuple(shape.name for shape in state.next_bag[:5])
    board_sig = tuple(sorted(api.board_cells(state).items()))
    return (
        piece_sig,
        bag_sig,
        board_sig,
        state.score,
        state.lines_cleared,
        api.is_game_over(state),
    )


def _snapshot_nd(state: api.GameStateND) -> tuple[object, ...]:
    piece = state.current_piece
    piece_sig = None
    if piece is not None:
        piece_sig = (piece.shape.name, tuple(piece.pos), tuple(piece.rel_blocks))
    bag_sig = tuple(shape.name for shape in state.next_bag[:5])
    board_sig = tuple(sorted(api.board_cells(state).items()))
    return (
        piece_sig,
        bag_sig,
        board_sig,
        state.score,
        state.lines_cleared,
        api.is_game_over(state),
    )


def test_engine_rng_fork_preserves_sequence() -> None:
    rng = api.new_rng(1234)
    clone = rng.fork()
    left = [rng.randrange(1000) for _ in range(8)]
    right = [clone.randrange(1000) for _ in range(8)]
    assert left == right


def test_api_new_state_2d_is_deterministic_for_same_seed_and_actions() -> None:
    cfg = api.GameConfig(width=8, height=16, speed_level=3)
    actions = (
        api.Action.MOVE_LEFT,
        api.Action.ROTATE_CW,
        api.Action.MOVE_RIGHT,
        api.Action.SOFT_DROP,
        api.Action.NONE,
        api.Action.ROTATE_CCW,
        api.Action.SOFT_DROP,
        api.Action.NONE,
    )

    state_a = api.new_game_state_2d(cfg, seed=77)
    state_b = api.new_game_state_2d(cfg, seed=77)

    before_a = _snapshot_2d(state_a)
    before_b = _snapshot_2d(state_b)
    assert before_a == before_b

    for action in actions:
        api.step_2d(state_a, action)
        api.step_2d(state_b, action)

    after_a = _snapshot_2d(state_a)
    after_b = _snapshot_2d(state_b)
    assert after_a == after_b


def test_api_new_state_nd_is_deterministic_for_same_seed_and_steps() -> None:
    cfg = api.GameConfigND(dims=(6, 14, 4), gravity_axis=1, speed_level=2)

    rng_a = api.new_rng(2024)
    rng_b = api.new_rng(2024)
    state_a = api.new_game_state_nd(cfg, rng=rng_a)
    state_b = api.new_game_state_nd(cfg, rng=rng_b)

    before_a = _snapshot_nd(state_a)
    before_b = _snapshot_nd(state_b)
    assert before_a == before_b

    # Apply the same deterministic sequence of legal state mutations and gravity ticks.
    for _ in range(4):
        state_a.try_move_axis(0, 1)
        state_b.try_move_axis(0, 1)
        api.step_nd(state_a)
        api.step_nd(state_b)

    after_a = _snapshot_nd(state_a)
    after_b = _snapshot_nd(state_b)
    assert after_a == after_b
