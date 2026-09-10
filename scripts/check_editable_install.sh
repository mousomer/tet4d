#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON_BIN="$(./scripts/resolve_python_env.sh)"

"$PYTHON_BIN" -c "from pathlib import Path; import tet4d; repo = Path.cwd().resolve(); pkg_root = Path(tet4d.__file__).resolve().parent; expected = repo / 'src' / 'tet4d'; raise SystemExit(0 if pkg_root == expected else f'Expected editable install from {expected}, got {pkg_root}')"
