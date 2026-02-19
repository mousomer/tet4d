#!/usr/bin/env python3
# ruff: noqa: E402
from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tetris_nd.board import BoardND
from tetris_nd.game2d import GameConfig, GameState
from tetris_nd.game_nd import GameConfigND, GameStateND
from tetris_nd.pieces2d import PIECE_SET_2D_CLASSIC
from tetris_nd.pieces_nd import PIECE_SET_3D_STANDARD, PIECE_SET_4D_STANDARD
from tetris_nd.playbot.planner_2d import plan_best_2d_move
from tetris_nd.playbot.planner_nd import plan_best_nd_move
from tetris_nd.playbot.types import (
    BotPlannerAlgorithm,
    BotPlannerProfile,
    benchmark_history_file,
    benchmark_p95_thresholds,
    default_planning_budget_ms,
)

DIMS_2D = (10, 20)
DIMS_3D = (6, 18, 6)
DIMS_4D = (6, 18, 6, 4)


def _resolve_repo_local_path(raw: Path) -> Path:
    candidate = (raw if raw.is_absolute() else (ROOT / raw)).resolve()
    root = ROOT.resolve()
    if candidate == root or root in candidate.parents:
        return candidate
    raise SystemExit(f"output path must stay within project root: {root}")


@dataclass(frozen=True)
class BenchSample:
    ms: float
    candidates: int


def _bench_2d(
    profile: BotPlannerProfile,
    budget_ms: int,
    runs: int,
    *,
    algorithm: BotPlannerAlgorithm,
) -> list[BenchSample]:
    samples: list[BenchSample] = []
    for i in range(runs):
        cfg = GameConfig(
            width=DIMS_2D[0],
            height=DIMS_2D[1],
            piece_set=PIECE_SET_2D_CLASSIC,
            speed_level=3,
        )
        state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)), rng=random.Random(100 + i))
        t0 = time.perf_counter()
        plan = plan_best_2d_move(state, profile=profile, budget_ms=budget_ms, algorithm=algorithm)
        elapsed = (time.perf_counter() - t0) * 1000.0
        if plan is None:
            continue
        samples.append(BenchSample(ms=elapsed, candidates=plan.stats.candidate_count))
    return samples


def _bench_nd(
    profile: BotPlannerProfile,
    budget_ms: int,
    runs: int,
    *,
    ndim: int,
    algorithm: BotPlannerAlgorithm,
) -> list[BenchSample]:
    if ndim == 3:
        cfg = GameConfigND(
            dims=DIMS_3D,
            gravity_axis=1,
            piece_set_id=PIECE_SET_3D_STANDARD,
            speed_level=3,
        )
    else:
        cfg = GameConfigND(
            dims=DIMS_4D,
            gravity_axis=1,
            piece_set_id=PIECE_SET_4D_STANDARD,
            speed_level=3,
        )

    samples: list[BenchSample] = []
    for i in range(runs):
        state = GameStateND(config=cfg, board=BoardND(cfg.dims), rng=random.Random(200 + i))
        t0 = time.perf_counter()
        plan = plan_best_nd_move(state, profile=profile, budget_ms=budget_ms, algorithm=algorithm)
        elapsed = (time.perf_counter() - t0) * 1000.0
        if plan is None:
            continue
        samples.append(BenchSample(ms=elapsed, candidates=plan.stats.candidate_count))
    return samples


def _summary(samples: list[BenchSample]) -> dict[str, float | int]:
    if not samples:
        return {"runs": 0, "p50_ms": 0.0, "p95_ms": 0.0, "max_ms": 0.0, "avg_candidates": 0}
    ms_values = [sample.ms for sample in samples]
    p50 = statistics.median(ms_values)
    p95 = statistics.quantiles(ms_values, n=20)[18] if len(ms_values) >= 20 else max(ms_values)
    return {
        "runs": len(samples),
        "p50_ms": round(p50, 3),
        "p95_ms": round(p95, 3),
        "max_ms": round(max(ms_values), 3),
        "avg_candidates": int(round(statistics.mean(sample.candidates for sample in samples))),
    }


