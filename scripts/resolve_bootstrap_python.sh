#!/usr/bin/env bash
set -euo pipefail

# Bootstrap interpreter selection.
#
# This runs before a project environment is guaranteed to exist, so it must not
# import project code. It is deliberately separate from the certification chain
# owned by `gov doctor`: this only decides what may *start* governance, never
# what gets verified.
#
# System Python on PATH is never an approved bootstrap. A bare `python3` is not
# a declared toolchain, and accepting one silently changes what every later
# check runs against. Priority is explicit override, then the workspace venv,
# then the inherited workspace overlay, then the repository venv. There is no
# fallback past the declared candidates: if none is executable, this fails.
#
# The inherited overlay is read here, in shell, on purpose. Bootstrap cannot ask
# the target interpreter to parse the configuration that selects it, so the
# reader below is a small JSON scanner rather than a grep: an overlay may carry
# a `tool_paths` entry whose key is also `interpreter`, and matching that nested
# key would silently start governance under the wrong Python.

cd "$(dirname "$0")/.."

WORKSPACE_MANIFEST=".governance/workspace.json"
INHERITED_OVERLAY=""

# Print the string value of one *top-level* key, or nothing. Depth-aware, so a
# matching key nested inside another object is never returned. Refuses any
# escape other than \" \\ \/ rather than guessing at an interpreter path.
json_top_level_string() {
  awk -v want="$2" '
    { text = text $0 "\n" }
    END {
      n = length(text); i = 1; depth = 0; key = ""
      while (i <= n) {
        c = substr(text, i, 1)
        if (c == "\"") {
          i++; s = ""
          while (i <= n) {
            c = substr(text, i, 1)
            if (c == "\\") {
              e = substr(text, i + 1, 1)
              if (e == "\"" || e == "\\" || e == "/") { s = s e; i += 2; continue }
              exit 0
            }
            if (c == "\"") { i++; break }
            s = s c; i++
          }
          j = i
          while (j <= n && substr(text, j, 1) ~ /[ \t\r\n]/) j++
          if (substr(text, j, 1) == ":") {
            if (depth == 1) key = s
            i = j + 1
          } else {
            if (depth == 1 && key == want) { print s; exit 0 }
            i = j
          }
          continue
        }
        if (c == "{" || c == "[") { depth++; i++; continue }
        if (c == "}" || c == "]") { depth--; i++; continue }
        i++
      }
    }
  ' "$1"
}

# Locate the overlay the certified resolver reads, keyed by workspace identity.
resolve_inherited_overlay() {
  [[ -f "$WORKSPACE_MANIFEST" ]] || return 0
  local workspace_id
  workspace_id="$(json_top_level_string "$WORKSPACE_MANIFEST" workspace_id)"
  # The id becomes a filename, so refuse anything that could escape the
  # configuration directory rather than constructing a traversing path.
  [[ "$workspace_id" =~ ^[A-Za-z0-9._-]+$ ]] || return 0
  INHERITED_OVERLAY="${XDG_CONFIG_HOME:-$HOME/.config}/workspace-governance/${workspace_id}.local.json"
}

resolve_inherited_overlay

candidates=()
if [[ -n "${GOVERNANCE_PYTHON:-}" ]]; then
  candidates+=("$GOVERNANCE_PYTHON")
fi
if [[ -n "${WORKSPACE_VENV:-}" ]]; then
  candidates+=("${WORKSPACE_VENV%/}/bin/python")
fi
if [[ -n "$INHERITED_OVERLAY" && -f "$INHERITED_OVERLAY" ]]; then
  inherited_interpreter="$(json_top_level_string "$INHERITED_OVERLAY" interpreter)"
  if [[ -n "$inherited_interpreter" ]]; then
    candidates+=("$inherited_interpreter")
  fi
fi
candidates+=(".venv/bin/python")

for candidate in "${candidates[@]}"; do
  if [[ -x "$candidate" ]]; then
    printf '%s/%s\n' \
      "$(cd "$(dirname "$candidate")" && pwd)" "$(basename "$candidate")"
    exit 0
  fi
done

overlay_source="${INHERITED_OVERLAY:-inherited workspace overlay}"
printf '{"status":"ENVIRONMENT_INVALID","diagnostics":[{"code":"ENVIRONMENT_MISMATCH","fact":"bootstrap.interpreter","owner":"environment","sources":["GOVERNANCE_PYTHON","WORKSPACE_VENV","%s",".venv/bin/python"],"reason":"no approved bootstrap Python is executable; system Python on PATH is not an approved bootstrap","repair":"declare an interpreter in the inherited workspace overlay, export WORKSPACE_VENV, set GOVERNANCE_PYTHON or PYTHON_BOOTSTRAP_BIN, or create .venv with ./scripts/bootstrap_env.sh"}]}\n' \
  "$overlay_source" >&2
exit 1
