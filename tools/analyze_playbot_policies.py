#!/usr/bin/env python3
# ruff: noqa: E402
from __future__ import annotations

import argparse
import csv
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
    benchmark_p95_thresholds,
    default_planning_budget_ms,
)


@dataclass(frozen=True)
class BoardCase:
    name: str
    ndim: int
    dims: tuple[int, ...]


_BASE_CASES = (
    BoardCase(name="2d_base", ndim=2, dims=(10, 20)),
    BoardCase(name="3d_base", ndim=3, dims=(6, 18, 6)),
    BoardCase(name="4d_base", ndim=4, dims=(6, 18, 6, 4)),
)

_STRESS_CASES = (
    BoardCase(name="2d_stress", ndim=2, dims=(12, 24)),
    BoardCase(name="3d_stress", ndim=3, dims=(8, 20, 8)),
    BoardCase(name="4d_stress", ndim=4, dims=(8, 20, 8, 5)),
)


def _parse_csv_values(raw: str, *, allowed: set[str], label: str) -> list[str]:
    parts = [item.strip().lower() for item in raw.split(",") if item.strip()]
    if not parts:
        raise SystemExit(f"{label} list must not be empty")
    unknown = [item for item in parts if item not in allowed]
    if unknown:
        allowed_text = ", ".join(sorted(allowed))
        raise SystemExit(f"unsupported {label}: {', '.join(unknown)} (allowed: {allowed_text})")
    return parts


def _board_cases(set_name: str) -> tuple[BoardCase, ...]:
    if set_name == "base":
        return _BASE_CASES
    if set_name == "stress":
        return _STRESS_CASES
    return _BASE_CASES + _STRESS_CASES


def _planner_sample_ms(
    *,
    case: BoardCase,
    algorithm: BotPlannerAlgorithm,
    profile: BotPlannerProfile,
    budget_ms: int,
    seed: int,
) -> tuple[float, int] | None:
    if case.ndim == 2:
        cfg2 = GameConfig(
            width=case.dims[0],
            height=case.dims[1],
            piece_set=PIECE_SET_2D_CLASSIC,
            speed_level=3,
        )
        state2 = GameState(config=cfg2, board=BoardND(case.dims), rng=random.Random(seed))
        t0 = time.perf_counter()
        plan = plan_best_2d_move(state2, profile=profile, budget_ms=budget_ms, algorithm=algorithm)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        if plan is None:
            return None
        return elapsed_ms, int(plan.stats.candidate_count)

    if case.ndim == 3:
        cfg_nd = GameConfigND(
            dims=case.dims,
            gravity_axis=1,
            piece_set_id=PIECE_SET_3D_STANDARD,
            speed_level=3,
        )
    else:
        cfg_nd = GameConfigND(
            dims=case.dims,
            gravity_axis=1,
            piece_set_id=PIECE_SET_4D_STANDARD,
            speed_level=3,
        )

    state_nd = GameStateND(config=cfg_nd, board=BoardND(case.dims), rng=random.Random(seed))
    t0 = time.perf_counter()
    plan_nd = plan_best_nd_move(state_nd, profile=profile, budget_ms=budget_ms, algorithm=algorithm)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    if plan_nd is None:
        return None
    return elapsed_ms, int(plan_nd.stats.candidate_count)


def _dimension_threshold_ms(ndim: int) -> float:
    thresholds = benchmark_p95_thresholds()
    if ndim <= 2:
        return float(thresholds["2d"])
    if ndim == 3:
        return float(thresholds["3d"])
    return float(thresholds["4d"])


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    if len(values) < 20:
        return max(values)
    return statistics.quantiles(values, n=20)[18]