def _assert_thresholds(results: dict[str, dict[str, float | int]]) -> tuple[bool, str]:
    thresholds = benchmark_p95_thresholds()
    for key, max_p95 in thresholds.items():
        p95 = float(results[key]["p95_ms"])
        if p95 > max_p95:
            return False, f"{key} planner p95 {p95:.2f} ms exceeds {max_p95:.2f} ms"
    return True, "benchmark thresholds passed"


def _append_trend_sample(
    *,
    output_path: Path,
    algorithm: BotPlannerAlgorithm,
    profile: BotPlannerProfile,
    runs: int,
    budgets: dict[str, int],
    results: dict[str, dict[str, float | int]],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "algorithm": algorithm.value,
        "profile": profile.value,
        "runs": int(runs),
        "budgets_ms": budgets,
        "results": results,
    }
    with output_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark playbot planner latency.")
    parser.add_argument("--runs", type=int, default=40, help="number of plans per dimension")
    parser.add_argument(
        "--profile",
        choices=[p.value for p in BotPlannerProfile],
        default=BotPlannerProfile.BALANCED.value,
        help="planner profile",
    )
    parser.add_argument(
        "--algorithm",
        choices=[p.value for p in BotPlannerAlgorithm],
        default=BotPlannerAlgorithm.AUTO.value,
        help="planner algorithm",
    )
    parser.add_argument("--budget-2d", type=int, default=0, help="override 2D planning budget in ms")
    parser.add_argument("--budget-3d", type=int, default=0, help="override 3D planning budget in ms")
    parser.add_argument("--budget-4d", type=int, default=0, help="override 4D planning budget in ms")
    parser.add_argument("--assert", action="store_true", dest="assert_mode", help="fail on threshold regressions")
    parser.add_argument(
        "--record-trend",
        action="store_true",
        help="append benchmark results to trend history JSONL",
    )
    parser.add_argument(
        "--trend-file",
        default="",
        help="override trend history file path (must be inside project root)",
    )
    args = parser.parse_args()

    profile = BotPlannerProfile(args.profile)
    algorithm = BotPlannerAlgorithm(args.algorithm)

    budget_2d = args.budget_2d or default_planning_budget_ms(2, profile, dims=DIMS_2D)
    budget_3d = args.budget_3d or default_planning_budget_ms(3, profile, dims=DIMS_3D)
    budget_4d = args.budget_4d or default_planning_budget_ms(4, profile, dims=DIMS_4D)

    results = {
        "2d": _summary(_bench_2d(profile, budget_2d, args.runs, algorithm=algorithm)),
        "3d": _summary(_bench_nd(profile, budget_3d, args.runs, ndim=3, algorithm=algorithm)),
        "4d": _summary(_bench_nd(profile, budget_4d, args.runs, ndim=4, algorithm=algorithm)),
    }
    payload = {
        "algorithm": algorithm.value,
        "profile": profile.value,
        "budgets_ms": {
            "2d": budget_2d,
            "3d": budget_3d,
            "4d": budget_4d,
        },
        "results": results,
        "thresholds_ms": benchmark_p95_thresholds(),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))

    if args.record_trend:
        trend_raw = Path(args.trend_file) if args.trend_file else Path(benchmark_history_file())
        trend_path = _resolve_repo_local_path(trend_raw)
        _append_trend_sample(
            output_path=trend_path,
            algorithm=algorithm,
            profile=profile,
            runs=args.runs,
            budgets=payload["budgets_ms"],
            results=results,
        )
        print(f"trend sample appended: {trend_path}")

    if args.assert_mode:
        ok, msg = _assert_thresholds(results)
        if not ok:
            print(msg)
            return 1
        print(msg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
