from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if __package__:
    from ._common import load_unified_code_rules
else:
    import sys

    sys.path.append(str(Path(__file__).resolve().parent))
    from _common import load_unified_code_rules


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class LocBucket:
    added: int = 0
    deleted: int = 0

    @property
    def net(self) -> int:
        return self.added - self.deleted


def _load_config() -> dict[str, Any]:
    unified = load_unified_code_rules(ROOT)
    if isinstance(unified, dict):
        loc_guidance = unified.get("loc_guidance")
        if isinstance(loc_guidance, dict):
            return loc_guidance
    raise SystemExit("missing required file: config/project/policy/code_rules.json")


def _git_numstat() -> list[tuple[int, int, str]]:
    result = subprocess.run(
        ["git", "diff", "--numstat"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit("failed to read git diff --numstat")
    rows: list[tuple[int, int, str]] = []
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        add_raw, del_raw, path = parts
        if add_raw == "-" or del_raw == "-":
            continue
        rows.append((int(add_raw), int(del_raw), path))
    return rows


def _match_bucket(path: str, bucket_patterns: dict[str, str]) -> str | None:
    for name, pattern in bucket_patterns.items():
        for token in pattern.split("|"):
            if token and token in path:
                return name
    return None


def _collect_buckets(
    rows: list[tuple[int, int, str]],
    *,
    include_exts: set[str],
    bucket_patterns: dict[str, str],
) -> dict[str, LocBucket]:
    totals: dict[str, LocBucket] = {name: LocBucket() for name in bucket_patterns}
    for added, deleted, path in rows:
        if Path(path).suffix not in include_exts:
            continue
        bucket = _match_bucket(path, bucket_patterns)
        if bucket is None:
            continue
        current = totals[bucket]
        totals[bucket] = LocBucket(
            added=current.added + added,
            deleted=current.deleted + deleted,
        )
    return totals


def main() -> int:
    cfg = _load_config()
    include_exts = set(cfg.get("include_extensions", [".py"]))
    bucket_patterns = cfg.get("buckets", {})
    thresholds = cfg.get("thresholds", {})
    if not isinstance(bucket_patterns, dict) or not isinstance(thresholds, dict):
        print("LOC guidance check failed:")
        print("- [schema] buckets and thresholds must be objects")
        return 1

    batch_env = str(cfg.get("batch_type_env_var", "LOC_GUIDANCE_BATCH_TYPE"))
    default_batch = str(cfg.get("default_batch_type", "mixed"))
    batch_type = os.getenv(batch_env, default_batch).strip().lower() or default_batch
    batch_threshold = thresholds.get(batch_type)
    if not isinstance(batch_threshold, dict):
        print("LOC guidance check failed:")
        print(f"- [schema] unknown batch type: {batch_type}")
        return 1

    totals = _collect_buckets(
        _git_numstat(),
        include_exts=include_exts,
        bucket_patterns={str(k): str(v) for k, v in bucket_patterns.items()},
    )

    warnings: list[str] = []
    for bucket, stat in totals.items():
        threshold = int(batch_threshold.get(bucket, 0))
        if stat.net > threshold:
            warnings.append(
                f"{bucket} net LOC delta {stat.net:+d} exceeds soft threshold +{threshold}"
            )

    print(f"LOC guidance check ({batch_type})")
    for bucket, stat in totals.items():
        print(f"- {bucket}: +{stat.added} / -{stat.deleted} => {stat.net:+d}")
    if warnings:
        print("LOC guidance warnings (non-blocking):")
        for item in warnings:
            print(f"- {item}")
        return 0
    print("LOC guidance: within soft thresholds.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
