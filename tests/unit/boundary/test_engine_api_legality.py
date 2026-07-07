from __future__ import annotations

from pathlib import Path

from tet4d.engine import api
from tet4d.engine.core.rules.piece_placement import (
    build_candidate_piece_placement,
    validate_candidate_piece_placement,
)


def _central_2d_pose_legal(state: api.GameState2D, piece: object) -> bool:
    return validate_candidate_piece_placement(
        build_candidate_piece_placement(
            piece,
            state.mapped_piece_cells_for_piece(piece, include_above=True),
        ),
        state.board.cells,
    )


def _central_nd_pose_legal(state: api.GameStateND, piece: object) -> bool:
    return validate_candidate_piece_placement(
        build_candidate_piece_placement(piece, state._mapped_piece_cells(piece)),
        state.board.cells,
    )


def test_public_piece_pose_legality_matches_central_2d_placement() -> None:
    state = api.new_game_state_2d(api.GameConfig(width=6, height=10), seed=17)
    assert state.current_piece is not None
    piece = state.current_piece
    blocked = piece.moved(-(state.config.width + 2), 0)

    assert api.piece_pose_legal(state, piece) == _central_2d_pose_legal(state, piece)
    assert api.piece_pose_legal(state, blocked) == _central_2d_pose_legal(
        state,
        blocked,
    )


def test_public_piece_pose_legality_matches_central_nd_placement() -> None:
    state = api.new_game_state_nd(
        api.GameConfigND(dims=(6, 10, 4), gravity_axis=1),
        seed=23,
    )
    assert state.current_piece is not None
    piece = state.current_piece
    blocked = piece.moved((-(state.config.dims[0] + 2), 0, 0))

    assert api.piece_pose_legal(state, piece) == _central_nd_pose_legal(state, piece)
    assert api.piece_pose_legal(state, blocked) == _central_nd_pose_legal(
        state,
        blocked,
    )


def test_public_translation_legality_matches_existing_engine_2d_behavior() -> None:
    state = api.new_game_state_2d(api.GameConfig(width=6, height=10), seed=31)
    assert state.current_piece is not None
    while api.translated_piece_pose_legal(state, (-1, 0)):
        assert state.try_move(-1, 0)

    assert api.translated_piece_pose_legal(state, (-1, 0)) is False
    assert state.try_move(-1, 0) is False


def test_public_translation_legality_matches_existing_engine_nd_behavior() -> None:
    state = api.new_game_state_nd(
        api.GameConfigND(dims=(6, 10, 4), gravity_axis=1),
        seed=37,
    )
    assert state.current_piece is not None
    while api.translated_piece_pose_legal(state, (-1, 0, 0)):
        assert state.try_move_axis(0, -1)

    assert api.translated_piece_pose_legal(state, (-1, 0, 0)) is False
    assert state.try_move_axis(0, -1) is False


def test_public_rotation_legality_matches_existing_nd_rotation_result() -> None:
    state = api.new_game_state_nd(
        api.GameConfigND(
            dims=(6, 10, 4),
            gravity_axis=1,
            kick_level="off",
        ),
        seed=41,
    )

    expected = api.rotated_piece_pose_legal(
        state,
        axis_a=0,
        axis_b=2,
        delta_steps=1,
    )

    assert state.try_rotate(0, 2, 1) is expected


def test_ui_and_tutorial_do_not_call_private_piece_legality() -> None:
    searched_roots = (
        Path("src/tet4d/ui/pygame"),
        Path("src/tet4d/engine/tutorial"),
    )
    offenders = [
        path.as_posix()
        for root in searched_roots
        for path in root.rglob("*.py")
        if "._can_exist(" in path.read_text(encoding="utf-8")
    ]

    assert offenders == []
