#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

absolute_path_pattern='(/Users/|/home/|[A-Za-z]:\\)'

search_repo_text() {
  local pattern="$1"
  if command -v rg >/dev/null 2>&1; then
    rg -n -I --hidden \
      --glob '!**/.git/**' \
      --glob '!**/.venv/**' \
      --glob '!**/__pycache__/**' \
      "$pattern" .
    return
  fi
  grep -RInE \
    --exclude-dir=.git \
    --exclude-dir=.venv \
    --exclude-dir=__pycache__ \
    --binary-files=without-match \
    "$pattern" .
}

if search_repo_text "$absolute_path_pattern"; then
  echo "Absolute filesystem paths detected." >&2
  exit 2
fi

space_name="$(
  find . \
    \( -path './.git' -o -path './.venv' \) -prune -o \
    -name '* *' -print -quit
)"
if [[ -n "$space_name" ]]; then
  echo "Filenames with spaces detected: ${space_name#./}" >&2
  exit 2
fi
