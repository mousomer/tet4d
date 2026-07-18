from __future__ import annotations

import argparse
import difflib
import json
import random
import subprocess
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.migration.trace_schema import canonical_json
from tools.migration.trace_cases import GAMEPLAY_TRACE_CASES
from tet4d.engine.core.model import BoardND
from tet4d.engine.gameplay.game2d import GameConfig, GameState
from tet4d.engine.gameplay.game_nd import GameConfigND, GameStateND

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GOLDEN_DIR = ROOT / "migration" / "golden_traces" / "gameplay"
PLAIN_2D_CASES = {
    "gameplay_plain_2d_short",
    "gameplay_plain_2d_rotation_short",
    "gameplay_plain_2d_hard_drop_lock",
    "gameplay_plain_2d_line_clear_short",
    "gameplay_plain_2d_configurable",
}
PLAIN_ND_CASES = {
    "gameplay_plain_3d_short",
    "gameplay_plain_4d_short",
    "gameplay_plain_3d_rotation_short",
    "gameplay_plain_4d_rotation_short",
    "gameplay_plain_3d_plane_clear_short",
    "gameplay_plain_4d_plane_clear_short",
    "gameplay_plain_3d_spawn_blocked_game_over",
    "gameplay_plain_4d_spawn_blocked_game_over",
    "gameplay_plain_3d_configurable",
    "gameplay_plain_4d_configurable_w8",
}
CONFIGURABLE_CASES = {
    "gameplay_plain_2d_configurable",
    "gameplay_plain_3d_configurable",
    "gameplay_plain_4d_configurable_w8",
}
SUPPORTED_CASES = PLAIN_2D_CASES | PLAIN_ND_CASES
PLAIN_SETUP_CASES = {
    "setup_plain_2d_standard": {
        "dimension": 2,
        "board_preset_id": "standard",
        "board_shape": (6, 6),
        "piece_set_id": "classic",
        "seed": 1337,
        "speed": 1,
        "actions": ("move_right", "rotate_cw", "soft_drop", "hard_drop"),
    },
    "setup_plain_2d_alternate": {
        "dimension": 2,
        "board_preset_id": "large",
        "board_shape": (10, 20),
        "piece_set_id": "classic",
        "seed": 2025,
        "speed": 7,
        "actions": ("soft_drop", "hard_drop"),
    },
    "setup_plain_3d_embedded_2d": {
        "dimension": 3,
        "board_preset_id": "large",
        "board_shape": (8, 16, 8),
        "piece_set_id": "embedded_2d",
        "seed": 2025,
        "speed": 6,
        "actions": ("move_z_pos", "rotate_xz_pos", "soft_drop", "hard_drop"),
    },
    "setup_plain_4d_embedded_3d": {
        "dimension": 4,
        "board_preset_id": "standard",
        "board_shape": (5, 10, 4, 4),
        "piece_set_id": "embedded_3d",
        "seed": 1337,
        "speed": 4,
        "actions": ("move_w_pos", "rotate_xw_pos", "soft_drop", "hard_drop"),
    },
    "setup_plain_4d_embedded_2d": {
        "dimension": 4,
        "board_preset_id": "standard",
        "board_shape": (5, 10, 4, 4),
        "piece_set_id": "embedded_2d",
        "seed": 2025,
        "speed": 3,
        "actions": ("rotate_xy_pos", "hard_drop"),
    },
    "setup_plain_4d_wide_true": {
        "dimension": 4,
        "board_preset_id": "wide_w",
        "board_shape": (8, 16, 5, 8),
        "piece_set_id": "standard_4d_5",
        "seed": 42,
        "speed": 8,
        "actions": ("move_w_pos", "rotate_xw_pos", "hard_drop"),
    },
}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _cpp_trace(case_id: str) -> dict[str, Any]:
    export_flag = (
        "--export-plain-nd-trace"
        if case_id in PLAIN_ND_CASES
        else "--export-plain-2d-trace"
    )
    command = [
        str(ROOT / "scripts" / "test_godot_tet4d_core.sh"),
        export_flag,
        case_id,
    ]
    result = subprocess.run(
        command,
        check=True,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return json.loads(result.stdout)


def _contract_projection(trace: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": trace["case_id"],
        "commands": trace["commands"],
        "dimension": trace["dimension"],
        "final": trace["final"],
        "frames": trace["frames"],
        "generator": trace["generator"],
        "initial": trace["initial"],
        "seed": trace["seed"],
        "topology_id": trace["topology_id"],
        "trace_type": trace["trace_type"],
        "trace_version": trace["trace_version"],
    }


def _field_diffs(expected: Any, actual: Any, path: str = "$") -> list[str]:
    if type(expected) is not type(actual):
        return [
            f"{path}: type mismatch expected {type(expected).__name__}, got {type(actual).__name__}"
        ]
    if isinstance(expected, dict):
        diffs: list[str] = []
        expected_keys = set(expected)
        actual_keys = set(actual)
        for key in sorted(expected_keys - actual_keys):
            diffs.append(f"{path}.{key}: missing from C++ trace")
        for key in sorted(actual_keys - expected_keys):
            diffs.append(f"{path}.{key}: unexpected in C++ trace")
        for key in sorted(expected_keys & actual_keys):
            diffs.extend(_field_diffs(expected[key], actual[key], f"{path}.{key}"))
        return diffs
    if isinstance(expected, list):
        diffs = []
        if len(expected) != len(actual):
            diffs.append(
                f"{path}: length mismatch expected {len(expected)}, got {len(actual)}"
            )
        for index, (expected_item, actual_item) in enumerate(zip(expected, actual)):
            diffs.extend(_field_diffs(expected_item, actual_item, f"{path}[{index}]"))
        return diffs
    if expected != actual:
        return [f"{path}: expected {expected!r}, got {actual!r}"]
    return []


def _canonical_diff(expected: Any, actual: Any) -> str:
    return "".join(
        difflib.unified_diff(
            canonical_json(expected).splitlines(keepends=True),
            canonical_json(actual).splitlines(keepends=True),
            fromfile="python-golden",
            tofile="cpp-native",
        )
    )


def _first_frame_mismatch(case_id: str, diffs: list[str]) -> str | None:
    for diff in diffs:
        marker = "$.frames["
        if not diff.startswith(marker):
            continue
        end = diff.find("]", len(marker))
        if end < 0:
            continue
        frame_index = diff[len(marker) : end]
        field_path = "$.frames[" + frame_index + "]" + diff[end + 1 :].split(": ", 1)[0]
        return (
            f"case {case_id}: first mismatching frame: {frame_index}; "
            f"field path: {field_path}"
        )
    return None


def compare_case(case_id: str, golden_dir: Path) -> list[str]:
    if case_id not in SUPPORTED_CASES:
        return [f"unsupported C++ gameplay parity case: {case_id}"]
    golden = _load_json(golden_dir / f"{case_id}.json")
    cpp = _cpp_trace(case_id)
    golden_contract = _contract_projection(golden)
    cpp_contract = _contract_projection(cpp)
    if cpp_contract != golden_contract:
        diffs = _field_diffs(golden_contract, cpp_contract)
        frame_mismatch = _first_frame_mismatch(case_id, diffs)
        hash_diffs = [
            diff
            for diff in diffs
            if "state_hash" in diff or "locked_cell_digest" in diff
        ]
        final_hash_diffs = [
            diff for diff in diffs if diff.startswith("$.final.state_hash:")
        ]
        summary = []
        if frame_mismatch is not None:
            summary.append(frame_mismatch)
        if final_hash_diffs:
            summary.append(f"case {case_id}: final hash mismatch")
            summary.extend(final_hash_diffs[:3])
        elif hash_diffs:
            summary.append(f"case {case_id}: state_hash mismatch")
        summary.extend(hash_diffs[:10])
        return [
            f"case id: {case_id}",
            *diffs[0:40],
            *summary,
            f"C++ gameplay trace contract mismatch for {case_id}",
            _canonical_diff(golden_contract, cpp_contract),
        ]
    return []


def _cpp_setup_case(case_id: str) -> dict[str, Any]:
    result = subprocess.run(
        [
            str(ROOT / "scripts" / "test_godot_tet4d_core.sh"),
            "--export-plain-setup",
            case_id,
        ],
        check=True,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return json.loads(result.stdout)


def _python_setup_state(case: dict[str, Any]) -> GameState | GameStateND:
    dimension = int(case["dimension"])
    shape = tuple(int(value) for value in case["board_shape"])
    seed = int(case["seed"])
    rng = random.Random(seed)
    if dimension == 2:
        config = GameConfig(
            width=shape[0],
            height=shape[1],
            piece_set=str(case["piece_set_id"]),
            rng_mode="fixed_seed",
            rng_seed=seed,
            speed_level=int(case["speed"]),
        )
        return GameState(config=config, board=BoardND(shape), rng=rng)
    config_nd = GameConfigND(
        dims=shape,
        piece_set_id=str(case["piece_set_id"]),
        rng_mode="fixed_seed",
        rng_seed=seed,
        speed_level=int(case["speed"]),
    )
    return GameStateND(config=config_nd, board=BoardND(shape), rng=rng)


def _apply_setup_action(state: GameState | GameStateND, action: str) -> None:
    if isinstance(state, GameState):
        if action == "move_right":
            state.try_move(1, 0)
        elif action == "rotate_cw":
            state.try_rotate(1)
        elif action == "soft_drop":
            state.try_soft_drop()
        elif action == "hard_drop":
            state.hard_drop()
        else:
            raise ValueError(f"unsupported 2D setup parity action: {action}")
        return
    if action == "move_z_pos":
        state.try_move_axis(2, 1)
    elif action == "move_w_pos":
        state.try_move_axis(3, 1)
    elif action == "rotate_xy_pos":
        state.try_rotate(0, 1, 1)
    elif action == "rotate_xz_pos":
        state.try_rotate(0, 2, 1)
    elif action == "rotate_xw_pos":
        state.try_rotate(0, 3, 1)
    elif action == "soft_drop":
        state.try_soft_drop()
    elif action == "hard_drop":
        state.hard_drop()
    else:
        raise ValueError(f"unsupported ND setup parity action: {action}")


def _python_setup_projection(
    state: GameState | GameStateND,
    case: dict[str, Any],
) -> dict[str, Any]:
    current = state.current_piece
    active_cells = (
        sorted(tuple(int(value) for value in cell) for cell in current.cells())
        if current is not None
        else []
    )
    locked_cells = [
        {"position": list(coord), "value": int(value)}
        for coord, value in sorted(state.board.cells.items())
    ]
    next_piece = state.next_bag[-1].name if state.next_bag else "pending_bag"
    return {
        "active_cells": [list(cell) for cell in active_cells],
        "board_shape": list(case["board_shape"]),
        "configured_seed": int(case["seed"]),
        "current_piece": current.shape.name if current is not None else "none",
        "effective_seed": int(case["seed"]),
        "game_over": bool(state.game_over),
        "game_over_reason": str(getattr(state, "game_over_reason", "")),
        "initial_speed_level": int(case["speed"]),
        "lines": int(state.lines_cleared),
        "locked_cells": locked_cells,
        "next_piece": next_piece,
        "piece_set_id": str(case["piece_set_id"]),
        "random_mode": "fixed_seed",
        "score": int(state.score),
    }


def _native_setup_projection(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "active_cells": sorted(
            [list(cell["position"]) for cell in snapshot.get("active_cells", [])]
        ),
        "board_shape": list(snapshot.get("board_shape", [])),
        "configured_seed": snapshot.get("configured_seed"),
        "current_piece": snapshot.get("current_piece"),
        "effective_seed": snapshot.get("effective_seed"),
        "game_over": bool(snapshot.get("game_over", False)),
        "game_over_reason": str(snapshot.get("game_over_reason", "")),
        "initial_speed_level": snapshot.get("initial_speed_level"),
        "lines": snapshot.get("lines"),
        "locked_cells": sorted(
            [
                {
                    "position": list(cell["position"]),
                    "value": int(cell["color_id"]),
                }
                for cell in snapshot.get("locked_cells", [])
            ],
            key=lambda item: item["position"],
        ),
        "next_piece": snapshot.get("next_piece"),
        "piece_set_id": snapshot.get("piece_set_id"),
        "random_mode": snapshot.get("random_mode"),
        "score": snapshot.get("score"),
    }


def compare_setup_case(case_id: str) -> list[str]:
    case = PLAIN_SETUP_CASES[case_id]
    native = _cpp_setup_case(case_id)
    state = _python_setup_state(case)
    expected_frames = [_python_setup_projection(state, case)]
    for action in case["actions"]:
        _apply_setup_action(state, str(action))
        expected_frames.append(_python_setup_projection(state, case))
    native_frames = native.get("frames", [])
    failures: list[str] = []
    for action_index, expected in enumerate(expected_frames):
        action = "initial" if action_index == 0 else str(case["actions"][action_index - 1])
        actual = (
            _native_setup_projection(native_frames[action_index]["snapshot"])
            if action_index < len(native_frames)
            else {}
        )
        if expected == actual:
            continue
        diffs = _field_diffs(expected, actual)
        failures.append(
            " | ".join(
                [
                    f"case={case_id}",
                    f"mode={case['dimension']}d",
                    f"board_shape={list(case['board_shape'])}",
                    f"piece_set={case['piece_set_id']}",
                    "random_mode=fixed_seed",
                    f"configured_seed={case['seed']}",
                    f"effective_seed={case['seed']}",
                    f"initial_speed={case['speed']}",
                    f"action_index={action_index - 1}",
                    f"action={action}",
                    f"expected_state={expected}",
                    f"actual_state={actual}",
                    f"expected_cells={expected.get('active_cells')}",
                    f"actual_cells={actual.get('active_cells')}",
                    f"expected_next_piece={expected.get('next_piece')}",
                    f"actual_next_piece={actual.get('next_piece')}",
                    f"expected_hash={native.get('final_hash')}",
                    f"actual_hash={native_frames[action_index]['snapshot'].get('state_hash') if action_index < len(native_frames) else None}",
                    f"diffs={diffs[:12]}",
                ]
            )
        )
    if not native.get("restart_matches_initial", False):
        failures.append(f"case={case_id}: restart did not reproduce the initial native state hash")
    return failures


def plain_2d_cases() -> list[str]:
    return [
        case.case_id for case in GAMEPLAY_TRACE_CASES if case.case_id in PLAIN_2D_CASES
    ]


def plain_nd_cases() -> list[str]:
    return [
        case.case_id for case in GAMEPLAY_TRACE_CASES if case.case_id in PLAIN_ND_CASES
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compare native C++ gameplay trace output with Python golden traces."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--case")
    group.add_argument(
        "--all-plain-2d",
        action="store_true",
        help="compare every Stage 11 plain 2D C++ parity case",
    )
    group.add_argument(
        "--all-plain-nd",
        action="store_true",
        help="compare every Stage 15 plain bounded 3D/4D C++ parity case",
    )
    group.add_argument(
        "--all-configurable",
        action="store_true",
        help="compare Stage 49 alternate-size 2D/3D/4D cases",
    )
    group.add_argument(
        "--all-plain-setup",
        action="store_true",
        help="compare Stage 50 canonical setup sessions against the Python oracle",
    )
    parser.add_argument("--golden-dir", type=Path, default=DEFAULT_GOLDEN_DIR)
    args = parser.parse_args(argv)

    if args.all_plain_setup:
        failures = []
        for case_id in sorted(PLAIN_SETUP_CASES):
            failures.extend(compare_setup_case(case_id))
        if failures:
            for failure in failures:
                print(failure, file=sys.stderr)
            return 1
        print(
            "C++ plain setup parity passed for "
            + ", ".join(sorted(PLAIN_SETUP_CASES))
            + " (including deterministic native restart hashes)"
        )
        return 0
    if args.all_configurable:
        case_ids = [
            case.case_id
            for case in GAMEPLAY_TRACE_CASES
            if case.case_id in CONFIGURABLE_CASES
        ]
    elif args.all_plain_2d:
        case_ids = plain_2d_cases()
    elif args.all_plain_nd:
        case_ids = plain_nd_cases()
    else:
        case_ids = [args.case]
    failures: list[str] = []
    for case_id in case_ids:
        failures.extend(compare_case(case_id, args.golden_dir))
    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    print(
        "C++ gameplay parity passed for "
        + ", ".join(case_ids)
        + " (including state_hash)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
