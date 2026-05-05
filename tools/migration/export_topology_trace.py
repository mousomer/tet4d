from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tet4d.engine.core.model import BoardND
from tet4d.engine.gameplay.game_nd import GameStateND
from tet4d.engine.gameplay.pieces_nd import ActivePieceND, PieceShapeND
from tet4d.engine.gameplay.play_move_intents import crosses_gravity_seam
from tet4d.engine.runtime.topology_explorer_preview import (
    advance_explorer_probe,
    compile_explorer_topology_preview,
)
from tet4d.engine.runtime.topology_playability_signal import (
    derive_topology_playability_analysis,
)
from tet4d.engine.runtime.topology_playground_launch import (
    build_gameplay_config_from_topology_playground_state,
)
from tet4d.engine.runtime.topology_playground_state import (
    default_topology_playground_state,
)
from tet4d.engine.topology_explorer import (
    ExplorerTopologyProfile,
    MoveStep,
    build_explorer_transport_resolver,
    movement_steps_for_dimension,
    validate_topology_bijection,
    validate_topology_structure,
)
from tools.migration.trace_cases import (
    TOPOLOGY_CASES_BY_ID,
    TOPOLOGY_TRACE_CASES,
    TopologyTraceCase,
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


DEFAULT_TOPOLOGY_TRACE_OUT = Path("migration/golden_traces/topology")


def _step_from_label(dimension: int, label: str) -> MoveStep:
    for step in movement_steps_for_dimension(dimension):
        if step.label == label:
            return step
    raise ValueError(f"unknown movement step for {dimension}D topology: {label!r}")


def _glue_payload(profile: ExplorerTopologyProfile) -> list[dict[str, Any]]:
    rows = []
    for glue in sorted(profile.gluings, key=lambda item: item.glue_id):
        rows.append(
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
        )
    return rows


def _analysis_payload(analysis: Any) -> dict[str, Any]:
    summary = analysis.movement_summary
    return {
        "errors": list(analysis.errors),
        "explorer_reason": analysis.explorer_reason,
        "explorer_usability": analysis.explorer_usability,
        "movement_summary": {
            "boundary_traversal_count": summary.boundary_traversal_count,
            "cell_count": summary.cell_count,
            "component_count": summary.component_count,
            "directed_edge_count": summary.directed_edge_count,
        },
        "recommended_next_preset": analysis.recommended_next_preset,
        "rigid_playability": analysis.rigid_playability,
        "rigid_reason": analysis.rigid_reason,
        "status": analysis.status,
        "summary": analysis.summary,
        "validity": analysis.validity,
        "validity_reason": analysis.validity_reason,
        "warnings": list(analysis.warnings),
    }


def _traversal_payload(traversal: Any) -> dict[str, Any] | None:
    if traversal is None:
        return None
    return {
        "destination_boundary": traversal.target_boundary.label,
        "glue_id": traversal.glue_id,
        "source_boundary": traversal.source_boundary.label,
    }


def _frame_transform_payload(transform: Any) -> dict[str, Any] | None:
    if transform is None:
        return None
    return {
        "permutation": list(transform.permutation),
        "signs": list(transform.signs),
        "translation": list(transform.translation),
    }


def _cell_step_payload(cell_step: Any) -> dict[str, Any]:
    return {
        "blocked": bool(cell_step.blocked),
        "from": coord_payload(cell_step.source),
        "to": coord_payload(cell_step.target),
        "frame_transform": _frame_transform_payload(cell_step.frame_transform),
        "piece_frame_transform": _frame_transform_payload(
            cell_step.piece_frame_transform
        ),
        "traversal": _traversal_payload(cell_step.traversal),
    }


def _piece_step_payload(piece_step: Any) -> dict[str, Any]:
    return {
        "cell_steps": [_cell_step_payload(step) for step in piece_step.cell_steps],
        "frame_transform": _frame_transform_payload(piece_step.frame_transform),
        "kind": piece_step.kind,
        "moved_cells": coords_payload(piece_step.moved_cells or ()),
        "rigidly_coherent": bool(piece_step.rigidly_coherent),
    }


def _preview_and_analysis(
    case: TopologyTraceCase,
    profile: ExplorerTopologyProfile,
) -> tuple[dict[str, Any] | None, str | None, dict[str, Any], dict[str, Any] | None]:
    state = default_topology_playground_state(
        dimension=case.dimension,
        axis_sizes=case.dims,
    )
    state.topology_config.explorer_profile = profile
    preview: dict[str, Any] | None = None
    preview_error: str | None = None
    try:
        validate_topology_structure(profile)
        validate_topology_bijection(profile, dims=case.dims)
        preview = compile_explorer_topology_preview(
            profile,
            dims=case.dims,
            source=f"migration:{case.case_id}",
            use_local_cache=False,
        )
    except ValueError as exc:
        preview_error = str(exc)
    analysis = derive_topology_playability_analysis(
        state,
        preview=preview,
        preview_error=preview_error,
        include_rigid_scan=True,
    )
    repeated = None
    if case.include_playability_repeat:
        second = derive_topology_playability_analysis(
            state,
            preview=preview,
            preview_error=preview_error,
            include_rigid_scan=True,
        )
        first_payload = _analysis_payload(analysis)
        second_payload = _analysis_payload(second)
        repeated = {
            "first_hash": stable_hash(first_payload),
            "repeat_hash": stable_hash(second_payload),
            "stable": first_payload == second_payload,
        }
    return preview, preview_error, _analysis_payload(analysis), repeated


def _play_policy_payload(
    case: TopologyTraceCase, profile: ExplorerTopologyProfile
) -> dict[str, Any]:
    if case.dimension < 3:
        return {"available": False, "reason": "play policy sample uses ND gameplay"}
    state = default_topology_playground_state(
        dimension=case.dimension,
        axis_sizes=case.dims,
    )
    state.topology_config.explorer_profile = profile
    cfg = build_gameplay_config_from_topology_playground_state(state)
    shape = PieceShapeND(
        name="TRACE_SINGLE",
        blocks=(tuple(0 for _ in range(case.dimension)),),
        color_id=9,
    )
    piece = ActivePieceND.from_shape(shape, case.probe_start)
    resolver_step = cfg.explorer_transport.resolve_piece_step(
        piece.cells(),
        MoveStep(axis=cfg.gravity_axis, delta=1),
    )
    translation_state = GameStateND(config=cfg, board=BoardND(cfg.dims))
    translation_state.board.cells.clear()
    translation_state.current_piece = piece
    translation_legal = translation_state.try_move_axis(cfg.gravity_axis, 1)

    drop_state = GameStateND(config=cfg, board=BoardND(cfg.dims))
    drop_state.board.cells.clear()
    drop_state.current_piece = piece
    soft_drop_legal = drop_state.try_soft_drop()

    gravity_state = GameStateND(config=cfg, board=BoardND(cfg.dims))
    gravity_state.board.cells.clear()
    gravity_state.current_piece = piece
    before_locked = len(gravity_state.board.cells)
    gravity_state.step_gravity()
    return {
        "available": True,
        "drop_intent_crosses_gravity_seam": crosses_gravity_seam(
            resolver_step,
            gravity_axis=cfg.gravity_axis,
        ),
        "gravity_axis": cfg.gravity_axis,
        "gravity_step_locked_cell_delta": len(gravity_state.board.cells)
        - before_locked,
        "gravity_step_locked_cells": coords_payload(gravity_state.board.cells.keys()),
        "initial_piece_cells": coords_payload(piece.cells()),
        "play_soft_drop_legal": bool(soft_drop_legal),
        "resolver_step": _piece_step_payload(resolver_step),
        "sandbox_translation_legal": bool(translation_legal),
        "translation_after_cells": coords_payload(
            translation_state.current_piece.cells()
            if translation_state.current_piece is not None
            else ()
        ),
    }


def build_topology_trace(case: TopologyTraceCase) -> dict[str, Any]:
    profile = case.profile_factory()
    preview, preview_error, diagnostics, repeated = _preview_and_analysis(case, profile)
    commands = [
        command_payload(command["id"], step=command["step"])
        for command in case.commands
    ]
    frames: list[dict[str, Any]] = []
    coord = tuple(int(value) for value in case.probe_start)
    permutation = tuple(range(case.dimension))
    signs = tuple(1 for _ in range(case.dimension))
    resolver = None
    resolver_error = None
    try:
        resolver = build_explorer_transport_resolver(profile, case.dims)
    except ValueError as exc:
        resolver_error = str(exc)

    for index, command in enumerate(case.commands):
        before_coord = coord
        before_frame = {"permutation": list(permutation), "signs": list(signs)}
        step = _step_from_label(case.dimension, command["step"])
        probe_result: dict[str, Any] | None = None
        piece_result: dict[str, Any] | None = None
        if resolver is not None:
            piece_step = resolver.resolve_piece_step((before_coord,), step)
            piece_result = _piece_step_payload(piece_step)
            coord, raw_probe_result = advance_explorer_probe(
                profile,
                dims=case.dims,
                coord=before_coord,
                step_label=step.label,
                frame_permutation=permutation,
                frame_signs=signs,
            )
            probe_result = to_jsonable(raw_probe_result)
            if "frame_permutation" in raw_probe_result:
                permutation = tuple(
                    int(value) for value in raw_probe_result["frame_permutation"]
                )
            if "frame_signs" in raw_probe_result:
                signs = tuple(int(value) for value in raw_probe_result["frame_signs"])
        frames.append(
            frame_payload(
                index,
                command_id=command["id"],
                attempted_move={
                    "axis": step.axis,
                    "delta": step.delta,
                    "label": step.label,
                },
                before={
                    "probe_coord": coord_payload(before_coord),
                    "probe_frame": before_frame,
                },
                after={
                    "probe_coord": coord_payload(coord),
                    "probe_frame": {
                        "permutation": list(permutation),
                        "signs": list(signs),
                    },
                },
                legal=probe_result is not None
                and not bool(probe_result.get("blocked")),
                probe_result=probe_result,
                piece_transport=piece_result,
                diagnostics=diagnostics,
            )
        )

    initial = {
        "axis_sizes": list(case.dims),
        "diagnostics": diagnostics,
        "glue_count": len(profile.gluings),
        "gluings": _glue_payload(profile),
        "notes": list(case.notes),
        "probe_coord": coord_payload(case.probe_start),
        "probe_frame": {
            "permutation": list(range(case.dimension)),
            "signs": [1 for _ in range(case.dimension)],
        },
        "preview_error": preview_error,
        "preview_summary": None
        if preview is None
        else {
            "boundary_traversal_count": preview["movement_graph"][
                "boundary_traversal_count"
            ],
            "component_count": preview["movement_graph"]["component_count"],
            "directed_edge_count": preview["movement_graph"]["directed_edge_count"],
        },
        "resolver_error": resolver_error,
    }
    if repeated is not None:
        initial["playability_repeat"] = repeated
    if case.include_play_policy:
        initial["play_vs_sandbox_policy"] = _play_policy_payload(case, profile)
    trace = {
        "case_id": case.case_id,
        "commands": commands,
        "dimension": case.dimension,
        "final": {},
        "frames": frames,
        "generator": generator_metadata("export_topology_trace"),
        "initial": initial,
        "seed": case.seed,
        "topology_id": case.topology_id,
        "trace_type": "topology",
        "trace_version": TRACE_VERSION,
    }
    trace["final"] = {
        "diagnostics_hash": stable_hash(diagnostics),
        "frame_count": len(frames),
        "state_hash": stable_hash(
            {
                "case_id": case.case_id,
                "diagnostics": diagnostics,
                "final_probe_coord": coord_payload(coord),
                "frames": frames,
            }
        ),
    }
    return trace


def export_case(case: TopologyTraceCase, out_dir: Path) -> Path:
    return write_canonical_json(
        out_dir / trace_file_name(case.case_id),
        build_topology_trace(case),
    )


def export_cases(cases: list[TopologyTraceCase], out_dir: Path) -> list[Path]:
    return [export_case(case, out_dir) for case in cases]


def _selected_cases(args: argparse.Namespace) -> list[TopologyTraceCase]:
    if args.all:
        return list(TOPOLOGY_TRACE_CASES)
    if args.case is None:
        raise SystemExit("use --all or --case CASE_ID")
    case = TOPOLOGY_CASES_BY_ID.get(args.case)
    if case is None:
        raise SystemExit(f"unknown topology trace case: {args.case}")
    return [case]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export Python-authoritative topology traces."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--all", action="store_true", help="export all topology trace cases"
    )
    group.add_argument("--case", help="export a single topology trace case")
    parser.add_argument("--out", type=Path, default=DEFAULT_TOPOLOGY_TRACE_OUT)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    paths = export_cases(_selected_cases(args), args.out)
    if not args.quiet:
        for path in paths:
            print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
