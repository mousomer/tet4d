#!/usr/bin/env python3
from __future__ import annotations

import argparse

from tetris_nd.game2d import GameConfig
from tetris_nd.game_nd import GameConfigND
from tetris_nd.pieces2d import PIECE_SET_2D_DEBUG
from tetris_nd.pieces_nd import PIECE_SET_3D_DEBUG, PIECE_SET_4D_DEBUG
from tetris_nd.playbot.dry_run import run_dry_run_2d, run_dry_run_nd


def _assert_report(ok: bool, details: str) -> None:
    if not ok:
        raise AssertionError(details)


def _check_once(seed: int) -> None:
    cfg_2d = GameConfig(width=6, height=14, piece_set=PIECE_SET_2D_DEBUG)
    report_2d = run_dry_run_2d(cfg_2d, max_pieces=30, seed=seed)
    _assert_report(
        report_2d.passed and report_2d.clears_observed > 0,
        f"2D dry-run failed (seed={seed}): {report_2d}",
    )

    cfg_3d = GameConfigND(dims=(6, 14, 4), gravity_axis=1, piece_set_id=PIECE_SET_3D_DEBUG)
    report_3d = run_dry_run_nd(cfg_3d, max_pieces=24, seed=seed)
    _assert_report(
        report_3d.passed and report_3d.clears_observed > 0,
        f"3D dry-run failed (seed={seed}): {report_3d}",
    )

    cfg_4d = GameConfigND(dims=(6, 14, 4, 3), gravity_axis=1, piece_set_id=PIECE_SET_4D_DEBUG)
    report_4d = run_dry_run_nd(cfg_4d, max_pieces=24, seed=seed)
    _assert_report(
        report_4d.passed and report_4d.clears_observed > 0,
        f"4D dry-run failed (seed={seed}): {report_4d}",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Repeated playbot dry-run stability checks.")
    parser.add_argument("--repeats", type=int, default=24, help="number of repeated dry-run checks")
    parser.add_argument("--seed-base", type=int, default=0, help="base seed for repeat sequence")
    args = parser.parse_args()

    repeats = max(1, int(args.repeats))
    seed_base = int(args.seed_base)
    for idx in range(repeats):
        _check_once(seed_base + idx)

    print(f"Playbot stability check passed ({repeats} runs).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
