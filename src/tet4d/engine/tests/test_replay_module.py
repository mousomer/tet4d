from __future__ import annotations

from tet4d.engine import api
from tet4d.replay import (
    play_replay_2d,
    play_replay_nd_ticks,
    record_replay_2d,
    record_replay_nd_ticks,
)
from tet4d.replay.format import ReplayScript2D, ReplayTickScriptND


def _sig_2d(state: api.GameState2D) -> tuple[object, ...]:
    piece = state.current_piece
    piece_sig = None
    if piece is not None:
        piece_sig = (piece.shape.name, tuple(piece.pos), int(piece.rotation))
    return (
        state.score,
        state.lines_cleared,
        state.game_over,
        tuple(sorted(api.board_cells(state).items())),
        piece_sig,
        tuple(shape.name for shape in state.next_bag),
    )


def _sig_nd(state: api.GameStateND) -> tuple[object, ...]:
    piece = state.current_piece
    piece_sig = None
    if piece is not None:
        piece_sig = (
            piece.shape.name,
            tuple(piece.pos),
            tuple(sorted(piece.rel_blocks)),
        )
    return (
        state.score,
        state.lines_cleared,
        state.game_over,
        tuple(sorted(api.board_cells(state).items())),
        piece_sig,
        tuple(shape.name for shape in state.next_bag),
    )


def test_replay_2d_record_and_payload_roundtrip() -> None:
    cfg = api.GameConfig(width=8, height=16, speed_level=2)
    actions = (
        api.Action.MOVE_LEFT,
        api.Action.ROTATE_CW,
        api.Action.SOFT_DROP,
        api.Action.NONE,
    )
    script = record_replay_2d(config=cfg, seed=55, actions=actions)

    payload = script.to_dict()
    restored = ReplayScript2D.from_dict(payload)

    assert restored.seed == 55
    assert restored.config.width == cfg.width
    assert tuple(event.action for event in restored.events) == tuple(
        a.name for a in actions
    )


def test_replay_2d_playback_matches_direct_api_execution() -> None:
    cfg = api.GameConfig(width=8, height=16, speed_level=2)
    actions = (
        api.Action.MOVE_LEFT,
        api.Action.ROTATE_CW,
        api.Action.SOFT_DROP,
        api.Action.MOVE_RIGHT,
        api.Action.NONE,
        api.Action.ROTATE_CCW,
    )
    script = record_replay_2d(config=cfg, seed=101, actions=actions)

    direct = api.new_game_state_2d(cfg, seed=101)
    for action in actions:
        api.step_2d(direct, action)

    replayed = play_replay_2d(script)
    assert _sig_2d(replayed) == _sig_2d(direct)


def test_replay_nd_tick_playback_matches_direct_api_execution() -> None:
    cfg = api.GameConfigND(dims=(6, 14, 4), gravity_axis=1, speed_level=1)
    script = record_replay_nd_ticks(config=cfg, seed=202, ticks=6)

    payload = script.to_dict()
    restored = ReplayTickScriptND.from_dict(payload)
    replayed = play_replay_nd_ticks(restored)

    direct = api.new_game_state_nd(cfg, seed=202)
    for _ in range(6):
        api.step_nd(direct)

    assert _sig_nd(replayed) == _sig_nd(direct)
