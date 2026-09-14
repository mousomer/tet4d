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

# Print one line per declaration this interpreter does not satisfy, and nothing
# at all when it satisfies every one. A predicate could only report that
# something is wrong; the caller has to be able to say which requirement it was.
unsatisfied_dependencies() {
  "$1" -c '
import importlib.metadata as metadata
import pathlib, tomllib
try:
    from packaging.requirements import Requirement
except ImportError:
    print("packaging is not importable, so declarations cannot be evaluated")
    raise SystemExit(0)
project = tomllib.loads(pathlib.Path("pyproject.toml").read_text())["project"]
groups = [("", project.get("dependencies", []))]
groups.extend(project.get("optional-dependencies", {}).items())
for extra, declarations in groups:
    for declaration in declarations:
        requirement = Requirement(declaration)
        if requirement.marker and not requirement.marker.evaluate({"extra": extra}):
            continue
        try:
            installed = metadata.version(requirement.name)
        except metadata.PackageNotFoundError:
            print(f"{declaration}: not installed")
            continue
        if installed not in requirement.specifier:
            print(f"{declaration}: installed {installed}")
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
  # Assign before testing rather than substituting inside `[[ ]]`, where `set -e`
  # does not apply: a crashing probe would yield an empty string and read as a
  # satisfied environment, which is the one answer it must never produce.
  if [[ -f "$FINGERPRINT_PATH" && "$(<"$FINGERPRINT_PATH")" == "$fingerprint" ]]; then
    # The digest records what this repository declares, never what a shared
    # environment contains, so a match is only ever an optimisation.
    sync_reason="$(unsatisfied_dependencies "$TARGET_PYTHON")"
  else
    sync_reason="the declared dependency digest does not match"
  fi

  if [[ -z "$sync_reason" ]]; then
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
    # pip exits zero when another project's pin wins the resolution, and the
    # fingerprint is the cache key every later run consults. Refuse to record
    # one, and name what is wrong instead of failing without saying why.
    remaining="$(unsatisfied_dependencies "$TARGET_PYTHON")"
    if [[ -n "$remaining" ]]; then
      echo "bootstrap: installation did not satisfy the declaration: ${PREFIX}" >&2
      while IFS= read -r gap; do
        echo "bootstrap: ${gap}" >&2
      done <<<"$remaining"
      exit 1
    fi
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
# Derive the prefix unconditionally: it is reported at the end regardless of
# whether this run had to create the environment, and assigning it only in the
# creating branch left it unset on every re-run.
VENV_PATH="$(dirname "$(dirname "${TARGET_PYTHON}")")"
if [ ! -x "${TARGET_PYTHON}" ]; then
  "${PYTHON_BOOTSTRAP_BIN}" -m venv "${VENV_PATH}"
fi
"${TARGET_PYTHON}" -m pip install "${PIP_ARGS[@]}" --upgrade pip
"${TARGET_PYTHON}" -m pip install "${PIP_ARGS[@]}" -e ".[dev]"
GOVERNANCE_PYTHON="${PYTHON_BOOTSTRAP_BIN}" TET4D_PYTHON="${TARGET_PYTHON}" \
  ./gov doctor >/dev/null

./scripts/install_git_hooks.sh

echo "Environment bootstrap complete: ${VENV_PATH}"
echo "No activation is required; governed scripts use the workspace resolver."
