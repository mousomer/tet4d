from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tet4d.ui.pygame.locked_cell_explosion.model import (
    ExplosionSeedCell,
    ExplosionTopologyInput,
)
from tet4d.ui.pygame.locked_cell_explosion.simulation import (
    build_endgame_state,
    step_endgame_state,
    total_kinetic_energy_for_particles,
    velocity_norm_sq_sum_for_particles,
)
from tools.migration.trace_cases import (
    ENDGAME_CASES_BY_ID,
    ENDGAME_TRACE_CASES,
    EndgameTraceCase,
)
from tools.migration.trace_schema import (
    TRACE_VERSION,
    coords_payload,
    frame_payload,
    generator_metadata,
    stable_hash,
    to_jsonable,
    trace_file_name,
    write_canonical_json,
)


DEFAULT_ENDGAME_TRACE_OUT = Path("migration/golden_traces/endgame")
ENDGAME_FLOAT_PRECISION = 6


def _seed_cells(case: EndgameTraceCase) -> tuple[ExplosionSeedCell, ...]:
    return tuple(
        ExplosionSeedCell(
            source_coord=tuple(int(value) for value in coord),
            color_id=int(color_id),
            source_group_id=None if group_id is None else str(group_id),
        )
        for coord, color_id, group_id in case.locked_cells
    )


def _profile(case: EndgameTraceCase):
    return (
        None
        if case.topology_profile_factory is None
        else case.topology_profile_factory()
    )


def _state_settings(case: EndgameTraceCase) -> dict[str, object]:
    return {
        "boundary_response": case.boundary_response,
        "collision_mode": case.collision_mode,
        "diagnostics_mode": "summary",
        "endgame_live_cell_fraction": case.live_fraction,
        "sound_enabled": False,
        "speed_preset": case.speed_preset,
        "time_scale": 1.0,
    }


def _particle_payload(particle) -> dict[str, Any]:
    return {
        "active": bool(particle.active),
        "color_id": int(particle.color_id),
        "escaped": bool(particle.escaped),
        "mass": float(particle.collision_mass),
        "particle_id": int(particle.particle_id),
        "position": [float(value) for value in particle.position_nd],
        "radius": float(particle.collision_radius),
        "source_coord": [int(value) for value in particle.source_coord],
        "source_group_id": particle.source_group_id,
        "velocity": [float(value) for value in particle.velocity_nd],
    }


def _particles_payload(state) -> list[dict[str, Any]]:
    return [
        _particle_payload(particle)
        for particle in sorted(state.particles, key=lambda item: item.particle_id)
    ]


def _energy_payload(state) -> dict[str, Any]:
    return {
        "kinetic_energy": total_kinetic_energy_for_particles(tuple(state.particles)),
        "weighted_speed_sq_sum": velocity_norm_sq_sum_for_particles(
            tuple(state.particles),
            weighted_by_mass=True,
        ),
        "speed_sq_sum": velocity_norm_sq_sum_for_particles(tuple(state.particles)),
    }


def _event_payload(event) -> dict[str, Any]:
    payload = to_jsonable(event)
    return payload if isinstance(payload, dict) else {"event": payload}


def _apply_particle_overrides(state, case: EndgameTraceCase) -> None:
    by_id = {int(particle.particle_id): particle for particle in state.particles}
    for override in case.particle_overrides:
        particle = by_id[int(override["particle_id"])]
        if "position" in override:
            position = tuple(float(value) for value in override["position"])
            if len(position) != int(case.dimension):
                raise ValueError(
                    f"{case.case_id}: override position dimension mismatch"
                )
            particle.position_nd = position
        if "velocity" in override:
            velocity = tuple(float(value) for value in override["velocity"])
            if len(velocity) != int(case.dimension):
                raise ValueError(
                    f"{case.case_id}: override velocity dimension mismatch"
                )
            particle.velocity_nd = velocity
    state.velocity_norm_sq_sum = velocity_norm_sq_sum_for_particles(state.particles)
    state.total_kinetic_energy = total_kinetic_energy_for_particles(state.particles)


