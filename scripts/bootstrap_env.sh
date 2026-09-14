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

dependency_snapshot() {
  "$1" -c '
import json, pathlib, tomllib

project = tomllib.loads(pathlib.Path("pyproject.toml").read_text())["project"]
items = list(project.get("dependencies", []))
for values in project.get("optional-dependencies", {}).values():
    items.extend(values)
print(json.dumps(sorted(set(items))))
'
}

requirements_for_snapshot() {
  TET4D_DEPENDENCY_SNAPSHOT="$1" "$PYTHON_BOOTSTRAP_BIN" -c '
import json, os

payload = json.load(open(os.environ["TET4D_DEPENDENCY_SNAPSHOT"], encoding="utf-8"))
if not isinstance(payload, list) or not all(isinstance(item, str) for item in payload):
    raise SystemExit("invalid shared dependency snapshot")
print("\n".join(payload))
'
}

compatibility_report() {
  TET4D_COMPAT_EXISTING="$2" TET4D_COMPAT_REQUESTED="$3" "$1" -c '
import json, os, subprocess, sys

existing = json.load(open(os.environ["TET4D_COMPAT_EXISTING"], encoding="utf-8"))
requested = json.loads(os.environ["TET4D_COMPAT_REQUESTED"])
probe = subprocess.run(
    [sys.executable, "-m", "tools.workspace_governance.dependency_compatibility"],
    input=json.dumps({"existing": existing, "requested": requested}),
    text=True,
    capture_output=True,
    check=False,
)
if probe.stdout:
    print(probe.stdout, end="")
raise SystemExit(probe.returncode)
'
}

# Print one line per declaration this interpreter does not satisfy, and nothing
# at all when it satisfies every one. A predicate could only report that
# something is wrong; the caller has to be able to say which requirement it was.
unsatisfied_dependencies() {
  TET4D_DEPENDENCY_REQUIREMENTS="$2" "$1" -c '
import importlib.metadata as metadata, os
try:
    from packaging.requirements import Requirement
except ImportError:
    print("packaging is not importable, so declarations cannot be evaluated")
    raise SystemExit(0)
for declaration in open(os.environ["TET4D_DEPENDENCY_REQUIREMENTS"], encoding="utf-8"):
    declaration = declaration.strip()
    if not declaration:
        continue
    requirement = Requirement(declaration)
    if requirement.marker and not requirement.marker.evaluate():
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
  SNAPSHOT_PATH="${PREFIX}/.tet4d-dependency-requirements.json"
  LOCK_DIR="${PREFIX}/.tet4d-sync.lock"

  # A shared environment is reachable from every worktree at once, and each
  # worktree's verify lock guards only its own tree. Serialise mutation here or
  # two checkouts can install into one site-packages simultaneously.
  lock_owner="${LOCK_DIR}/owner"
  lock_host="$(hostname 2>/dev/null || uname -n)"
  lock_start="$(ps -p "$$" -o lstart= 2>/dev/null | tr -s ' ' | sed 's/^ //' || true)"
  lock_start="${lock_start:-unavailable}"
  acquire_lock() {
    if mkdir "$LOCK_DIR" 2>/dev/null; then
      printf 'pid=%s\nhost=%s\nstart=%s\n' "$$" "$lock_host" "$lock_start" >"$lock_owner"
      return 0
    fi
    if [[ ! -f "$lock_owner" ]]; then
      echo "bootstrap: lock: ${LOCK_DIR}; owner metadata is missing, refusing recovery" >&2
      return 1
    fi
    unset owner_pid owner_host owner_start
    while IFS='=' read -r key value; do
      case "$key" in pid) owner_pid="$value";; host) owner_host="$value";; start) owner_start="$value";; esac
    done <"$lock_owner"
    if [[ -z "${owner_pid:-}" || -z "${owner_host:-}" || -z "${owner_start:-}" ]]; then
      echo "bootstrap: lock: ${LOCK_DIR}; owner metadata is incomplete, refusing recovery" >&2
      return 1
    fi
    if [[ "$owner_host" != "$lock_host" ]]; then
      echo "bootstrap: lock: ${LOCK_DIR}; owner ${owner_pid}@${owner_host} is foreign, refusing recovery" >&2
      return 1
    fi
    if kill -0 "$owner_pid" 2>/dev/null; then
      observed_start="$(ps -p "$owner_pid" -o lstart= 2>/dev/null | tr -s ' ' | sed 's/^ //' || true)"
      if [[ "$owner_start" == "unavailable" || -z "$observed_start" || "$observed_start" == "$owner_start" ]]; then
        echo "bootstrap: lock: ${LOCK_DIR}; live owner ${owner_pid}@${owner_host} (${owner_start})" >&2
        return 1
      fi
      echo "bootstrap: lock: ${LOCK_DIR}; PID ${owner_pid} was reused; recovering stale owner" >&2
    else
      echo "bootstrap: lock: ${LOCK_DIR}; local owner ${owner_pid}@${owner_host} is stale; recovering" >&2
    fi
    rm -f "$lock_owner"
    if ! rmdir "$LOCK_DIR"; then
      echo "bootstrap: lock: ${LOCK_DIR}; stale lock could not be removed" >&2
      return 1
    fi
    mkdir "$LOCK_DIR"
    printf 'pid=%s\nhost=%s\nstart=%s\n' "$$" "$lock_host" "$lock_start" >"$lock_owner"
  }
  release_lock() { rm -f "$lock_owner"; rmdir "$LOCK_DIR" 2>/dev/null || true; }
  if ! acquire_lock; then
    exit 1
  fi
  trap release_lock EXIT

  requested_snapshot="$(dependency_snapshot "$TARGET_PYTHON")"
  if [[ -f "$SNAPSHOT_PATH" ]]; then
    if ! report="$(compatibility_report "$PYTHON_BOOTSTRAP_BIN" "$SNAPSHOT_PATH" "$requested_snapshot")"; then
      echo "bootstrap: shared dependency declarations are not certifiably compatible: ${PREFIX}" >&2
      echo "$report" >&2
      exit 1
    fi
    combined_snapshot="$("$PYTHON_BOOTSTRAP_BIN" - "$SNAPSHOT_PATH" "$requested_snapshot" <<'PY'
