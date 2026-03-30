#!/usr/bin/env python3
# ruff: noqa: E402
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from contextlib import ExitStack
from pathlib import Path
from statistics import mean
from types import SimpleNamespace
from unittest import mock

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

if not os.environ.get("SDL_VIDEODRIVER"):
    os.environ["SDL_VIDEODRIVER"] = "dummy"

try:
    import pygame
except ModuleNotFoundError as exc:  # pragma: no cover - runtime environment dependent
    raise SystemExit("pygame-ce is required for startup profiling") from exc

from tet4d.engine.runtime.topology_explorer_runtime import (
    compile_runtime_explorer_experiments,
)
from tet4d.engine.runtime.settings_schema import atomic_write_text
from tet4d.engine.runtime.topology_explorer_store import load_explorer_topology_profile
from tet4d.engine.runtime import topology_playability_signal as playability_mod
from tet4d.engine.runtime import topology_explorer_preview as preview_mod
from tet4d.engine.topology_explorer import movement_graph as graph_mod
from tet4d.engine.topology_explorer.presets import explorer_presets_for_dimension
from tet4d.ui.pygame.launch import topology_lab_menu
from tet4d.ui.pygame.launch import topology_lab_state_factory as factory_mod
from tet4d.ui.pygame.topology_lab import app as app_mod
from tet4d.ui.pygame.topology_lab import controls_panel as controls_panel_mod
from tet4d.ui.pygame.topology_lab import piece_sandbox as piece_sandbox_mod
from tet4d.ui.pygame.topology_lab import scene_preview_state as scene_preview_mod
from tet4d.ui.pygame.topology_lab import scene_state as scene_state_mod
from tet4d.ui.pygame.topology_lab.app import build_explorer_playground_launch
from tet4d.ui.pygame.topology_lab.scene_state import playground_dims_for_state

_REPRESENTATIVE_PRESET_IDS = {
    2: "torus_2d",
    3: "full_wrap_3d",
    4: "full_wrap_4d",
}


def _resolve_repo_local_path(raw: Path) -> Path:
    candidate = (raw if raw.is_absolute() else (_REPO_ROOT / raw)).resolve()
    root = _REPO_ROOT.resolve()
    if candidate == root or root in candidate.parents:
        return candidate
    raise SystemExit(f"output path must stay within project root: {root}")


def _parse_dimensions(raw: str) -> tuple[int, ...]:
    dimensions = tuple(int(part.strip()) for part in raw.split(",") if part.strip())
    if not dimensions:
        raise SystemExit("--dimensions must contain at least one dimension")
    if any(dimension not in _REPRESENTATIVE_PRESET_IDS for dimension in dimensions):
        raise SystemExit("--dimensions must only contain 2, 3, and/or 4")
    return dimensions


def _matching_preset_id(dimension: int, profile) -> str | None:
    for preset in explorer_presets_for_dimension(dimension):
        if preset.profile == profile:
            return preset.preset_id
    return None


def _representative_profile(dimension: int):
    target_preset_id = _REPRESENTATIVE_PRESET_IDS[int(dimension)]
    for preset in explorer_presets_for_dimension(int(dimension)):
        if preset.preset_id == target_preset_id:
            return preset.profile
    raise SystemExit(
        f"representative preset {target_preset_id!r} not found for {dimension}D"
    )


def _fonts() -> SimpleNamespace:
    return SimpleNamespace(
        title_font=pygame.font.Font(None, 36),
        menu_font=pygame.font.Font(None, 28),
        hint_font=pygame.font.Font(None, 22),
    )


def _summarize_records(
    records: dict[str, dict[str, float | int]],
) -> dict[str, dict[str, float | int]]:
    return {
        key: {
            "count": int(value["count"]),
            "total_ms": round(float(value["total_ms"]), 3),
            "avg_ms": round(float(value["total_ms"]) / max(1, int(value["count"])), 3),
        }
        for key, value in sorted(records.items())
    }


def _summarize_graph_calls(items: list[dict[str, object]]) -> dict[str, object]:
    unique = {
        (
            tuple(str(glue_id) for glue_id in item["glue_ids"]),
            tuple(int(value) for value in item["dims"]),
        )
        for item in items
    }
    return {
        "calls": len(items),
        "unique_signatures": len(unique),
        "samples": items[:6],
    }


def _summarize_validation_calls(items: list[dict[str, object]]) -> dict[str, object]:
    unique = {
        (int(item["glue_count"]), tuple(int(value) for value in item["dims"]))
        for item in items
    }
    return {
        "calls": len(items),
        "unique_signatures": len(unique),
        "avg_ms": round(
            mean(float(item["elapsed_ms"]) for item in items),
            6,
        )
        if items
        else 0.0,
    }


