from __future__ import annotations

import argparse
import copy
import random
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tet4d.engine.core.model import BoardND
from tet4d.engine.gameplay.game2d import GameConfig, GameState
from tet4d.engine.gameplay.game_nd import GameConfigND, GameStateND
from tet4d.engine.gameplay.pieces2d import ActivePiece2D, PieceShape2D
from tet4d.engine.gameplay.pieces_nd import ActivePieceND, PieceShapeND
from tet4d.engine.gameplay.play_move_intents import crosses_gravity_seam
from tet4d.engine.runtime.topology_playground_launch import (
    build_gameplay_config_from_topology_playground_state,
)
from tet4d.engine.runtime.topology_playground_state import (
    default_topology_playground_state,
)
from tet4d.engine.topology_explorer import MoveStep
from tet4d.engine.topology_explorer.transport_resolver import (
    build_explorer_transport_resolver,
)
from tools.migration.trace_cases import (
    GAMEPLAY_CASES_BY_ID,
    GAMEPLAY_TRACE_CASES,
    GameplayTraceCase,
)
from tools.migration.trace_schema import (
    TRACE_VERSION,
    command_payload,
    coord_payload,
    coords_payload,
    frame_payload,
    generator_metadata,
    stable_hash,
    to_jsonable,
    trace_file_name,
    write_canonical_json,
)


DEFAULT_GAMEPLAY_TRACE_OUT = Path("migration/golden_traces/gameplay")


def _profile_payload(profile: Any) -> dict[str, Any] | None:
    if profile is None:
        return None
    return {
        "dimension": profile.dimension,
        "gluings": [
            {
                "enabled": bool(glue.enabled),
                "glue_id": glue.glue_id,
                "source": glue.source.label,
                "target": glue.target.label,
                "transform": {
                    "permutation": list(glue.transform.permutation),
                    "signs": list(glue.transform.signs),
                },
            }
            for glue in sorted(profile.gluings, key=lambda item: item.glue_id)
        ],
    }


def _settings_payload(config: GameConfig | GameConfigND) -> dict[str, Any]:
    if isinstance(config, GameConfig):
        dims = (config.width, config.height)
        piece_set = config.piece_set
    else:
        dims = tuple(config.dims)
        piece_set = config.piece_set_id
    profile_payload = _profile_payload(config.explorer_topology_profile)
    return {
        "axis_sizes": list(dims),
        "exploration_mode": bool(config.exploration_mode),
        "explorer_profile_digest": None
        if profile_payload is None
        else stable_hash(profile_payload),
        "explorer_rigid_play_enabled": config.explorer_rigid_play_enabled,
        "gravity_axis": config.gravity_axis,
        "piece_set": piece_set,
        "topology_mode": config.topology_mode,
        "wrap_gravity_axis": config.wrap_gravity_axis,
    }


def _active_piece_payload(state: GameState | GameStateND) -> dict[str, Any] | None:
    piece = state.current_piece
    if piece is None:
        return None
    payload = {
        "cells": coords_payload(state.current_piece_cells_mapped(include_above=True)),
        "color_id": int(piece.shape.color_id),
        "pos": coord_payload(piece.pos),
        "shape": piece.shape.name,
    }
    if isinstance(piece, ActivePiece2D):
        payload["blocks"] = coords_payload(piece.shape.blocks)
        payload["rotation"] = int(piece.rotation)
    else:
        payload["rel_blocks"] = coords_payload(piece.rel_blocks)
        payload["last_rotation_plane"] = coord_payload(piece.last_rotation_plane)
        payload["last_rotation_steps"] = int(piece.last_rotation_steps)
    return payload


def _locked_cells_payload(state: GameState | GameStateND) -> list[dict[str, Any]]:
    return [
        {"coord": coord_payload(coord), "value": int(value)}
        for coord, value in sorted(state.board.cells.items())
    ]