def _topology_payload(
    case: EndgameTraceCase, topology: ExplosionTopologyInput
) -> dict[str, Any]:
    profile = topology.explorer_topology_profile
    return {
        "board_shape": list(topology.board_dims),
        "profile_digest": None
        if profile is None
        else stable_hash(
            {
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
        ),
        "topology_id": case.topology_id,
    }


def build_endgame_trace(case: EndgameTraceCase) -> dict[str, Any]:
    topology = ExplosionTopologyInput(
        board_dims=tuple(int(value) for value in case.dims),
        explorer_topology_profile=_profile(case),
    )
    source_cells = _seed_cells(case)
    state = build_endgame_state(
        locked_cells=source_cells,
        board_shape=case.dims,
        dimension=case.dimension,
        topology=topology,
        preset=case.preset,
        seed=case.seed,
        settings=_state_settings(case),
    )
    _apply_particle_overrides(state, case)
    initial_particles = _particles_payload(state)
    initial = {
        "energy": _energy_payload(state),
        "full_locked_cells": [
            {
                "color_id": int(cell.color_id),
                "source_coord": [int(value) for value in cell.source_coord],
                "source_group_id": cell.source_group_id,
            }
            for cell in source_cells
        ],
        "particle_count": len(state.particles),
        "particles": initial_particles,
        "selected_live_cells": coords_payload(
            particle.source_coord for particle in state.particles
        ),
        "state_hash": stable_hash(
            {"energy": _energy_payload(state), "particles": initial_particles}
        ),
    }
    frames: list[dict[str, Any]] = []
    for index in range(int(case.frame_count)):
        step_endgame_state(state, dt_ms=float(case.dt_ms), time_scale=1.0)
        particles = _particles_payload(state)
        energy = _energy_payload(state)
        events = [_event_payload(event) for event in state.last_step_events]
        frames.append(
            frame_payload(
                index,
                elapsed_ms=float(state.elapsed_ms),
                energy=energy,
                events=events,
                particles=particles,
            )
        )
    final_particles = _particles_payload(state)
    final_energy = _energy_payload(state)
    final = {
        "energy": final_energy,
        "particle_count": len(final_particles),
        "state_hash": stable_hash(
            {"energy": final_energy, "particles": final_particles}
        ),
    }
    return {
        "trace_type": "endgame",
        "trace_version": TRACE_VERSION,
        "case_id": case.case_id,
        "dimension": int(case.dimension),
        "board_shape": list(case.dims),
        "topology_preset": case.preset,
        "topology": _topology_payload(case, topology),
        "collision_mode": case.collision_mode,
        "speed_preset": case.speed_preset,
        "seed": int(case.seed),
        "generator": generator_metadata("export_endgame_trace"),
        "float_precision": ENDGAME_FLOAT_PRECISION,
        "notes": list(case.notes),
        "initial": to_jsonable(initial),
        "frames": to_jsonable(frames),
        "final": to_jsonable(final),
    }


def export_cases(cases: list[EndgameTraceCase], out_dir: Path) -> list[Path]:
    paths: list[Path] = []
    for case in cases:
        path = out_dir / trace_file_name(case.case_id)
        paths.append(write_canonical_json(path, build_endgame_trace(case)))
    return paths


def _selected_cases(args: argparse.Namespace) -> list[EndgameTraceCase]:
    if args.all:
        return list(ENDGAME_TRACE_CASES)
    if args.case:
        case = ENDGAME_CASES_BY_ID.get(args.case)
        if case is None:
            raise SystemExit(f"unknown endgame trace case: {args.case}")
        return [case]
    raise SystemExit("choose --all or --case CASE_ID")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export deterministic locked-cell endgame golden traces."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true")
    group.add_argument("--case")
    parser.add_argument("--out", type=Path, default=DEFAULT_ENDGAME_TRACE_OUT)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    paths = export_cases(_selected_cases(args), args.out)
    if not args.quiet:
        for path in paths:
            print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
