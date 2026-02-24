#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

ENGINE_DIR="src/tet4d/engine"
AI_DIR="src/tet4d/ai"

if [[ ! -d "$ENGINE_DIR" ]]; then
  exit 0
fi

# Ignore common noise directories.
RG_BASE=(rg -n --hidden --glob '!.git/**' --glob '!.venv/**' --glob '!**/__pycache__/**')

fail() {
  echo "$1" >&2
  exit 2
}

collect_import_files() {
  local pattern="$1"
  shift
  if ! "${RG_BASE[@]}" "$pattern" "$@" >/dev/null; then
    return 0
  fi
  "${RG_BASE[@]}" "$pattern" "$@" | cut -d: -f1 | sort -u
}

print_unexpected_list() {
  local label="$1"
  shift
  echo "$label" >&2
  for item in "$@"; do
    echo "  - $item" >&2
  done
}

append_lines_to_array() {
  local __var_name="$1"
  local line
  while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    eval "$__var_name+=(\"\$line\")"
  done
}

# 1) Engine must not import pygame.
# Transitional Stage 1 behavior: lock the current mixed-layer baseline and fail only on new
# pygame imports outside the known adapter-heavy engine modules. Tests are excluded.
pygame_files=()
append_lines_to_array pygame_files < <(
  collect_import_files \
    '^\s*(import|from)\s+pygame(\.|(\s|$))' \
    "$ENGINE_DIR" \
    --glob '!src/tet4d/engine/tests/**'
)

PYGAME_IMPORT_ALLOWLIST=$(cat <<'EOF'
src/tet4d/engine/app_runtime.py
src/tet4d/engine/audio.py
src/tet4d/engine/bot_options_menu.py
src/tet4d/engine/camera_mouse.py
src/tet4d/engine/control_helper.py
src/tet4d/engine/control_icons.py
src/tet4d/engine/display.py
src/tet4d/engine/font_profiles.py
src/tet4d/engine/front3d_game.py
src/tet4d/engine/front3d_render.py
src/tet4d/engine/front3d_setup.py
src/tet4d/engine/front4d_game.py
src/tet4d/engine/front4d_render.py
src/tet4d/engine/frontend_nd.py
src/tet4d/engine/game_loop_common.py
src/tet4d/engine/gfx_game.py
src/tet4d/engine/gfx_panel_2d.py
src/tet4d/engine/grid_mode_render.py
src/tet4d/engine/help_menu.py
src/tet4d/engine/key_display.py
src/tet4d/engine/keybindings.py
src/tet4d/engine/keybindings_defaults.py
src/tet4d/engine/keybindings_menu.py
src/tet4d/engine/keybindings_menu_input.py
src/tet4d/engine/keybindings_menu_view.py
src/tet4d/engine/launcher_nd_runner.py
src/tet4d/engine/launcher_play.py
src/tet4d/engine/launcher_settings.py
src/tet4d/engine/loop_runner_nd.py
src/tet4d/engine/menu_control_guides.py
src/tet4d/engine/menu_controls.py
src/tet4d/engine/menu_keybinding_shortcuts.py
src/tet4d/engine/menu_model.py
src/tet4d/engine/menu_runner.py
src/tet4d/engine/panel_utils.py
src/tet4d/engine/pause_menu.py
src/tet4d/engine/projection3d.py
src/tet4d/engine/text_render_cache.py
src/tet4d/engine/ui_utils.py
EOF
)

unexpected_pygame=()
for f in "${pygame_files[@]}"; do
  if ! grep -Fqx "$f" <<<"$PYGAME_IMPORT_ALLOWLIST"; then
    unexpected_pygame+=("$f")
  fi
done
if ((${#unexpected_pygame[@]})); then
  print_unexpected_list \
    "Architecture violation: new engine pygame imports detected outside Stage 1 allowlist." \
    "${unexpected_pygame[@]}"
  fail "Architecture violation: engine imports pygame (forbidden; baseline-only exceptions allowed temporarily)."
fi

# 2) Engine must not import UI (planned package path).
ui_imports=()
append_lines_to_array ui_imports < <(
  collect_import_files \
    '^\s*(import|from)\s+tet4d\.ui(\.|(\s|$))' \
    "$ENGINE_DIR" \
    --glob '!src/tet4d/engine/tests/**'
)
if ((${#ui_imports[@]})); then
  print_unexpected_list "Architecture violation: engine imports tet4d.ui (forbidden)." "${ui_imports[@]}"
  fail "Architecture violation: engine imports tet4d.ui (forbidden)."
fi

# 3) Engine must not import tools (either in-package or top-level).
tools_pkg_imports=()
append_lines_to_array tools_pkg_imports < <(
  collect_import_files \
    '^\s*(import|from)\s+tet4d\.tools(\.|(\s|$))' \
    "$ENGINE_DIR" \
    --glob '!src/tet4d/engine/tests/**'
)
if ((${#tools_pkg_imports[@]})); then
  print_unexpected_list "Architecture violation: engine imports tet4d.tools (forbidden)." "${tools_pkg_imports[@]}"
  fail "Architecture violation: engine imports tet4d.tools (forbidden)."
fi

tools_top_imports=()
append_lines_to_array tools_top_imports < <(
  collect_import_files \
    '^\s*(import|from)\s+tools(\.|(\s|$))' \
    "$ENGINE_DIR" \
    --glob '!src/tet4d/engine/tests/**'
)
if ((${#tools_top_imports[@]})); then
  print_unexpected_list "Architecture violation: engine imports top-level tools (forbidden)." "${tools_top_imports[@]}"
  fail "Architecture violation: engine imports top-level tools (forbidden)."
fi

# 4) AI package should depend on engine.api only (no deep engine imports).
if [[ -d "$AI_DIR" ]]; then
  ai_engine_import_lines="$("${RG_BASE[@]}" \
    '^\s*(import|from)\s+tet4d\.engine(\.|(\s|$))' \
    "$AI_DIR" \
    --glob '!src/tet4d/ai/tests/**' || true)"
  if [[ -n "${ai_engine_import_lines}" ]]; then
    ai_disallowed_lines="$(printf '%s\n' "$ai_engine_import_lines" | grep -Ev \
      '^\s*[^:]+:\d+:\s*(import|from)\s+tet4d\.engine\.api(\.|(\s|$))|^\s*[^:]+:\d+:\s*from\s+tet4d\.engine\s+import\s+api(\s|,|$)' \
      || true)"
    if [[ -n "${ai_disallowed_lines}" ]]; then
      echo "Architecture violation: tet4d.ai imports deep engine internals (use tet4d.engine.api)." >&2
      printf '%s\n' "$ai_disallowed_lines" >&2
      fail "Architecture violation: tet4d.ai must import tet4d.engine.api only."
    fi
  fi
fi

exit 0
