from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from tet4d.engine import api
from tet4d.engine.core.model import BoardND
from tet4d.engine.core.rules.piece_placement import (
    build_candidate_piece_placement,
    validate_candidate_piece_placement,
)
from tet4d.engine.gameplay.game2d import GameConfig, GameState
from tet4d.engine.gameplay.game_nd import GameConfigND, GameStateND
from tet4d.engine.gameplay.pieces2d import ActivePiece2D, PieceShape2D
from tet4d.engine.gameplay.pieces_nd import ActivePieceND, PieceShapeND
from tet4d.engine.topology_explorer import MoveStep, build_explorer_transport_resolver
from tet4d.engine.topology_explorer.presets import axis_wrap_profile, swapped_xz_profile_3d


REPO_ROOT = Path(__file__).resolve().parents[3]
QUERY_TEST_BIN = REPO_ROOT / "native" / "tet4d_core" / "build" / "tests" / "query_core_tests"


def _native_query_payload() -> dict[str, object]:
    if not QUERY_TEST_BIN.exists():
        pytest.skip("native query test binary is not built")
    completed = subprocess.run(
        [str(QUERY_TEST_BIN), "--query-parity"],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def _legality_cases() -> dict[str, bool]:
    shape_2d = PieceShape2D("dot", [(0, 0)], color_id=1)
    state_2d = GameState(config=GameConfig(width=4, height=5), board=BoardND((4, 5)))
    state_2d.board.cells.clear()

    state_2d_blocked = GameState(
        config=GameConfig(width=4, height=5),
        board=BoardND((4, 5)),
    )
    state_2d_blocked.board.cells.clear()
    state_2d_blocked.board.cells[(1, 1)] = 9

    shape_3d = PieceShapeND("dot", ((0, 0, 0),), color_id=2)
    state_3d = GameStateND(
        config=GameConfigND(dims=(4, 5, 3), gravity_axis=1),
        board=BoardND((4, 5, 3)),
    )
    state_3d.board.cells.clear()
    state_3d.current_piece = ActivePieceND.from_shape(shape_3d, pos=(1, 1, 1))

    rotate_shape = PieceShapeND("bar", ((0, 0, 0), (0, 0, 1)), color_id=3)
    rotate_state = GameStateND(
        config=GameConfigND(dims=(4, 5, 3), gravity_axis=1),
        board=BoardND((4, 5, 3)),
    )
    rotate_state.board.cells.clear()
    rotate_state.current_piece = ActivePieceND.from_shape(rotate_shape, pos=(1, 1, 1))

    duplicate_candidate = build_candidate_piece_placement(
        object(),
        ((1, 1), (1, 1)),
    )

    return {
        "bounded_2d_legal": api.piece_pose_legal(
            state_2d,
            ActivePiece2D(shape_2d, pos=(1, 1), rotation=0),
        ),
        "bounded_2d_occupied": api.piece_pose_legal(
            state_2d_blocked,
            ActivePiece2D(shape_2d, pos=(1, 1), rotation=0),
        ),
        "bounded_2d_boundary": api.piece_pose_legal(
            state_2d,
            ActivePiece2D(shape_2d, pos=(-1, 1), rotation=0),
        ),
        "bounded_2d_duplicate": validate_candidate_piece_placement(
            duplicate_candidate,
            state_2d.board.cells,
            coord_validator=state_2d.board.inside_bounds,
        ),
        "bounded_3d_translate": api.translated_piece_pose_legal(state_3d, (1, 0, 0)),
        "bounded_3d_translate_boundary": api.piece_pose_legal(
            state_3d,
            ActivePieceND.from_shape(shape_3d, pos=(4, 1, 1)),
        ),
        "bounded_3d_rotate": api.rotated_piece_pose_legal(
            rotate_state,
            axis_a=0,
            axis_b=2,
            delta_steps=1,
        ),
    }


def _topology_cases() -> dict[str, dict[str, object]]:
    torus = build_explorer_transport_resolver(
        axis_wrap_profile(dimension=2, wrapped_axes=(0, 1)),
        (3, 4),
    )
    bounded = build_explorer_transport_resolver(
        axis_wrap_profile(dimension=2, wrapped_axes=()),
        (3, 4),
    )
    swapped = build_explorer_transport_resolver(swapped_xz_profile_3d(), (4, 4, 4))
    cases = {
        "bounded_2d_y_plus_blocked": bounded.resolve_cell_step(
            (1, 3),
            MoveStep(axis=1, delta=1),
        ),
        "torus_2d_x_plus": torus.resolve_cell_step((2, 2), MoveStep(axis=0, delta=1)),
        "torus_2d_y_plus": torus.resolve_cell_step((1, 3), MoveStep(axis=1, delta=1)),
        "cross_axis_x_minus_to_z_plus": swapped.resolve_cell_step(
            (0, 1, 2),
            MoveStep(axis=0, delta=-1),
        ),
        "cross_axis_reverse_z_plus": swapped.resolve_cell_step(
            (2, 1, 3),
            MoveStep(axis=2, delta=1),
        ),
    }
    return {
        name: {
            "ok": True,
            "target": None if result.target is None else list(result.target),
            "glue_id": None if result.traversal is None else result.traversal.glue_id,
            "source_boundary": (
                None
                if result.traversal is None
                else result.traversal.source_boundary.label
            ),
            "target_boundary": (
                None
                if result.traversal is None
                else result.traversal.target_boundary.label
            ),
            "entry_step": (
                result.step.label
                if result.traversal is None
                else result.traversal.entry_step.label
            ),
            "error": "",
        }
        for name, result in cases.items()
    }


def test_cpp_legality_queries_match_python_oracle() -> None:
    native = _native_query_payload()
    actual = {case["name"]: case["legal"] for case in native["legality_cases"]}

    assert actual == _legality_cases()


def test_cpp_topology_queries_match_python_resolver() -> None:
    native = _native_query_payload()
    actual = {case["name"]: {key: value for key, value in case.items() if key != "name"} for case in native["topology_cases"]}

    assert actual == _topology_cases()
