from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from tools.governance.policy_pack_io import load_policy_pack

from .baseline import (
    BASELINE_PATH,
    ROOT,
    BaselineMismatchError,
    require_frozen_baseline,
)
from .codex_rollout import RejectedTrajectory, adapt_rollout, discover_rollouts
from .measurement import (
    TrajectoryValidationError,
    measure_trajectory,
    normalize_trajectory,
)
from .postmortem import (
    PostmortemValidationError,
    bind_overlay_records,
    build_postmortem_aggregate,
    postmortem_from_trajectory,
    read_json_records,
    render_task_summary,
)
from .reporting import write_outputs


def _write_json(path: Path | None, payload: object) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if path is None:
        sys.stdout.write(text)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _baseline(args: argparse.Namespace) -> tuple[dict[str, Any] | None, int]:
    try:
        fingerprint = require_frozen_baseline(args.root, args.baseline)
    except BaselineMismatchError as exc:
        payload = dict(exc.fingerprint)
        payload["baseline_validation"] = {
            "status": "mismatch",
            "mismatches": exc.mismatches,
        }
        _write_json(getattr(args, "output", None), payload)
        return None, 2
    fingerprint["baseline_validation"] = {"status": "match", "mismatches": []}
    return fingerprint, 0


def _fingerprint_command(args: argparse.Namespace) -> int:
    fingerprint, status = _baseline(args)
    if fingerprint is not None:
        _write_json(args.output, fingerprint)
    return status


def _measure_command(args: argparse.Namespace) -> int:
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        record = normalize_trajectory(payload)
    except (OSError, json.JSONDecodeError, TrajectoryValidationError) as exc:
        sys.stderr.write(f"trajectory rejected: {exc}\n")
        return 2
    _write_json(
        args.output, {"trajectory": record, "metrics": measure_trajectory(record)}
    )
    return 0


def _trajectory_id(trajectory: dict[str, Any]) -> str | None:
    source = trajectory.get("source")
    source_id = source.get("source_id") if isinstance(source, dict) else None
    return source_id if isinstance(source_id, str) else None


def _postmortem_command(args: argparse.Namespace) -> int:
    try:
        trajectories = [
            trajectory
            for path in args.trajectory
            for trajectory in read_json_records(path)
        ]
        known = {_trajectory_id(trajectory) for trajectory in trajectories} - {None}
        overlays = {
            payload_key: bind_overlay_records(
                [record for path in paths or [] for record in read_json_records(path)],
                payload_key,
                known,
            )
            for payload_key, paths in (
                ("evaluation", args.evaluator),
                ("work_segment", args.segment),
                ("resolver_evidence", args.resolver_evidence),
            )
        }
        postmortems = []
        for trajectory in trajectories:
            trajectory_id = _trajectory_id(trajectory)
            postmortems.append(
                postmortem_from_trajectory(
                    trajectory,
                    evaluator=overlays["evaluation"].get(trajectory_id),
                    segment=overlays["work_segment"].get(trajectory_id),
                    resolver_evidence=overlays["resolver_evidence"].get(trajectory_id),
                )
            )
        aggregate = build_postmortem_aggregate(postmortems)
    except (
        OSError,
        json.JSONDecodeError,
        PostmortemValidationError,
        TrajectoryValidationError,
    ) as exc:
        _write_json(args.output, {"status": "invalid", "error": str(exc)})
        return 2
    payload = {
        "postmortems": postmortems,
        "aggregate": aggregate,
        "summaries": [render_task_summary(record) for record in postmortems],
    }
    _write_json(args.output, payload)
    return 0


def _corpus_command(args: argparse.Namespace) -> int:
    fingerprint, status = _baseline(args)
    if fingerprint is None:
        sys.stderr.write(
            "historical corpus measurement blocked by frozen-baseline mismatch\n"
        )
        return status
    policy = load_policy_pack(args.root / "config/project/policy_pack.json")
    records = []
    dispositions = []
    for path in discover_rollouts(args.source_root):
        adapted = adapt_rollout(path, args.root, policy)
        if isinstance(adapted, RejectedTrajectory):
            dispositions.append({"status": adapted.status, "reason": adapted.reason})
        else:
            records.append(adapted)
    aggregate = write_outputs(args.output_dir, fingerprint, records, dispositions)
    sys.stdout.write(json.dumps(aggregate, indent=2, sort_keys=True) + "\n")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Stage C1 governance-materialization instrumentation"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    fingerprint = subparsers.add_parser("fingerprint")
    fingerprint.add_argument("--root", type=Path, default=ROOT)
    fingerprint.add_argument("--baseline", type=Path, default=BASELINE_PATH)
    fingerprint.add_argument("--output", type=Path)
    fingerprint.set_defaults(handler=_fingerprint_command)

    measure = subparsers.add_parser("measure")
    measure.add_argument("--input", type=Path, required=True)
    measure.add_argument("--output", type=Path)
    measure.set_defaults(handler=_measure_command)

    corpus = subparsers.add_parser("corpus")
    corpus.add_argument("--root", type=Path, default=ROOT)
    corpus.add_argument("--baseline", type=Path, default=BASELINE_PATH)
    corpus.add_argument("--source-root", type=Path, action="append", required=True)
    corpus.add_argument("--output-dir", type=Path, required=True)
    corpus.set_defaults(handler=_corpus_command)

    postmortem = subparsers.add_parser(
        "postmortem",
        help="derive evidence-preserving task post-mortems from normalized trajectories",
    )
    postmortem.add_argument(
        "--trajectory",
        type=Path,
        action="append",
        required=True,
        help="normalized trajectory JSON or JSONL; repeat for multiple tasks",
    )
    postmortem.add_argument(
        "--evaluator",
        type=Path,
        action="append",
        help="optional {source_trajectory_id, evaluation} records",
    )
    postmortem.add_argument(
        "--segment",
        type=Path,
        action="append",
        help="optional {source_trajectory_id, work_segment} G1 records",
    )
    postmortem.add_argument(
        "--resolver-evidence",
        type=Path,
        action="append",
        help="optional {source_trajectory_id, resolver_evidence} captured gov output",
    )
    postmortem.add_argument("--output", type=Path)
    postmortem.set_defaults(handler=_postmortem_command)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
