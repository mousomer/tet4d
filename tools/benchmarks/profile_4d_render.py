#!/usr/bin/env python3
# ruff: noqa: E402
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Benchmark renders into offscreen surfaces only; prefer headless-safe SDL defaults.
if not os.environ.get("SDL_VIDEODRIVER"):
    os.environ["SDL_VIDEODRIVER"] = "dummy"

try:
    import pygame
except ModuleNotFoundError as exc:  # pragma: no cover - runtime environment dependent
    raise SystemExit("pygame-ce is required for profiling") from exc

from tet4d.engine import api as engine_api
from tet4d.engine.api import GameConfigND


@dataclass(frozen=True)
class Scenario:
    name: str
    xw_deg: float
    zw_deg: float
    dense: bool


def _resolve_repo_local_path(raw: Path) -> Path:
    candidate = (raw if raw.is_absolute() else (_REPO_ROOT / raw)).resolve()
    root = _REPO_ROOT.resolve()
    if candidate == root or root in candidate.parents:
        return candidate
    raise SystemExit(f"output path must stay within project root: {root}")


def _fill_dense_board(state) -> None:
    dims = state.config.dims
    state.board.cells.clear()
    for x in range(dims[0]):
        for y in range(max(0, dims[1] // 2 - 1), dims[1]):
            for z in range(dims[2]):
                for w in range(dims[3]):
                    if (x + y + z + w) % 3 != 0:
                        continue
                    state.board.cells[(x, y, z, w)] = 1 + ((x + z + w) % 7)


def _run_scenario(
    *,
    scenario: Scenario,
    frames: int,
    warmup: int,
    surface: pygame.Surface,
    fonts,
    dims4: tuple[int, int, int, int],
) -> dict[str, float | int | str | bool]:
    cfg = GameConfigND(dims=dims4, gravity_axis=1, speed_level=1)
    state = engine_api.profile_4d_create_initial_state(cfg)
    if scenario.dense:
        _fill_dense_board(state)
    view = engine_api.profile_4d_new_layer_view_3d(
        xw_deg=scenario.xw_deg, zw_deg=scenario.zw_deg
    )

    for _ in range(warmup):
        engine_api.profile_4d_draw_game_frame(
            surface,
            state,
            view,
            fonts,
            grid_mode=engine_api.GridMode.FULL,
        )

    t0 = time.perf_counter()
    for _ in range(frames):
        engine_api.profile_4d_draw_game_frame(
            surface,
            state,
            view,
            fonts,
            grid_mode=engine_api.GridMode.FULL,
        )
    elapsed_s = time.perf_counter() - t0
    avg_ms = (elapsed_s / max(1, frames)) * 1000.0
    fps = 1000.0 / avg_ms if avg_ms > 0 else 0.0
    return {
        "name": scenario.name,
        "dense": scenario.dense,
        "xw_deg": scenario.xw_deg,
        "zw_deg": scenario.zw_deg,
        "frames": frames,
        "warmup": warmup,
        "total_ms": round(elapsed_s * 1000.0, 3),
        "avg_ms": round(avg_ms, 4),
        "fps": round(fps, 2),
    }


def _relative_overhead(base_ms: float, current_ms: float) -> tuple[float, float]:
    delta_ms = current_ms - base_ms
    if base_ms <= 0:
        return delta_ms, 0.0
    return delta_ms, (delta_ms / base_ms) * 100.0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Profile 4D renderer draw_game_frame overhead."
    )
    parser.add_argument(
        "--frames", type=int, default=120, help="Measured frames per scenario."
    )
    parser.add_argument(
        "--warmup", type=int, default=20, help="Warmup frames per scenario."
    )
    parser.add_argument("--width", type=int, default=1400, help="Render surface width.")
    parser.add_argument(
        "--height", type=int, default=900, help="Render surface height."
    )
    parser.add_argument(
        "--dims", type=str, default="6,12,6,4", help="4D dims as x,y,z,w."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("state/bench/4d_render_profile_latest.json"),
        help="JSON report output path (must be inside project root).",
    )
    parser.add_argument(
        "--assert-threshold",
        action="store_true",
        help="Exit non-zero if hyper sparse overhead exceeds thresholds.",
    )
    parser.add_argument("--overhead-pct-threshold", type=float, default=15.0)
    parser.add_argument("--overhead-ms-threshold", type=float, default=2.0)
    args = parser.parse_args()

    dims_parts = tuple(
        int(part.strip()) for part in args.dims.split(",") if part.strip()
    )
    if len(dims_parts) != 4 or any(value <= 0 for value in dims_parts):
        raise SystemExit("--dims must be four positive integers (x,y,z,w)")

    pygame.init()
    try:
        fonts = engine_api.profile_4d_init_fonts()
        surface = pygame.Surface((args.width, args.height), pygame.SRCALPHA)
        scenarios = (
            Scenario(name="default_sparse", xw_deg=0.0, zw_deg=0.0, dense=False),
            Scenario(name="hyper_sparse", xw_deg=90.0, zw_deg=90.0, dense=False),
            Scenario(name="default_dense", xw_deg=0.0, zw_deg=0.0, dense=True),
            Scenario(name="hyper_dense", xw_deg=90.0, zw_deg=90.0, dense=True),
        )
        results = [
            _run_scenario(
                scenario=scenario,
                frames=max(1, args.frames),
                warmup=max(0, args.warmup),
                surface=surface,
                fonts=fonts,
                dims4=dims_parts,
            )
            for scenario in scenarios
        ]
    finally:
        pygame.quit()

    by_name = {entry["name"]: entry for entry in results}
    sparse_delta_ms, sparse_delta_pct = _relative_overhead(
        float(by_name["default_sparse"]["avg_ms"]),
        float(by_name["hyper_sparse"]["avg_ms"]),
    )
    dense_delta_ms, dense_delta_pct = _relative_overhead(
        float(by_name["default_dense"]["avg_ms"]),
        float(by_name["hyper_dense"]["avg_ms"]),
    )

    threshold_exceeded = (
        sparse_delta_pct > args.overhead_pct_threshold
        or sparse_delta_ms > args.overhead_ms_threshold
    )

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "tool": "tools/benchmarks/profile_4d_render.py",
        "version": 1,
        "frames": max(1, args.frames),
        "warmup": max(0, args.warmup),
        "dims": dims_parts,
        "scenarios": results,
        "overhead": {
            "sparse": {
                "delta_ms": round(sparse_delta_ms, 4),
                "delta_pct": round(sparse_delta_pct, 2),
            },
            "dense": {
                "delta_ms": round(dense_delta_ms, 4),
                "delta_pct": round(dense_delta_pct, 2),
            },
        },
        "thresholds": {
            "sparse_pct_limit": args.overhead_pct_threshold,
            "sparse_ms_limit": args.overhead_ms_threshold,
            "sparse_threshold_exceeded": threshold_exceeded,
        },
    }

    output_path = _resolve_repo_local_path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"report written: {output_path}")

    if args.assert_threshold and threshold_exceeded:
        print("threshold assertion failed: sparse hyper-view overhead exceeded limits")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
