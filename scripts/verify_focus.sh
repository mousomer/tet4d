#!/usr/bin/env bash

set -euo pipefail



cd "$(dirname "$0")/.."



CODEX_MODE="${CODEX_MODE:-1}"

CHECK_DOCS=0

RUFF_TARGETS=()

PYTEST_TARGETS=()

CURRENT_BUCKET="ruff"



usage() {

  cat <<'EOF'

Usage:

  ./scripts/verify_focus.sh [--docs] [ruff-targets...] [--pytest pytest-targets...]



Examples:

  ./scripts/verify_focus.sh src/tet4d/engine/topology_explorer tests/unit/engine/test_topology_explorer.py

  ./scripts/verify_focus.sh --docs tools/governance/generate_maintenance_docs.py --pytest tests/unit/governance/test_generate_maintenance_docs.py



Purpose:

  Fast staged local validation before the full canonical gate. This does not

  replace ./scripts/verify.sh before commit/push.

EOF

}



while [[ $# -gt 0 ]]; do

  case "$1" in

    --docs)

      CHECK_DOCS=1

      shift

      ;;

    --pytest)

      CURRENT_BUCKET="pytest"

      shift

      ;;

    -h|--help)

      usage

      exit 0

      ;;

    *)

      if [[ "$CURRENT_BUCKET" == "ruff" ]]; then

        RUFF_TARGETS+=("$1")

      else

        PYTEST_TARGETS+=("$1")

      fi

      shift

      ;;

  esac

done



if [[ ${#RUFF_TARGETS[@]} -eq 0 ]]; then

  RUFF_TARGETS=(".")

fi



if [[ -n "${PYTHON_BIN:-}" ]]; then

  :

elif [[ -x ".venv/bin/python" ]]; then

  PYTHON_BIN=".venv/bin/python"

elif [[ -x ".venv/Scripts/python.exe" ]]; then

  PYTHON_BIN=".venv/Scripts/python.exe"

elif command -v python3 >/dev/null 2>&1; then

  PYTHON_BIN="python3"

elif command -v python >/dev/null 2>&1; then

  PYTHON_BIN="python"

else

  echo "No Python runtime found. Set PYTHON_BIN or install python3." >&2

  exit 1

fi



require_module() {

  local module="$1"

  local package_name="$2"

  if "$PYTHON_BIN" -c "import ${module}" >/dev/null 2>&1; then

    return 0

  fi

  echo "Missing python module '${module}' in ${PYTHON_BIN}." >&2

  echo "Install it with: ${PYTHON_BIN} -m pip install ${package_name}" >&2

  exit 1

}



require_repo_package() {

  if "$PYTHON_BIN" -c "import tet4d" >/dev/null 2>&1; then

    return 0

  fi

  echo "Missing repo package 'tet4d' in ${PYTHON_BIN}." >&2

  echo "Run: ${PYTHON_BIN} -m pip install -e '.[dev]'" >&2

  exit 1

}



filter_python_targets() {

  local target

  local filtered=()

  for target in "$@"; do

    if [[ -d "$target" || "$target" == *.py || "$target" == "." ]]; then

      filtered+=("$target")

    fi

  done

  printf '%s\n' "${filtered[@]}"

}



require_module ruff ruff

require_repo_package



env PYTHON_BIN="$PYTHON_BIN" ./scripts/check_editable_install.sh

mapfile -t RUFF_CHECK_TARGETS < <(filter_python_targets "${RUFF_TARGETS[@]}")

if [[ ${#RUFF_CHECK_TARGETS[@]} -gt 0 ]]; then

  "$PYTHON_BIN" -m ruff check "${RUFF_CHECK_TARGETS[@]}"

fi



mapfile -t FORMAT_TARGETS < <(filter_python_targets "${RUFF_TARGETS[@]}")

if [[ ${#FORMAT_TARGETS[@]} -gt 0 ]]; then

  "$PYTHON_BIN" -m ruff format --check "${FORMAT_TARGETS[@]}"

fi



if [[ "$CHECK_DOCS" == "1" ]]; then

  "$PYTHON_BIN" tools/governance/validate_project_contracts.py

  "$PYTHON_BIN" tools/governance/generate_configuration_reference.py --check

  "$PYTHON_BIN" tools/governance/generate_maintenance_docs.py --check

  "$PYTHON_BIN" tools/governance/check_drift_protection.py

fi



if [[ ${#PYTEST_TARGETS[@]} -gt 0 ]]; then

  export TET4D_PYTEST_TMP_WORKAROUND=1

  PYTEST_ARGS=(-q --maxfail=1 --disable-warnings)

  if [[ "$CODEX_MODE" == "1" ]]; then

    export TET4D_STATE_ROOT="${TET4D_STATE_ROOT:-state/verify_focus}"

    PYTEST_ARGS+=(--basetemp="$TET4D_STATE_ROOT/pytest_basetemp" -p no:cacheprovider -p no:tmpdir)

  fi

  "$PYTHON_BIN" -m pytest "${PYTEST_ARGS[@]}" "${PYTEST_TARGETS[@]}"

fi



echo "verify_focus: OK"

