#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ -n "${PYTHON_BIN:-}" ]]; then
  :
elif [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "No Python runtime found. Set PYTHON_BIN or install python3." >&2
  exit 1
fi

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

if ! "$PYTHON_BIN" -c "import tet4d" >/dev/null 2>&1; then
  echo "Missing repo package 'tet4d' in ${PYTHON_BIN}." >&2
  echo "Run: ${PYTHON_BIN} -m pip install -e '.[dev]'" >&2
  exit 1
fi

# Fast architecture policy guardrail (pass-quiet / fail-loud).
scripts/check_engine_core_purity.sh
scripts/check_architecture_boundaries.sh

# Delegate to the repo's canonical policy/security checks.
# Canonical command tokens retained for contract validation:
# python3 tools/governance/validate_project_contracts.py
# python3 tools/governance/scan_secrets.py
"$PYTHON_BIN" tools/governance/validate_project_contracts.py
"$PYTHON_BIN" tools/governance/scan_secrets.py

# Stage 6 guardrail (enforced): block legacy tetris_nd imports outside the removed shim path.
"$PYTHON_BIN" - <<'PY'
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
except Exception as exc:  # pragma: no cover - policy check should remain deterministic in CI
    print(f"ERROR: legacy import guardrail failed (git ls-files failed: {exc})", file=sys.stderr)
    raise SystemExit(1)

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
        "ERROR: legacy 'tetris_nd' imports detected. The compatibility shim was removed in Stage 6.",
        file=sys.stderr,
    )
    print(
        "ERROR: Use 'tet4d.engine.*' imports instead. See docs/MIGRATION_NOTES.md.",
        file=sys.stderr,
    )
    sample_limit = 20
    for hit in hits[:sample_limit]:
        print(f"ERROR: {hit}", file=sys.stderr)
    if len(hits) > sample_limit:
        print(
            f"ERROR: ... {len(hits) - sample_limit} more legacy import occurrences not shown.",
            file=sys.stderr,
        )
    raise SystemExit(1)
PY