def _measure_dimension(
    *,
    dimension: int,
    surface: pygame.Surface,
    fonts: SimpleNamespace,
) -> dict[str, object]:
    phase = "startup"
    records: dict[str, dict[str, dict[str, float | int]]] = {
        "startup": {},
        "repeat_refresh": {},
        "manual": {},
    }
    graph_signatures: dict[str, list[dict[str, object]]] = {
        "startup": [],
        "repeat_refresh": [],
        "manual": [],
    }
    validation_signatures: dict[str, list[dict[str, object]]] = {
        "startup": [],
        "repeat_refresh": [],
        "manual": [],
    }

    def record(name: str, elapsed_ms: float) -> None:
        entry = records[phase].setdefault(name, {"count": 0, "total_ms": 0.0})
        entry["count"] = int(entry["count"]) + 1
        entry["total_ms"] = float(entry["total_ms"]) + float(elapsed_ms)

    def patch_callable(name: str, module: object, attr_name: str, *, after=None):
        original = getattr(module, attr_name)

        def wrapped(*args, **kwargs):
            start = time.perf_counter()
            try:
                return original(*args, **kwargs)
            finally:
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                record(name, elapsed_ms)
                if after is not None:
                    after(args, kwargs, elapsed_ms)

        return mock.patch.object(module, attr_name, new=wrapped)

    def after_build_graph(args, kwargs, elapsed_ms: float) -> None:
        profile = args[0]
        dims = tuple(
            int(value) for value in kwargs.get("dims", args[1] if len(args) > 1 else ())
        )
        graph_signatures[phase].append(
            {
                "glue_ids": [glue.glue_id for glue in profile.gluings],
                "dims": list(dims),
                "elapsed_ms": round(elapsed_ms, 3),
            }
        )

    def after_validate(args, kwargs, elapsed_ms: float) -> None:
        profile = args[0]
        dims = tuple(
            int(value) for value in kwargs.get("dims", args[1] if len(args) > 1 else ())
        )
        validation_signatures[phase].append(
            {
                "glue_count": len(profile.gluings),
                "dims": list(dims),
                "elapsed_ms": round(elapsed_ms, 6),
            }
        )

    stored_profile = load_explorer_topology_profile(dimension)
    launch_profile = _representative_profile(dimension)

    with ExitStack() as stack:
        stack.enter_context(
            patch_callable(
                "app._profile_validation_error",
                app_mod,
                "_profile_validation_error",
            )
        )
        stack.enter_context(
            patch_callable(
                "factory.load_topology_profile",
                factory_mod,
                "load_topology_profile",
            )
        )
        stack.enter_context(
            patch_callable(
                "ss.recommended_explorer_probe_coord",
                scene_state_mod,
                "recommended_explorer_probe_coord",
            )
        )
        stack.enter_context(
            patch_callable(
                "cp.sync_canonical_playground_state",
                controls_panel_mod,
                "sync_canonical_playground_state",
            )
        )
        stack.enter_context(
            patch_callable(
                "menu._sync_canonical_playground_state",
                topology_lab_menu,
                "_sync_canonical_playground_state",
            )
        )
        stack.enter_context(
            patch_callable(
                "scene_preview._compile_explorer_preview_payload",
                scene_preview_mod,
                "_compile_explorer_preview_payload",
            )
        )
        stack.enter_context(
            patch_callable(
                "menu.ensure_piece_sandbox",
                topology_lab_menu,
                "ensure_piece_sandbox",
            )
        )
        stack.enter_context(
            patch_callable(
                "piece.ensure_piece_sandbox_state",
                piece_sandbox_mod,
                "ensure_piece_sandbox_state",
            )
        )
        stack.enter_context(
            patch_callable(
                "menu._refresh_explorer_scene_state",
                topology_lab_menu,
                "_refresh_explorer_scene_state",
            )
        )
        stack.enter_context(
            patch_callable(
                "menu._draw_explorer_workspace",
                topology_lab_menu,
                "_draw_explorer_workspace",
            )
        )
        stack.enter_context(
            patch_callable(
                "menu._draw_explorer_scene",
                topology_lab_menu,
                "_draw_explorer_scene",
            )
        )
        stack.enter_context(
            patch_callable(
                "cp.explorer_presets_for_dimension",
                controls_panel_mod,
                "explorer_presets_for_dimension",
            )
        )
        stack.enter_context(
            patch_callable(
                "ss.designer_profiles_for_dimension",
                scene_state_mod,
                "designer_profiles_for_dimension",
            )
        )
        stack.enter_context(
            patch_callable(
                "ss.explorer_presets_for_dimension",
                scene_state_mod,
                "explorer_presets_for_dimension",
            )
        )
        stack.enter_context(
            patch_callable(
                "preview.build_movement_graph",
                preview_mod,
                "build_movement_graph",
                after=after_build_graph,
            )
        )
        stack.enter_context(
            patch_callable(
                "preview.basis_arrow_payload",
                preview_mod,
                "basis_arrow_payload",
            )
        )
        stack.enter_context(
            patch_callable(
                "graph.validate_explorer_topology_profile",
                graph_mod,
                "validate_explorer_topology_profile",
                after=after_validate,
            )
        )
        stack.enter_context(
            patch_callable(
                "scene_preview.update_topology_playability_analysis",
                scene_preview_mod,
                "update_topology_playability_analysis",
            )
        )
        stack.enter_context(
            patch_callable(
                "playability._first_rigid_transport_failure",
                playability_mod,
                "_first_rigid_transport_failure",
            )
        )

        start = time.perf_counter()
        launch = build_explorer_playground_launch(
            dimension=dimension,
            explorer_profile=launch_profile,
            entry_source="explorer",
        )
        launch_ms = (time.perf_counter() - start) * 1000.0

        start = time.perf_counter()
        state = topology_lab_menu._initial_topology_lab_state(
            launch.dimension,
            gameplay_mode=launch.gameplay_mode,
            initial_explorer_profile=launch.explorer_profile,
            initial_tool=launch.initial_tool,
            play_settings=launch.settings_snapshot,
        )
        init_ms = (time.perf_counter() - start) * 1000.0

        start = time.perf_counter()
        topology_lab_menu._draw_menu(surface, fonts, state)
        draw_ms = (time.perf_counter() - start) * 1000.0

        phase = "repeat_refresh"
        repeat_refresh_ms: list[float] = []
        for _ in range(2):
            start = time.perf_counter()
            topology_lab_menu._refresh_explorer_scene_state(state)
            repeat_refresh_ms.append(round((time.perf_counter() - start) * 1000.0, 3))

        phase = "manual"
        start = time.perf_counter()
        experiments = compile_runtime_explorer_experiments(
            state.explorer_profile,
            dims=playground_dims_for_state(state),
            source=f"topology_playground_startup_audit_{dimension}d",
        )
        manual_playability_ms = (time.perf_counter() - start) * 1000.0

    return {
        "dimension": int(dimension),
        "board_dims": list(launch.settings_snapshot.board_dims),
        "stored_profile": {
            "matching_preset_id": _matching_preset_id(dimension, stored_profile),
            "glue_ids": [glue.glue_id for glue in stored_profile.gluings],
        },
        "launch_profile": {
            "matching_preset_id": _matching_preset_id(dimension, launch_profile),
            "glue_ids": [glue.glue_id for glue in launch_profile.gluings],
        },
        "launch_ms": round(launch_ms, 3),
        "init_ms": round(init_ms, 3),
        "draw_ms": round(draw_ms, 3),
        "first_frame_ready_ms": round(launch_ms + init_ms + draw_ms, 3),
        "active_tool": str(state.active_tool),
        "startup": {
            "records": _summarize_records(records["startup"]),
            "movement_graph": _summarize_graph_calls(graph_signatures["startup"]),
            "validation": _summarize_validation_calls(validation_signatures["startup"]),
        },
        "repeat_refresh": {
            "refresh_ms": repeat_refresh_ms,
            "records": _summarize_records(records["repeat_refresh"]),
            "movement_graph": _summarize_graph_calls(
                graph_signatures["repeat_refresh"]
            ),
            "validation": _summarize_validation_calls(
                validation_signatures["repeat_refresh"]
            ),
        },
        "manual_playability_analysis": {
            "elapsed_ms": round(manual_playability_ms, 3),
            "experiment_count": int(experiments["experiment_count"]),
            "records": _summarize_records(records["manual"]),
            "movement_graph": _summarize_graph_calls(graph_signatures["manual"]),
            "validation": _summarize_validation_calls(validation_signatures["manual"]),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Profile Topology Playground startup through first interactive draw."
    )
    parser.add_argument(
        "--dimensions",
        default="2,3,4",
        help="Comma-separated dimensions to profile (subset of 2,3,4).",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1280,
        help="Offscreen surface width used for the first-frame draw.",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=900,
        help="Offscreen surface height used for the first-frame draw.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional JSON report path (must stay within project root).",
    )
    args = parser.parse_args()

    dimensions = _parse_dimensions(args.dimensions)
    if args.width <= 0 or args.height <= 0:
        raise SystemExit("--width and --height must be positive")

    pygame.init()
    try:
        if not pygame.font.get_init():
            pygame.font.init()
        surface = pygame.Surface((args.width, args.height))
        fonts = _fonts()
        report = {
            "version": 1,
            "tool": "scripts/profile_topology_playground_startup.py",
            "dimensions": list(dimensions),
            "results": [
                _measure_dimension(dimension=dimension, surface=surface, fonts=fonts)
                for dimension in dimensions
            ],
        }
    finally:
        pygame.quit()

    payload = json.dumps(report, indent=2)
    print(payload)
    if args.output is not None:
        output_path = _resolve_repo_local_path(args.output)
        atomic_write_text(output_path, payload + "\n")
        print(f"report written: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
