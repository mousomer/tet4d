from __future__ import annotations

from pathlib import Path

from tet4d.engine import api
from tet4d.engine.gameplay.pieces2d import ActivePiece2D, PieceShape2D
from tet4d.engine.gameplay.pieces_nd import ActivePieceND, PieceShapeND
from tet4d.engine.core.rules.piece_placement import piece_placement_is_legal


def _central_2d_pose_legal(state: api.GameState2D, piece: object) -> bool:
    return piece_placement_is_legal(
        piece,
        state.mapped_piece_cells_for_piece(piece, include_above=True),
        state.board.cells,
    )


def _central_nd_pose_legal(state: api.GameStateND, piece: object) -> bool:
    return piece_placement_is_legal(
        piece,
        state._mapped_piece_cells(piece),
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


def test_public_legality_matches_for_2d_embedded_in_nd_collision_and_rotation() -> None:
    blocks_2d = ((0, 0), (1, 0), (0, 1))
    shape_2d = PieceShape2D("corner", list(blocks_2d), color_id=5)
    shape_nd = PieceShapeND(
        "corner",
        tuple((x, y, 0) for x, y in blocks_2d),
        color_id=5,
    )
    state_2d = api.new_game_state_2d(
        api.GameConfig(width=5, height=6, kick_level="off"),
        seed=43,
    )
    state_nd = api.new_game_state_nd(
        api.GameConfigND(dims=(5, 6, 1), gravity_axis=1, kick_level="off"),
        seed=43,
    )
    state_2d.board.cells.clear()
    state_nd.board.cells.clear()
    state_2d.current_piece = ActivePiece2D(shape_2d, pos=(2, 2), rotation=0)
    state_nd.current_piece = ActivePieceND.from_shape(shape_nd, pos=(2, 2, 0))
    state_2d.board.cells[(3, 3)] = 9
    state_nd.board.cells[(3, 3, 0)] = 9

    assert api.translated_piece_pose_legal(state_2d, (1, 0)) is False
    assert api.translated_piece_pose_legal(state_nd, (1, 0, 0)) is False
    assert api.rotated_piece_pose_legal(state_2d, delta_steps=1) is False
    assert (
        api.rotated_piece_pose_legal(
            state_nd,
            axis_a=0,
            axis_b=1,
            delta_steps=1,
        )
        is False
    )


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
