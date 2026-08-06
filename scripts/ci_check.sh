#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

# Temporary diagnostic: expose the exact generated restart handoff.
# This commit exists only to trigger the ready diagnostic PR.
python - <<'PY'
from pathlib import Path

import tools.governance.generate_maintenance_docs as maintenance

actual = Path("CURRENT_STATE.md").read_text(encoding="utf-8")
expected = maintenance.render_current_state_doc()
if actual != expected:
    print("BEGIN_EXPECTED_CURRENT_STATE")
    print(expected, end="")
    print("END_EXPECTED_CURRENT_STATE")
PY

# CI/local CI wrapper delegates to the canonical verification pipeline.
QUIET="${QUIET:-1}"
CODEX_MODE="${CODEX_MODE:-0}"

export QUIET
export CODEX_MODE

exec ./scripts/verify.sh
