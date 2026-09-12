#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

# The one owner of Python environment mutation. Verification never installs, so
# if several scripts could reach for pip the environment would have no single
# authority and a gate could silently change what it then verifies.
#
# Which environment is built follows the declared execution mode rather than a
# second switch: installed mode means an environment belonging to this checkout,
# so the project is installed editable into it; source mode means a shared
# toolchain that must own no source binding, so only declared dependencies are
# installed and the checkout supplies its own source.

PYTHON_BOOTSTRAP_BIN="${PYTHON_BOOTSTRAP_BIN:-$(./scripts/resolve_bootstrap_python.sh)}"
PIP_ARGS=(--disable-pip-version-check --no-input)

# Diagnose an unsupported bootstrap before any environment creation or replacement.
"${PYTHON_BOOTSTRAP_BIN}" -c 'from tools.workspace_governance.cli.bootstrap import main; raise SystemExit(main(check_only=True))'

# `gov env` is the shell boundary for governed execution state. It resolves the
# mode and interpreter with the same precedence as doctor and verification, so
# bootstrap cannot accidentally mutate an overlay interpreter when an explicit
# governed override selects another one.
GOVERNED_ENV="$(./gov env --allow-missing-interpreter)"
eval "$GOVERNED_ENV"
MODE="$TET4D_ENVIRONMENT_MODE"

declared_dependencies() {
  "${PYTHON_BOOTSTRAP_BIN}" -c '
import pathlib, tomllib

project = tomllib.loads(pathlib.Path("pyproject.toml").read_text())["project"]
items = list(project.get("dependencies", []))
for extra in project.get("optional-dependencies", {}).values():
    items.extend(extra)
print("\n".join(items))
'
}

dependency_fingerprint() {
  "$1" -c '
import hashlib, pathlib, sys, tomllib

project = tomllib.loads(pathlib.Path("pyproject.toml").read_text())["project"]
digest = hashlib.sha256()
digest.update(f"python={sys.version_info.major}.{sys.version_info.minor}\n".encode())
digest.update(repr(sorted(project.get("dependencies", []))).encode())
digest.update(repr(sorted(
    (name, sorted(values))
    for name, values in project.get("optional-dependencies", {}).items()
)).encode())
print(digest.hexdigest())
'
}

if [[ "$MODE" == "source" ]]; then
  TARGET_PYTHON="$PYTHON_BIN"
  PREFIX="$("$TARGET_PYTHON" -c 'import sys; print(sys.prefix)')"
  FINGERPRINT_PATH="${PREFIX}/.tet4d-dependency-fingerprint"
  LOCK_DIR="${PREFIX}/.tet4d-sync.lock"

  # A shared environment is reachable from every worktree at once, and each
  # worktree's verify lock guards only its own tree. Serialise mutation here or
  # two checkouts can install into one site-packages simultaneously.
  if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    echo "bootstrap: another checkout is synchronising ${PREFIX}" >&2
    echo "bootstrap: lock: ${LOCK_DIR}" >&2
    exit 1
  fi
  trap 'rmdir "$LOCK_DIR" 2>/dev/null || true' EXIT

  fingerprint="$(dependency_fingerprint "$TARGET_PYTHON")"
  if [[ -f "$FINGERPRINT_PATH" && "$(<"$FINGERPRINT_PATH")" == "$fingerprint" ]]; then
    echo "Dependencies already synchronised: ${PREFIX}"
  else
    # `mapfile` is bash 4+, and macOS ships 3.2, so read the list portably.
    requirements=()
    while IFS= read -r requirement; do
      if [[ -n "$requirement" ]]; then
        requirements+=("$requirement")
      fi
    done < <(declared_dependencies)
    "$TARGET_PYTHON" -m pip install "${PIP_ARGS[@]}" "${requirements[@]}"
    printf '%s\n' "$fingerprint" >"$FINGERPRINT_PATH"
    echo "Dependencies synchronised: ${PREFIX}"
  fi

  # Deliberately no project install: the checkout supplies its own source, and
  # an installed distribution here would make one checkout authoritative for
  # every other sharing this interpreter.
  ./scripts/install_git_hooks.sh
  echo "Shared toolchain ready; each checkout binds its own source."
  exit 0
fi

TARGET_PYTHON="$PYTHON_BIN"
if [ ! -x "${TARGET_PYTHON}" ]; then
  VENV_PATH="$(dirname "$(dirname "${TARGET_PYTHON}")")"
  "${PYTHON_BOOTSTRAP_BIN}" -m venv "${VENV_PATH}"
fi
"${TARGET_PYTHON}" -m pip install "${PIP_ARGS[@]}" --upgrade pip
"${TARGET_PYTHON}" -m pip install "${PIP_ARGS[@]}" -e ".[dev]"
GOVERNANCE_PYTHON="${PYTHON_BOOTSTRAP_BIN}" TET4D_PYTHON="${TARGET_PYTHON}" \
  ./gov doctor >/dev/null

./scripts/install_git_hooks.sh

echo "Environment bootstrap complete: ${VENV_PATH}"
echo "No activation is required; governed scripts use the workspace resolver."
