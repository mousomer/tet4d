# Shared release-boundary interpreter validation.  Packaging intentionally does
# not call `gov env`: release jobs must be hermetic and must not depend on a
# contributor's shared workspace overlay.

require_packaging_python() {
  local root_dir="$1"
  if [[ -z "${PYTHON_BIN:-}" ]]; then
    if [[ -x "$root_dir/.venv/bin/python" ]]; then
      PYTHON_BIN="$root_dir/.venv/bin/python"
    elif [[ -x "$root_dir/.venv/Scripts/python.exe" ]]; then
      PYTHON_BIN="$root_dir/.venv/Scripts/python.exe"
    else
      echo "packaging: no approved Python. Set PYTHON_BIN to an absolute interpreter path." >&2
      exit 1
    fi
  fi
  if [[ ! "$PYTHON_BIN" =~ ^(/|[A-Za-z]:[\\/]|\\\\) ]]; then
    echo "packaging: PYTHON_BIN must be an explicit absolute interpreter path; bare commands are not allowed: $PYTHON_BIN" >&2
    exit 1
  fi
  if [[ ! -f "$PYTHON_BIN" || ! -x "$PYTHON_BIN" ]]; then
    echo "packaging: PYTHON_BIN is not an executable interpreter file: $PYTHON_BIN" >&2
    exit 1
  fi
  export PYTHON_BIN
}
