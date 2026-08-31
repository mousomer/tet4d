#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APP_PATH="${1:-$ROOT_DIR/artifacts/godot/macos/Tet4D.app}"

if [[ ! -d "$APP_PATH" ]]; then
  echo "Exported Tet4D app is missing: $APP_PATH" >&2
  exit 1
fi

stage_root="$(mktemp -d "/private/tmp/tet4d-release-smoke.XXXXXX")"
trap 'rm -rf "$stage_root"' EXIT
staged_app="$stage_root/Tet4D.app"
ditto "$APP_PATH" "$staged_app"
staged_binary="$staged_app/Contents/MacOS/Tet4D"

for run_number in 1 2; do
  user_root="$stage_root/user-$run_number"
  log_path="$stage_root/clean-start-$run_number.log"
  mkdir -p "$user_root/home"
  (
    cd "$stage_root"
    env HOME="$user_root/home" \
      XDG_CACHE_HOME="$user_root/cache" \
      XDG_CONFIG_HOME="$user_root/config" \
      XDG_DATA_HOME="$user_root/data" \
      "$staged_binary" --headless --quit-after 8 --log-file "$log_path"
  )
  if grep -Eiq 'SCRIPT ERROR|ERROR:|Failed to load|Cannot load|GDExtension.*(fail|error)' "$log_path"; then
    echo "Exported app clean-start smoke $run_number emitted an error:" >&2
    sed -n '1,160p' "$log_path" >&2
    exit 1
  fi
done

echo "Exported app passed two isolated outside-tree clean-start smoke runs."
