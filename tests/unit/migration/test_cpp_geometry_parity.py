from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from tet4d.engine.core.piece_transform import (
    canonicalize_blocks_nd,
    normalize_blocks_nd,
    rotate_blocks_nd,
    rotate_point_nd,
)
from tools.parity.first_subsystem_parity_pilot import python_oracle_stable_hash_text


REPO_ROOT = Path(__file__).resolve().parents[3]
GEOMETRY_TEST_BIN = (
    REPO_ROOT / "native" / "tet4d_core" / "build" / "tests" / "geometry_core_tests"
)


def _blocks_2d() -> tuple[tuple[int, ...], ...]:
    return ((2, -1), (0, 0), (2, -1), (1, 0))


def _blocks_3d() -> tuple[tuple[int, ...], ...]:
    return ((2, -1, 0), (0, 0, 1), (1, 0, -1), (0, 1, 1))


def _blocks_4d() -> tuple[tuple[int, ...], ...]:
    return ((1, -2, 0, 3), (0, -1, 1, 2), (2, -2, 0, 1), (1, -3, 1, 2))


def _translate_blocks(
    blocks: tuple[tuple[int, ...], ...],
    offset: tuple[int, ...],
) -> tuple[tuple[int, ...], ...]:
    return canonicalize_blocks_nd(
        tuple(
            tuple(coord[axis] + offset[axis] for axis in range(len(offset)))
            for coord in blocks
        )
    )


def _rotate_around_origin(
    blocks: tuple[tuple[int, ...], ...],
) -> tuple[tuple[int, ...], ...]:
    return tuple(rotate_point_nd(coord, 0, 1, 1) for coord in blocks)


def _geometry_hash(blocks: tuple[tuple[int, ...], ...]) -> str:
    canonical = canonicalize_blocks_nd(blocks)
    serialized = "blocks:" + ";".join(
        "[" + ",".join(str(value) for value in coord) + "]" for coord in canonical
    )
    return python_oracle_stable_hash_text(serialized)


def test_cpp_geometry_slice_matches_python_oracle() -> None:
    if not GEOMETRY_TEST_BIN.exists():
        pytest.skip("native geometry test binary is not built")

    completed = subprocess.run(
        [str(GEOMETRY_TEST_BIN), "--geometry-parity"],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    native = json.loads(completed.stdout)
    actual_cases = {case["name"]: case["actual"] for case in native["cases"]}

    expected_cases = {
        "canonicalize_2d_duplicates": canonicalize_blocks_nd(_blocks_2d()),
        "normalize_3d_negative_unsorted": normalize_blocks_nd(_blocks_3d()),
        "translate_3d": _translate_blocks(_blocks_3d(), (-2, 3, 1)),
        "rotate_3d_xz": rotate_blocks_nd(_blocks_3d(), 0, 2, 1),
        "rotate_4d_xw_negative": rotate_blocks_nd(_blocks_4d(), 0, 3, -1),
        "rotate_2d_explicit_pivot": _rotate_around_origin(((1, 0), (0, 1))),
    }
    assert actual_cases == {
        name: [list(coord) for coord in coords]
        for name, coords in expected_cases.items()
    }
    assert native["hash_case"] == {
        "name": "hash_3d",
        "actual": _geometry_hash(_blocks_3d()),
    }
