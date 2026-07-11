from types import SimpleNamespace

from tet4d.engine.core.model import BoardND
from tet4d.engine.core.rotation_kicks import resolve_and_commit_rotated_piece
from tet4d.engine.core.rules.lifecycle import install_spawn_candidate
from tet4d.engine.gameplay.game2d import GameConfig, GameState
from tet4d.engine.gameplay.game_nd import GameConfigND, GameStateND
from tet4d.engine.gameplay.pieces2d import ActivePiece2D, PieceShape2D
from tet4d.engine.gameplay.pieces_nd import ActivePieceND, PieceShapeND


def test_install_spawn_candidate_sets_piece_and_game_over_from_legality() -> None:
    candidate = object()
    for legal, expected_game_over in ((True, False), (False, True)):
        state = SimpleNamespace(current_piece=None, game_over=False)

        installed = install_spawn_candidate(
            state,
            candidate,
            can_exist=lambda _piece, legal=legal: legal,
        )

        assert installed is legal
        assert state.current_piece is candidate
        assert state.game_over is expected_game_over


def test_resolve_and_commit_rotated_piece_commits_only_legal_candidate() -> None:
    cases = (
        ("light", ((0, 0), (-1, 0)), lambda piece: piece == (-1, 0), [(-1, 0)]),
        ("off", ((0, 0),), lambda _piece: False, []),
    )
    for kick_level, offsets, can_place, expected_commits in cases:
        committed: list[tuple[int, int]] = []
        result = resolve_and_commit_rotated_piece(
            (0, 0),
            ndim=2,
            axis_a=0,
            axis_b=1,
            gravity_axis=1,
            kick_level=kick_level,
            plane_offsets_for_level=lambda _level, offsets=offsets: offsets,
            move_piece=lambda piece, vector: (
                piece[0] + vector[0],
                piece[1] + vector[1],
            ),
            can_place=can_place,
            commit_piece=lambda piece: committed.append(piece) or True,
        )

        assert result is bool(expected_commits)
        assert committed == expected_commits


def test_2d_and_embedded_nd_lock_clear_and_score_are_equivalent() -> None:
    state_2d = GameState(config=GameConfig(width=2, height=3), board=BoardND((2, 3)))
    state_nd = GameStateND(
        config=GameConfigND(dims=(2, 3, 1), gravity_axis=1),
        board=BoardND((2, 3, 1)),
    )
    state_2d.board.cells = {(0, 0): 9, (0, 2): 1}
    state_nd.board.cells = {(0, 0, 0): 9, (0, 2, 0): 1}
    state_2d.current_piece = ActivePiece2D(
        PieceShape2D("dot", [(0, 0)], color_id=6),
        pos=(1, 2),
        rotation=0,
    )
    state_nd.current_piece = ActivePieceND.from_shape(
        PieceShapeND("dot", ((0, 0, 0),), color_id=6),
        pos=(1, 2, 0),
    )

    cleared_2d = state_2d.lock_current_piece()
    cleared_nd = state_nd.lock_current_piece()
    nd_cells_2d = {(x, y): color for (x, y, _z), color in state_nd.board.cells.items()}

    assert cleared_2d == cleared_nd
    assert state_2d.lines_cleared == state_nd.lines_cleared
    assert state_2d.score == state_nd.score
    assert state_2d.board.cells == nd_cells_2d
    assert state_2d.game_over == state_nd.game_over
