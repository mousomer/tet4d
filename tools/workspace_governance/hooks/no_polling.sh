#!/bin/sh
# Pack-managed PreToolUse guard (workspace-governance, supervised-completion-v3).
# Usage: no_polling.sh <claude|codex> [prompt]; hook JSON arrives on stdin.
# The classifier decides normally. When the guard itself fails (no approved
# interpreter, crash, deadline), the failure is scoped: only a call that plainly
# waits for or probes an operation is blocked (exit 2); every other call proceeds
# with a GUARD_DEGRADED warning. A waiting-policy failure never becomes a blanket
# prohibition of unrelated work. Prompt mode never blocks a user prompt. This
# launcher uses shell builtins only on its failure paths, so a broken PATH cannot
# turn into a blanket denial either.
mode="${2:-tool}"
runtime="${1:-}"
deadline="${NO_POLLING_GUARD_DEADLINE:-20}"
case "$deadline" in
  [1-9] | 1[0-9] | 2[0-5]) ;;
  *) deadline=20 ;;
esac
payload=""
while IFS= read -r line || [ -n "$line" ]; do
  payload="$payload$line
"
done
scoped() {
  if [ "$mode" = prompt ]; then exit 0; fi
  case "$payload" in
    *"gh run watch"* | *"gh run view"* | *"gh pr checks"* | *"--watch"* | \
    *"--interval"* | *"gh api"*"/runs"* | *"gh api"*"status"* | *"watch "* | \
    *"sleep "[0-9]* | *"tail -f"* | *"tail -F"* | *"while "*"sleep "* | \
    *"until "*"; do"* | *"ps -p"* | *"kill -0"* | *"pgrep "*)
      echo "NO_AUTONOMOUS_POLLING (GUARD_FAILURE): $1. This call looks like a wait or status probe, so it is blocked while the guard is degraded. Unrelated commands remain available; repair the pack-managed hook (./gov check)." >&2
      exit 2 ;;
  esac
  message="NO_AUTONOMOUS_POLLING (GUARD_DEGRADED): $1. Waiting-policy enforcement is degraded for this call, which is allowed because it is not a wait or status probe. Report this enforcement error; repair with ./gov check."
  echo "$message" >&2
  if [ "$runtime" = claude ]; then
    printf '{"systemMessage": "%s"}\n' "$message"
  fi
  exit 0
}
case "$0" in
  */*) here="${0%/*}" ;;
  *) here="." ;;
esac
here=$(CDPATH='' cd -- "$here" 2>/dev/null && pwd) || scoped "hook directory unavailable"
root="${here%/tools/workspace_governance/hooks}"
[ "$root" != "$here" ] || scoped "consumer root unavailable"
guard() {
  python=""
  if [ -x "$root/scripts/resolve_bootstrap_python.sh" ]; then
    python=$("$root/scripts/resolve_bootstrap_python.sh" 2>/dev/null) || python=""
  fi
  if [ -z "$python" ] && [ -n "${GOVERNANCE_PYTHON:-}" ]; then
    python="$GOVERNANCE_PYTHON"
  fi
  [ -n "$python" ] && [ -x "$python" ] || exit 97
  exec "$python" -I -B "$here/no_polling.py" "$@" <<GUARD_PAYLOAD
$payload
GUARD_PAYLOAD
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
  97) scoped "no approved governance interpreter" ;;
  137) scoped "classifier exceeded its ${deadline}s deadline" ;;
  *) scoped "classifier exited with status $status" ;;
esac