def _summarize_case(
    *,
    case: BoardCase,
    algorithm: BotPlannerAlgorithm,
    profile: BotPlannerProfile,
    budget_ms: int,
    runs: int,
    seed_start: int,
) -> dict[str, object]:
    elapsed_samples: list[float] = []
    candidate_samples: list[int] = []
    for i in range(runs):
        sample = _planner_sample_ms(
            case=case,
            algorithm=algorithm,
            profile=profile,
            budget_ms=budget_ms,
            seed=seed_start + i,
        )
        if sample is None:
            continue
        elapsed_ms, candidates = sample
        elapsed_samples.append(elapsed_ms)
        candidate_samples.append(candidates)

    p50_ms = statistics.median(elapsed_samples) if elapsed_samples else 0.0
    p95_ms = _p95(elapsed_samples)
    threshold_ms = _dimension_threshold_ms(case.ndim)
    ratio = (p95_ms / threshold_ms) if threshold_ms > 0 else 0.0
    avg_candidates = statistics.mean(candidate_samples) if candidate_samples else 0.0
    return {
        "case": case.name,
        "ndim": case.ndim,
        "dims": list(case.dims),
        "algorithm": algorithm.value,
        "profile": profile.value,
        "budget_ms": budget_ms,
        "runs": len(elapsed_samples),
        "p50_ms": round(p50_ms, 3),
        "p95_ms": round(p95_ms, 3),
        "max_ms": round(max(elapsed_samples), 3) if elapsed_samples else 0.0,
        "avg_candidates": int(round(avg_candidates)),
        "threshold_ms": round(threshold_ms, 3),
        "threshold_ratio": round(ratio, 4),
    }


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Offline comparison of playbot planner policies across dimensions, boards, and seeds.",
    )
    parser.add_argument("--board-set", choices=("base", "stress", "all"), default="all")
    parser.add_argument("--runs", type=int, default=24, help="plans per case/policy")
    parser.add_argument("--seed-start", type=int, default=100, help="first RNG seed")
    parser.add_argument("--budget-scale", type=float, default=1.0, help="multiplier on default budgets")
    parser.add_argument(
        "--profiles",
        default="fast,balanced,deep,ultra",
        help="comma-separated planner profiles",
    )
    parser.add_argument(
        "--algorithms",
        default="auto,heuristic,greedy_layer",
        help="comma-separated planner algorithms",
    )
    parser.add_argument("--output-json", default="", help="optional JSON output file")
    parser.add_argument("--output-csv", default="", help="optional CSV output file")
    parser.add_argument("--show-top", type=int, default=18, help="rows to show in terminal summary")
    args = parser.parse_args()

    profiles = _parse_csv_values(
        args.profiles,
        allowed={profile.value for profile in BotPlannerProfile},
        label="profiles",
    )
    algorithms = _parse_csv_values(
        args.algorithms,
        allowed={algorithm.value for algorithm in BotPlannerAlgorithm},
        label="algorithms",
    )
    cases = _board_cases(args.board_set)

    rows: list[dict[str, object]] = []
    for case in cases:
        for algorithm_name in algorithms:
            algorithm = BotPlannerAlgorithm(algorithm_name)
            for profile_name in profiles:
                profile = BotPlannerProfile(profile_name)
                base_budget = default_planning_budget_ms(case.ndim, profile, dims=case.dims)
                budget_ms = max(1, int(round(base_budget * args.budget_scale)))
                rows.append(
                    _summarize_case(
                        case=case,
                        algorithm=algorithm,
                        profile=profile,
                        budget_ms=budget_ms,
                        runs=args.runs,
                        seed_start=args.seed_start,
                    )
                )

    rows.sort(key=lambda item: (float(item["threshold_ratio"]), float(item["p95_ms"])))
    top_n = max(1, args.show_top)
    payload = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "board_set": args.board_set,
        "runs": int(args.runs),
        "seed_start": int(args.seed_start),
        "budget_scale": float(args.budget_scale),
        "rows": rows,
    }

    print(json.dumps({"summary_top": rows[:top_n], "count": len(rows)}, indent=2))

    if args.output_json:
        json_path = Path(args.output_json)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"wrote JSON: {json_path}")
    if args.output_csv:
        csv_path = Path(args.output_csv)
        _write_csv(csv_path, rows)
        print(f"wrote CSV: {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