import json, sys
existing = json.load(open(sys.argv[1], encoding="utf-8"))
requested = json.loads(sys.argv[2])
print(json.dumps(sorted(set(existing) | set(requested))))
PY
)"
  else
    combined_snapshot="$requested_snapshot"
  fi
  snapshot_tmp="${SNAPSHOT_PATH}.new"
  printf '%s\n' "$combined_snapshot" >"$snapshot_tmp"
  fingerprint="$(printf '%s' "$combined_snapshot" | "$PYTHON_BOOTSTRAP_BIN" -c 'import hashlib,sys; print(hashlib.sha256(sys.stdin.buffer.read()).hexdigest())')"
  requirements_tmp="${PREFIX}/.tet4d-dependency-requirements.txt"
  printf '%s\n' "$combined_snapshot" >"${requirements_tmp}.json"
  requirements_for_snapshot "${requirements_tmp}.json" >"$requirements_tmp"
  # Assign before testing rather than substituting inside `[[ ]]`, where `set -e`
  # does not apply: a crashing probe would yield an empty string and read as a
  # satisfied environment, which is the one answer it must never produce.
  if [[ -f "$FINGERPRINT_PATH" && "$(<"$FINGERPRINT_PATH")" == "$fingerprint" ]]; then
    # The digest records what this repository declares, never what a shared
    # environment contains, so a match is only ever an optimisation.
    sync_reason="$(unsatisfied_dependencies "$TARGET_PYTHON" "$requirements_tmp")"
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
    done <"$requirements_tmp"
    "$TARGET_PYTHON" -m pip install "${PIP_ARGS[@]}" "${requirements[@]}"
    # pip exits zero when another project's pin wins the resolution, and the
    # fingerprint is the cache key every later run consults. Refuse to record
    # one, and name what is wrong instead of failing without saying why.
    remaining="$(unsatisfied_dependencies "$TARGET_PYTHON" "$requirements_tmp")"
    if [[ -n "$remaining" ]]; then
      echo "bootstrap: installation did not satisfy the declaration: ${PREFIX}" >&2
      while IFS= read -r gap; do
        echo "bootstrap: ${gap}" >&2
      done <<<"$remaining"
      exit 1
    fi
    printf '%s\n' "$fingerprint" >"$FINGERPRINT_PATH"
    mv "$snapshot_tmp" "$SNAPSHOT_PATH"
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
