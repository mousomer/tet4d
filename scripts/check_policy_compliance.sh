#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

required_files=(
  "AGENTS.md"
  "config/project/policy_manifest.json"
  "scripts/verify.sh"
)

missing=0

for f in "${required_files[@]}"; do
  if [[ ! -f "$f" ]]; then
    echo "Missing required policy file: $f" >&2
    missing=1
  fi
done

if [[ "$missing" -ne 0 ]]; then
  exit 2
fi

# Delegate to the repo's canonical policy/security checks.
python3 tools/governance/validate_project_contracts.py
python3 tools/governance/scan_secrets.py

# Stage 5 guardrail (warn-only): detect legacy tetris_nd imports outside the shim path.
# This prevents silent backsliding while the repo is still migrating imports to tet4d.engine.
python3 - <<'PY'
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

repo_root = Path.cwd()
legacy_import_re = re.compile(r"^\s*(?:from|import)\s+tetris_nd\b")
exclude_prefixes = ("tetris_nd/",)

try:
    result = subprocess.run(
        ["git", "ls-files", "*.py"],
        check=True,
        capture_output=True,
        text=True,
    )
except Exception as exc:  # pragma: no cover - policy check should remain best-effort here
    print(f"WARNING: legacy import guardrail skipped (git ls-files failed: {exc})", file=sys.stderr)
    raise SystemExit(0)

hits: list[str] = []
for rel in result.stdout.splitlines():
    if not rel or rel.startswith(exclude_prefixes):
        continue
    path = repo_root / rel
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        continue
    for lineno, line in enumerate(text.splitlines(), start=1):
        if legacy_import_re.search(line):
            hits.append(f"{rel}:{lineno}: {line.strip()}")

if hits:
    print(
        "WARNING: legacy 'tetris_nd' imports detected outside the shim (warn-only in Stage 5).",
        file=sys.stderr,
    )
    print(
        "WARNING: Prefer 'tet4d.engine.*' for new/modified code. See docs/MIGRATION_NOTES.md.",
        file=sys.stderr,
    )
    sample_limit = 20
    for hit in hits[:sample_limit]:
        print(f"WARNING: {hit}", file=sys.stderr)
    if len(hits) > sample_limit:
        print(
            f"WARNING: ... {len(hits) - sample_limit} more legacy import occurrences not shown.",
            file=sys.stderr,
        )
PY
