#!/bin/sh
# Pack-managed PreToolUse guard (workspace-governance, NO_AUTONOMOUS_POLLING).
# Usage: no_polling.sh <claude|codex> [prompt]; hook JSON arrives on stdin.
# Fail closed: any failure to start or run the shared classifier blocks the
# tool call (exit 2). Prompt mode only advances the observation epoch and
# never blocks a user prompt.
mode="${2:-tool}"
fail() {
  echo "NO_AUTONOMOUS_POLLING (GUARD_FAILURE): $1; the call is blocked. Repair the pack-managed hook (./gov check)." >&2
  if [ "$mode" = prompt ]; then exit 0; fi
  exit 2
}
here=$(CDPATH='' cd -- "$(dirname -- "$0")" 2>/dev/null && pwd) || fail "hook directory unavailable"
root=$(CDPATH='' cd -- "$here/../../.." 2>/dev/null && pwd) || fail "consumer root unavailable"
python=""
if [ -x "$root/scripts/resolve_bootstrap_python.sh" ]; then
  python=$("$root/scripts/resolve_bootstrap_python.sh" 2>/dev/null) || python=""
fi
if [ -z "$python" ] && [ -n "${GOVERNANCE_PYTHON:-}" ]; then
  python="$GOVERNANCE_PYTHON"
fi
[ -n "$python" ] && [ -x "$python" ] || fail "no approved governance interpreter"
"$python" -I -B "$here/no_polling.py" "$@"
status=$?
case "$status" in
  0) exit 0 ;;
  2) if [ "$mode" = prompt ]; then exit 0; fi; exit 2 ;;
  *) fail "classifier exited with status $status" ;;
esac