def _topology_event_for_command(
    state: GameState | GameStateND,
    command: dict[str, Any],
) -> dict[str, Any] | None:
    config = state.config
    transport = getattr(config, "explorer_transport", None)
    piece = state.current_piece
    if transport is None or piece is None:
        return None
    action = str(command.get("action"))
    axis: int | None = None
    delta: int | None = None
    intent = action
    if action == "move_axis":
        axis = int(command["axis"])
        delta = int(command["delta"])
        intent = "translation"
    elif action == "move" and isinstance(state, GameState):
        dx, dy = [int(value) for value in command["delta"]]
        non_zero = [(0, dx), (1, dy)]
        non_zero = [(axis, step) for axis, step in non_zero if step != 0]
        if len(non_zero) == 1 and abs(non_zero[0][1]) == 1:
            axis, delta = non_zero[0]
            intent = "translation"
    elif action in {"soft_drop", "gravity_step", "hard_drop"}:
        axis = int(config.gravity_axis)
        delta = 1
        intent = action
    if axis is None or delta is None or abs(delta) != 1:
        return None
    step = MoveStep(axis=axis, delta=delta)
    piece_step = transport.resolve_piece_step(piece.cells(), step)
    return {
        "crosses_gravity_seam": crosses_gravity_seam(
            piece_step,
            gravity_axis=config.gravity_axis,
        ),
        "intent": intent,
        "kind": piece_step.kind,
        "moved_cells": coords_payload(piece_step.moved_cells or ()),
        "rigidly_coherent": bool(piece_step.rigidly_coherent),
        "source_cells": coords_payload(piece.cells()),
        "step": {"axis": axis, "delta": delta, "label": step.label},
        "traversals": [
            None
            if cell.traversal is None
            else {
                "destination_boundary": cell.traversal.target_boundary.label,
                "glue_id": cell.traversal.glue_id,
                "source_boundary": cell.traversal.source_boundary.label,
            }
            for cell in piece_step.cell_steps
        ],
    }


def _state_snapshot(state: GameState | GameStateND) -> dict[str, Any]:
    locked_cells = _locked_cells_payload(state)
    payload = {
        "active_piece": _active_piece_payload(state),
        "game_over": bool(state.game_over),
        "legal_moves": _legal_moves_summary(state),
        "level": None,
        "lines": int(state.lines_cleared),
        "locked_cell_count": len(locked_cells),
        "locked_cell_digest": stable_hash(locked_cells),
        "locked_cells": locked_cells,
        "score": int(state.score),
    }
    if isinstance(state, GameStateND):
        payload["piece_frame"] = {
            "permutation": list(state._piece_frame_permutation),
            "signs": list(state._piece_frame_signs),
        }
    return payload


def _legal_moves_summary(state: GameState | GameStateND) -> dict[str, Any]:
    if state.current_piece is None:
        return {"has_active_piece": False}
    probes: dict[str, Any] = {}
    if isinstance(state, GameState):
        for name, args in (
            ("x-", (-1, 0)),
            ("x+", (1, 0)),
            ("soft_drop", (0, 1)),
        ):
            clone = copy.deepcopy(state)
            probes[name] = (
                bool(clone.try_move(*args))
                if name != "soft_drop"
                else bool(clone.try_soft_drop())
            )
    else:
        for axis in range(state.config.ndim):
            for delta in (-1, 1):
                clone = copy.deepcopy(state)
                probes[f"{axis}:{delta}"] = bool(clone.try_move_axis(axis, delta))
        clone = copy.deepcopy(state)
        probes["soft_drop"] = bool(clone.try_soft_drop())
    return {
        "has_active_piece": True,
        "moves": probes,
    }


def _build_config(case: GameplayTraceCase) -> GameConfig | GameConfigND:
    if case.launch_from_playground:
        if case.topology_profile_factory is None:
            raise ValueError("launch trace case requires topology_profile_factory")
        playground_state = default_topology_playground_state(
            dimension=case.dimension,
            axis_sizes=case.dims,
        )
        playground_state.topology_config.explorer_profile = (
            case.topology_profile_factory()
        )
        return build_gameplay_config_from_topology_playground_state(playground_state)
    if case.dimension == 2:
        return GameConfig(
            width=case.dims[0],
            height=case.dims[1],
            topology_mode=case.legacy_topology_mode,
            wrap_gravity_axis=case.wrap_gravity_axis,
            rng_seed=case.seed,
        )
    return GameConfigND(
        dims=case.dims,
        topology_mode=case.legacy_topology_mode,
        wrap_gravity_axis=case.wrap_gravity_axis,
        rng_seed=case.seed,
    )


