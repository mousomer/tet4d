#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

VENV_PATH=".venv"
VENV_PYTHON="${VENV_PATH}/bin/python"
FINGERPRINT_PATH="${VENV_PATH}/.tet4d-bootstrap-fingerprint"
LOG_DIR="state/local_verify"
LOG_PATH="${LOG_DIR}/bootstrap.log"
BOOTSTRAP_ONLY=0
REBUILD_VENV=0

usage() {
  echo "Usage: ./scripts/verify_local.sh [--bootstrap-only] [--rebuild-venv]" >&2
}

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --bootstrap-only) BOOTSTRAP_ONLY=1 ;;
    --rebuild-venv) REBUILD_VENV=1 ;;
    -h|--help) usage; exit 0 ;;
    *) usage; exit 2 ;;
  esac
  shift
done

if [[ -n "${BOOTSTRAP_PYTHON:-}" ]]; then
  BOOTSTRAP_BIN="${BOOTSTRAP_PYTHON}"
else
  BOOTSTRAP_BIN="$(./scripts/resolve_bootstrap_python.sh)"
fi

absolute_logical_path() {
  local candidate="$1"
  local directory
  local filename
  directory="$(dirname "$candidate")"
  filename="$(basename "$candidate")"
  (
    cd -L "$directory"
    printf '%s/%s\n' "$PWD" "$filename"
  )
}

if [[ "$REBUILD_VENV" == "1" ]]; then
  venv_absolute="$(absolute_logical_path "$VENV_PATH")"
  bootstrap_absolute="$(absolute_logical_path "$BOOTSTRAP_BIN")"
  if [[ "$bootstrap_absolute" == "$venv_absolute"/* ]]; then
    echo "local verify: refusing --rebuild-venv because bootstrap Python is inside the .venv slated for deletion: ${BOOTSTRAP_BIN}" >&2
    echo "local verify: select an approved external bootstrap explicitly, for example BOOTSTRAP_PYTHON=/absolute/path/to/python ./scripts/verify_local.sh --rebuild-venv" >&2
    exit 2
  fi
fi

if ! "$BOOTSTRAP_BIN" -c 'import sys' >/dev/null 2>&1; then
  echo "local verify: bootstrap Python is unavailable: ${BOOTSTRAP_BIN}" >&2
  exit 1
fi

# Diagnose an unsupported bootstrap before any environment creation or replacement.
"$BOOTSTRAP_BIN" -c 'from tools.workspace_governance.cli.bootstrap import main; raise SystemExit(main(check_only=True))'

mkdir -p "$LOG_DIR"

bootstrap_fingerprint() {
  local metadata=(pyproject.toml setup.py setup.cfg poetry.lock Pipfile.lock uv.lock requirements.txt requirements-dev.txt requirements-dev.lock)
  local present=()
  local metadata_path
  for metadata_path in "${metadata[@]}"; do
    [[ -f "$metadata_path" ]] && present+=("$metadata_path")
  done
  "$BOOTSTRAP_BIN" - "${present[@]}" <<'PY'
import hashlib
import pathlib
import sys

digest = hashlib.sha256()
digest.update(f"python={sys.version_info.major}.{sys.version_info.minor}\n".encode())
for raw_path in sys.argv[1:]:
    path = pathlib.Path(raw_path)
    digest.update(f"path={path.as_posix()}\n".encode())
    digest.update(path.read_bytes())
    digest.update(b"\n")
print(digest.hexdigest())
PY
}

run_bootstrap_phase() {
  local phase="$1"
  shift
  if ! "$@" >>"$LOG_PATH" 2>&1; then
    echo "local verify: ${phase} failed" >&2
    echo "local verify: log: ${LOG_PATH}" >&2
    tail -n 40 "$LOG_PATH" >&2 || true
    exit 1
  fi
}

recreate_venv() {
  rm -rf "$VENV_PATH"
  echo "local verify: creating .venv"
  : >"$LOG_PATH"
  run_bootstrap_phase "venv creation" "$BOOTSTRAP_BIN" -m venv "$VENV_PATH"
  echo "local verify: installing dev environment"
  run_bootstrap_phase "dependency installation" "$VENV_PYTHON" -m pip install --disable-pip-version-check --no-input --quiet -e '.[dev]'
}

requested_version="$($BOOTSTRAP_BIN -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
if [[ "$REBUILD_VENV" == "1" ]]; then
  recreate_venv
elif [[ ! -x "$VENV_PYTHON" ]]; then
  recreate_venv
else
  existing_version="$($VENV_PYTHON -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
  if [[ "$existing_version" != "$requested_version" ]]; then
    echo "local verify: recreating .venv for Python ${requested_version}"
    recreate_venv
  fi
fi

fingerprint="$(bootstrap_fingerprint)"
if [[ ! -f "$FINGERPRINT_PATH" || "$(<"$FINGERPRINT_PATH")" != "$fingerprint" ]]; then
  echo "local verify: installing dev environment"
  : >"$LOG_PATH"
  run_bootstrap_phase "dependency installation" "$VENV_PYTHON" -m pip install --disable-pip-version-check --no-input --quiet -e '.[dev]'
  printf '%s\n' "$fingerprint" >"$FINGERPRINT_PATH"
elif ! TET4D_PYTHON="$VENV_PYTHON" ./scripts/check_editable_install.sh >/dev/null 2>&1; then
  echo "local verify: repairing editable installation"
  : >"$LOG_PATH"
  run_bootstrap_phase "editable installation repair" "$VENV_PYTHON" -m pip install --disable-pip-version-check --no-input --quiet -e '.[dev]'
  printf '%s\n' "$fingerprint" >"$FINGERPRINT_PATH"
else
  echo "local verify: venv cached"
fi

if ! TET4D_PYTHON="$VENV_PYTHON" ./scripts/check_editable_install.sh; then
  echo "local verify: editable installation does not belong to this worktree" >&2
  exit 1
fi

if [[ "$BOOTSTRAP_ONLY" == "1" ]]; then
  exit 0
fi

echo "local verify: running repository gate"
exec env TET4D_PYTHON="$VENV_PYTHON" CODEX_MODE="${CODEX_MODE:-1}" QUIET="${QUIET:-1}" ./scripts/verify.sh
