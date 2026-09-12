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



# An empty target list defaults to the declared scope once the interpreter is
# resolved below, so this gate cannot be narrower than the canonical one.




eval "$(./gov env)"

# Both gates read their Ruff scope from one authority. Carrying separate target
# lists is how repository-wide formatting drift stayed invisible to whichever
# list was narrower.
static_analysis_scope() {
  "$PYTHON_BIN" - "$1" <<'SCOPE'
import json
import pathlib
import sys

rules = json.loads(pathlib.Path("config/project/policy_pack.json").read_text())
print(" ".join(rules["code_rules"]["static_analysis"][sys.argv[1]]))
SCOPE
}

if [[ ${#RUFF_TARGETS[@]} -eq 0 ]]; then
  read -r -a RUFF_TARGETS <<<"$(static_analysis_scope ruff_format_scope)"
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

# Importability is not origin. `gov doctor` owns that assertion -- interpreter,
# binding, and which checkout the import resolved from -- so the focused gate
# cannot report success against another worktree's source.
./gov doctor >/dev/null



RUFF_CHECK_TARGETS=()
while IFS= read -r target; do
  [[ -n "$target" ]] && RUFF_CHECK_TARGETS+=("$target")
done < <(filter_python_targets "${RUFF_TARGETS[@]}")

if [[ ${#RUFF_CHECK_TARGETS[@]} -gt 0 ]]; then

  "$PYTHON_BIN" -m ruff check "${RUFF_CHECK_TARGETS[@]}"

fi



FORMAT_TARGETS=()
while IFS= read -r target; do
  [[ -n "$target" ]] && FORMAT_TARGETS+=("$target")
done < <(filter_python_targets "${RUFF_TARGETS[@]}")

if [[ ${#FORMAT_TARGETS[@]} -gt 0 ]]; then

  "$PYTHON_BIN" -m ruff format --check "${FORMAT_TARGETS[@]}"

fi



if [[ "$CHECK_DOCS" == "1" ]]; then

  "$PYTHON_BIN" tools/governance/validate_governance.py

  "$PYTHON_BIN" tools/governance/generate_configuration_reference.py --check

  "$PYTHON_BIN" tools/governance/generate_maintenance_docs.py --check

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