def _build_state(
    case: GameplayTraceCase, config: GameConfig | GameConfigND
) -> GameState | GameStateND:
    rng = random.Random(case.seed)
    if isinstance(config, GameConfig):
        state = GameState(
            config=config, board=BoardND((config.width, config.height)), rng=rng
        )
        shape = PieceShape2D(
            name=f"TRACE_{case.dimension}D",
            blocks=[
                tuple(int(value) for value in block) for block in case.piece_blocks
            ],
            color_id=8,
        )
        pos = case.piece_pos if case.piece_pos is not None else (config.width // 2, 1)
        state.current_piece = ActivePiece2D(shape=shape, pos=tuple(pos), rotation=0)
    else:
        state = GameStateND(config=config, board=BoardND(config.dims), rng=rng)
        shape = PieceShapeND(
            name=f"TRACE_{case.dimension}D",
            blocks=tuple(
                tuple(int(value) for value in block) for block in case.piece_blocks
            ),
            color_id=8,
        )
        pos = (
            case.piece_pos
            if case.piece_pos is not None
            else tuple(size // 2 for size in config.dims)
        )
        state.current_piece = ActivePieceND.from_shape(shape=shape, pos=tuple(pos))
    state.board.cells.clear()
    state.game_over = False
    return state


def _apply_command(
    state: GameState | GameStateND, command: dict[str, Any]
) -> dict[str, Any]:
    before_locked = len(state.board.cells)
    before_active = coords_payload(
        state.current_piece_cells_mapped(include_above=True)
        if state.current_piece is not None
        else ()
    )
    action = str(command["action"])
    result = (
        _apply_2d_command(state, action, command)
        if isinstance(state, GameState)
        else _apply_nd_command(state, action, command)
    )
    return {
        "active_cells_before": before_active,
        "locked_cell_delta": len(state.board.cells) - before_locked,
        "return_value": to_jsonable(result),
    }


def _apply_2d_command(
    state: GameState,
    action: str,
    command: dict[str, Any],
) -> Any:
    if action == "move":
        dx, dy = [int(value) for value in command["delta"]]
        return state.try_move(dx, dy)
    if action == "soft_drop":
        return state.try_soft_drop()
    if action == "hard_drop":
        state.hard_drop()
        return None
    if action == "gravity_step":
        state.step_gravity()
        return None
    if action == "rotate":
        state.try_rotate(int(command.get("delta", 1)))
        return None
    raise ValueError(f"unsupported 2D gameplay action: {action}")


def _apply_nd_command(
    state: GameStateND,
    action: str,
    command: dict[str, Any],
) -> Any:
    if action == "move_axis":
        return state.try_move_axis(int(command["axis"]), int(command["delta"]))
    if action == "soft_drop":
        return state.try_soft_drop()
    if action == "hard_drop":
        state.hard_drop()
        return None
    if action == "gravity_step":
        state.step_gravity()
        return None
    if action == "rotate":
        return state.try_rotate(
            int(command.get("axis_a", 0)),
            int(command.get("axis_b", state.config.gravity_axis)),
            int(command.get("delta", 1)),
        )
    raise ValueError(f"unsupported ND gameplay action: {action}")


def _launch_parity_payload(
    case: GameplayTraceCase, config: GameConfig | GameConfigND
) -> dict[str, Any] | None:
    if not case.launch_from_playground or case.topology_profile_factory is None:
        return None
    profile = case.topology_profile_factory()
    profile_payload = _profile_payload(profile)
    cfg_profile_payload = _profile_payload(config.explorer_topology_profile)
    parity = {
        "config_profile_digest": stable_hash(cfg_profile_payload),
        "configured_transport_dims": list(config.explorer_transport.dims),
        "playground_profile_digest": stable_hash(profile_payload),
        "profile_digest_equal": profile_payload == cfg_profile_payload,
    }
    first_command = case.commands[0] if case.commands else None
    if first_command is not None and str(first_command.get("action")) == "move_axis":
        step = MoveStep(
            axis=int(first_command["axis"]), delta=int(first_command["delta"])
        )
        piece_cells = (case.piece_pos,)
        expected = build_explorer_transport_resolver(
            profile, case.dims
        ).resolve_piece_step(
            piece_cells,
            step,
        )
        actual = config.explorer_transport.resolve_piece_step(piece_cells, step)
        parity["first_transport_equal"] = (
            coords_payload(expected.moved_cells or ())
            == coords_payload(actual.moved_cells or ())
            and expected.kind == actual.kind
        )
    return parity


def build_gameplay_trace(case: GameplayTraceCase) -> dict[str, Any]:
    config = _build_config(case)
    state = _build_state(case, config)
    settings = _settings_payload(config)
    initial_snapshot = _state_snapshot(state)
    commands = [
        command_payload(
            command["id"],
            **{key: value for key, value in command.items() if key != "id"},
        )
        for command in case.commands
    ]
    frames: list[dict[str, Any]] = []
    for index, command in enumerate(case.commands):
        topology_event = _topology_event_for_command(state, command)
        command_result = _apply_command(state, command)
        snapshot = _state_snapshot(state)
        frames.append(
            frame_payload(
                index,
                command_id=command["id"],
                command={
                    key: to_jsonable(value) for key, value in sorted(command.items())
                },
                command_result=command_result,
                active_piece=snapshot["active_piece"],
                drop_lock_status={
                    "game_over": snapshot["game_over"],
                    "locked_cell_count": snapshot["locked_cell_count"],
                    "locked_cell_delta": command_result["locked_cell_delta"],
                    "soft_drop_legal_after": snapshot["legal_moves"]["moves"].get(
                        "soft_drop"
                    )
                    if snapshot["legal_moves"].get("has_active_piece")
                    else None,
                },
                legal_moves=snapshot["legal_moves"],
                lines=snapshot["lines"],
                locked_cell_digest=snapshot["locked_cell_digest"],
                locked_cells=snapshot["locked_cells"],
                score=snapshot["score"],
                topology_event=topology_event,
            )
        )
    final_snapshot = _state_snapshot(state)
    trace = {
        "case_id": case.case_id,
        "commands": commands,
        "dimension": case.dimension,
        "final": {},
        "frames": frames,
        "generator": generator_metadata("export_gameplay_trace"),
        "initial": {
            "active_piece": initial_snapshot["active_piece"],
            "board_shape": list(case.dims),
            "launch_parity": _launch_parity_payload(case, config),
            "locked_cells": initial_snapshot["locked_cells"],
            "notes": list(case.notes),
            "settings": settings,
            "settings_digest": stable_hash(settings),
        },
        "seed": case.seed,
        "topology_id": case.topology_id,
        "trace_type": "gameplay",
        "trace_version": TRACE_VERSION,
    }
    trace["final"] = {
        "locked_cell_count": final_snapshot["locked_cell_count"],
        "locked_cell_digest": final_snapshot["locked_cell_digest"],
        "score": final_snapshot["score"],
        "state_hash": stable_hash(
            {
                "case_id": case.case_id,
                "final_snapshot": final_snapshot,
                "frames": frames,
            }
        ),
    }
    return trace


def export_case(case: GameplayTraceCase, out_dir: Path) -> Path:
    return write_canonical_json(
        out_dir / trace_file_name(case.case_id),
        build_gameplay_trace(case),
    )


def export_cases(cases: list[GameplayTraceCase], out_dir: Path) -> list[Path]:
    return [export_case(case, out_dir) for case in cases]


def _selected_cases(args: argparse.Namespace) -> list[GameplayTraceCase]:
    if args.all:
        return list(GAMEPLAY_TRACE_CASES)
    if args.case is None:
        raise SystemExit("use --all or --case CASE_ID")
    case = GAMEPLAY_CASES_BY_ID.get(args.case)
    if case is None:
        raise SystemExit(f"unknown gameplay trace case: {args.case}")
    return [case]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export Python-authoritative gameplay traces."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--all", action="store_true", help="export all gameplay trace cases"
    )
    group.add_argument("--case", help="export a single gameplay trace case")
    parser.add_argument("--out", type=Path, default=DEFAULT_GAMEPLAY_TRACE_OUT)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    paths = export_cases(_selected_cases(args), args.out)
    if not args.quiet:
        for path in paths:
            print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
