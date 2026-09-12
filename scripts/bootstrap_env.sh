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
VENV_PATH="${VENV_PATH:-.venv}"
VENV_PYTHON="${VENV_PATH}/bin/python"
PIP_ARGS=(--disable-pip-version-check --no-input)

# Diagnose an unsupported bootstrap before any environment creation or replacement.
"${PYTHON_BOOTSTRAP_BIN}" -c 'from tools.workspace_governance.cli.bootstrap import main; raise SystemExit(main(check_only=True))'

# Read the declaration through the governance resolver, not a second parser. The
# bootstrap interpreter can import it because check-level governance is
# standard-library only, which matters here: this runs before the environment
# it is about to build exists.
read -r MODE DECLARED_INTERPRETER <<<"$(
  "${PYTHON_BOOTSTRAP_BIN}" -c '
from pathlib import Path
from tools.workspace_governance.resolver.core import GovernanceResolver
from tools.workspace_governance.validators.core import resolve_execution_mode

resolver = GovernanceResolver.for_root(Path.cwd())
_, project, _ = resolver.load()
local, _ = resolver.local_overlay()
mode = resolve_execution_mode(project, None, local)[0]
print(mode, (local or {}).get("interpreter", ""))
'
)"

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
  "${PYTHON_BOOTSTRAP_BIN}" -c '
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
  if [[ -z "$DECLARED_INTERPRETER" ]]; then
    echo "bootstrap: source mode needs an interpreter declared in an overlay" >&2
    echo "bootstrap: see docs/architecture/workspace_governance_v0_1.md" >&2
    exit 1
  fi
  TARGET_PYTHON="$DECLARED_INTERPRETER"
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

  fingerprint="$(dependency_fingerprint)"
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

if [ ! -x "${VENV_PYTHON}" ]; then
  "${PYTHON_BOOTSTRAP_BIN}" -m venv "${VENV_PATH}"
fi
"${VENV_PYTHON}" -m pip install "${PIP_ARGS[@]}" --upgrade pip
"${VENV_PYTHON}" -m pip install "${PIP_ARGS[@]}" -e ".[dev]"
GOVERNANCE_PYTHON="${VENV_PYTHON}" TET4D_PYTHON="${VENV_PYTHON}" \
  ./gov doctor >/dev/null

./scripts/install_git_hooks.sh

echo "Environment bootstrap complete: ${VENV_PATH}"
echo "No activation is required; governed scripts use the workspace resolver."
