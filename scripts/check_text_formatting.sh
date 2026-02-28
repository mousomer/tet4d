#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

python3 - <<'PY'
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path.cwd()
ALLOWLIST_PATH = REPO_ROOT / "config/project/format_allowlist.txt"
TEXT_EXTS = {".py", ".sh", ".yml", ".yaml", ".md", ".json"}
MINIFIED_SIZE_THRESHOLD = 400


def load_allowlist() -> set[str]:
    if not ALLOWLIST_PATH.exists():
        return set()
    entries: set[str] = set()
    for raw in ALLOWLIST_PATH.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        entries.add(line)
    return entries


def tracked_files() -> list[str]:
    out = subprocess.check_output(["git", "ls-files", "-z"], text=False)
    return [p.decode("utf-8", errors="surrogateescape") for p in out.split(b"\0") if p]


def main() -> int:
    allowlist = load_allowlist()
    missing_newline: list[str] = []
    minified_blob: list[str] = []

    for rel in tracked_files():
        if rel in allowlist:
            continue
        path = REPO_ROOT / rel
        if path.suffix.lower() not in TEXT_EXTS or not path.is_file():
            continue
        data = path.read_bytes()
        if not data:
            continue
        if b"\0" in data:
            continue
        if data[-1:] != b"\n":
            missing_newline.append(rel)
        line_count = data.count(b"\n")
        if line_count <= 1 and len(data) > MINIFIED_SIZE_THRESHOLD:
            minified_blob.append(f"{rel} (bytes={len(data)}, lines<={line_count})")

    if not missing_newline and not minified_blob:
        return 0

    if missing_newline:
        print("Formatting check failed: missing trailing newline in tracked text files:", file=sys.stderr)
        for rel in missing_newline:
            print(f"  - {rel}", file=sys.stderr)
    if minified_blob:
        print("Formatting check failed: suspicious single-line/minified tracked text files:", file=sys.stderr)
        for rel in minified_blob:
            print(f"  - {rel}", file=sys.stderr)
    return 2


raise SystemExit(main())
PY
