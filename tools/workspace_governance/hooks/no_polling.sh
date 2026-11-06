#!/bin/sh
# Pack-managed PreToolUse guard (workspace-governance, NO_AUTONOMOUS_POLLING).
# Usage: no_polling.sh <claude|codex> [prompt]; hook JSON arrives on stdin.
# Fail closed: any failure to start or run the shared classifier blocks the
# tool call (exit 2), and a deadline below the runtime's 30 s hook timeout turns
# a hang into a block before the runtime would let the call proceed. Prompt
# mode only advances the observation epoch and never blocks a user prompt.
mode="${2:-tool}"
deadline="${NO_POLLING_GUARD_DEADLINE:-20}"
case "$deadline" in
  [1-9] | 1[0-9] | 2[0-5]) ;;
  *) deadline=20 ;;
esac
fail() {
  echo "NO_AUTONOMOUS_POLLING (GUARD_FAILURE): $1; the call is blocked. Repair the pack-managed hook (./gov check)." >&2
  if [ "$mode" = prompt ]; then exit 0; fi
  exit 2
}
here=$(CDPATH='' cd -- "$(dirname -- "$0")" 2>/dev/null && pwd) || fail "hook directory unavailable"
root="${here%/tools/workspace_governance/hooks}"
[ "$root" != "$here" ] || fail "consumer root unavailable"
exec 3<&0
guard() {
  python=""
  if [ -x "$root/scripts/resolve_bootstrap_python.sh" ]; then
    python=$("$root/scripts/resolve_bootstrap_python.sh" 2>/dev/null) || python=""
  fi
  if [ -z "$python" ] && [ -n "${GOVERNANCE_PYTHON:-}" ]; then
    python="$GOVERNANCE_PYTHON"
  fi
  [ -n "$python" ] && [ -x "$python" ] || exit 97
  exec "$python" -I -B "$here/no_polling.py" "$@" <&3
}
guard "$@" &
child=$!
(
  trap 'kill "$sleeper" 2>/dev/null; exit 0' TERM
  sleep "$deadline" &
  sleeper=$!
  wait "$sleeper"
  kill -KILL "$child" 2>/dev/null
) </dev/null >/dev/null 2>&1 &
watchdog=$!
wait "$child"
status=$?
kill "$watchdog" 2>/dev/null
case "$status" in
  0) exit 0 ;;
  2) if [ "$mode" = prompt ]; then exit 0; fi; exit 2 ;;
  97) fail "no approved governance interpreter" ;;
  137) fail "classifier exceeded its ${deadline}s deadline" ;;
  *) fail "classifier exited with status $status" ;;
esac
