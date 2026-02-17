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
    default_planning_budget_ms,
)


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
            width=10,
            height=20,
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
            dims=(6, 18, 6),
            gravity_axis=1,
            piece_set_id=PIECE_SET_3D_STANDARD,
            speed_level=3,
        )
    else:
        cfg = GameConfigND(
            dims=(6, 18, 6, 4),
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
    # Budget-based fallback means p95 should stay close to budget on normal hardware.
    thresholds = {
        "2d": 20.0,
        "3d": 45.0,
        "4d": 70.0,
    }
    for key, max_p95 in thresholds.items():
        p95 = float(results[key]["p95_ms"])
        if p95 > max_p95:
            return False, f"{key} planner p95 {p95:.2f} ms exceeds {max_p95:.2f} ms"
    return True, "benchmark thresholds passed"


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
    args = parser.parse_args()

    profile = BotPlannerProfile(args.profile)
    algorithm = BotPlannerAlgorithm(args.algorithm)
    budget_2d = args.budget_2d or default_planning_budget_ms(2, profile)
    budget_3d = args.budget_3d or default_planning_budget_ms(3, profile)
    budget_4d = args.budget_4d or default_planning_budget_ms(4, profile)

    results = {
        "2d": _summary(_bench_2d(profile, budget_2d, args.runs, algorithm=algorithm)),
        "3d": _summary(_bench_nd(profile, budget_3d, args.runs, ndim=3, algorithm=algorithm)),
        "4d": _summary(_bench_nd(profile, budget_4d, args.runs, ndim=4, algorithm=algorithm)),
    }
    print(
        json.dumps(
            {"algorithm": algorithm.value, "profile": profile.value, "results": results},
            indent=2,
            sort_keys=True,
        )
    )

    if args.assert_mode:
        ok, msg = _assert_thresholds(results)
        if not ok:
            print(msg)
            return 1
        print(msg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
