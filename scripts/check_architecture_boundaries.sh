#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

ENGINE_DIR="src/tet4d/engine"
REPLAY_DIR="src/tet4d/replay"
UI_DIR="src/tet4d/ui"
AI_DIR="src/tet4d/ai"
TOOLS_STABILITY_DIR="tools/stability"
TOOLS_BENCHMARKS_DIR="tools/benchmarks"

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
src/tet4d/engine/ui_logic/menu_controls.py
src/tet4d/engine/ui_logic/menu_keybinding_shortcuts.py
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
# Transitional behavior: lock the current migration baseline and fail only on new
# engine->ui imports outside the known adapter-heavy engine modules.
ui_imports=()
append_lines_to_array ui_imports < <(
  collect_import_files \
    '^\s*(import|from)\s+tet4d\.ui(\.|(\s|$))' \
    "$ENGINE_DIR" \
    --glob '!src/tet4d/engine/tests/**'
)
ENGINE_UI_IMPORT_ALLOWLIST=$(cat <<'EOF'
src/tet4d/engine/api.py
src/tet4d/engine/app_runtime.py
src/tet4d/engine/bot_options_menu.py
src/tet4d/engine/front3d_game.py
src/tet4d/engine/front3d_render.py
src/tet4d/engine/front3d_setup.py
src/tet4d/engine/front4d_game.py
src/tet4d/engine/front4d_render.py
src/tet4d/engine/frontend_nd.py
src/tet4d/engine/gameplay/rotation_anim.py
src/tet4d/engine/gfx_game.py
src/tet4d/engine/gfx_panel_2d.py
src/tet4d/engine/grid_mode_render.py
src/tet4d/engine/help_menu.py
src/tet4d/engine/keybindings.py
src/tet4d/engine/keybindings_menu.py
src/tet4d/engine/keybindings_menu_view.py
src/tet4d/engine/launcher_nd_runner.py
src/tet4d/engine/launcher_play.py
src/tet4d/engine/launcher_settings.py
src/tet4d/engine/loop_runner_nd.py
src/tet4d/engine/pause_menu.py
src/tet4d/engine/view_controls.py
EOF
)
unexpected_engine_ui_imports=()
for f in "${ui_imports[@]}"; do
  if ! grep -Fqx "$f" <<<"$ENGINE_UI_IMPORT_ALLOWLIST"; then
    unexpected_engine_ui_imports+=("$f")
  fi
done
if ((${#unexpected_engine_ui_imports[@]})); then
  print_unexpected_list \
    "Architecture violation: new engine imports tet4d.ui outside baseline allowlist." \
    "${unexpected_engine_ui_imports[@]}"
  fail "Architecture violation: engine imports tet4d.ui (forbidden; baseline-only exceptions allowed temporarily)."
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

# 3b) Engine must not import replay modules (tests may import replay helpers).
replay_imports=()
append_lines_to_array replay_imports < <(
  collect_import_files \
    '^\s*(import|from)\s+tet4d\.replay(\.|(\s|$))' \
    "$ENGINE_DIR" \
    --glob '!src/tet4d/engine/tests/**'
)
if ((${#replay_imports[@]})); then
  print_unexpected_list "Architecture violation: engine imports tet4d.replay (forbidden)." "${replay_imports[@]}"
  fail "Architecture violation: engine imports tet4d.replay (forbidden)."
fi

check_engine_api_only_imports() {
  local dir="$1"
  local label="$2"
  local exclude_glob="${3:-}"
  [[ -d "$dir" ]] || return 0

  local args=("$dir")
  if [[ -n "$exclude_glob" ]]; then
    args+=(--glob "$exclude_glob")
  fi
  local import_lines
  import_lines="$("${RG_BASE[@]}" '^\s*(import|from)\s+tet4d\.engine(\.|(\s|$))' "${args[@]}" || true)"
  [[ -n "$import_lines" ]] || return 0

  local disallowed_lines
  disallowed_lines="$(printf '%s\n' "$import_lines" | grep -Ev \
    '^\s*[^:]+:[0-9]+:\s*(import|from)\s+tet4d\.engine\.api(\.|(\s|$))|^\s*[^:]+:[0-9]+:\s*from\s+tet4d\.engine\s+import\s+api(\s|,|$)' \
    || true)"
  if [[ -n "$disallowed_lines" ]]; then
    echo "Architecture violation: ${label} imports deep engine internals (use tet4d.engine.api)." >&2
    printf '%s\n' "$disallowed_lines" >&2
    fail "Architecture violation: ${label} must import tet4d.engine.api only."
  fi
}

# 4) Replay + AI packages should depend on engine.api only (no deep engine imports).
check_engine_api_only_imports "$REPLAY_DIR" "tet4d.replay"
check_engine_api_only_imports "$AI_DIR" "tet4d.ai" '!src/tet4d/ai/tests/**'

# 4b) UI adapters may still import engine internals during migration, but lock the current baseline.
if [[ -d "$UI_DIR" ]]; then
  ui_engine_imports=()
  append_lines_to_array ui_engine_imports < <(
    collect_import_files \
      '^\s*(import|from)\s+tet4d\.engine(\.|(\s|$))' \
      "$UI_DIR" \
      --glob '!src/tet4d/ui/tests/**'
  )
  UI_ENGINE_IMPORT_ALLOWLIST=$(cat <<'EOF'
src/tet4d/ui/pygame/control_helper.py
src/tet4d/ui/pygame/control_icons.py
src/tet4d/ui/pygame/front3d.py
src/tet4d/ui/pygame/front3d_setup.py
src/tet4d/ui/pygame/front4d.py
src/tet4d/ui/pygame/grid_mode_render.py
src/tet4d/ui/pygame/launcher_nd_runner.py
src/tet4d/ui/pygame/keybindings_menu.py
src/tet4d/ui/pygame/keybindings_menu_view.py
src/tet4d/ui/pygame/profile_4d.py
src/tet4d/ui/pygame/projection3d.py
src/tet4d/ui/pygame/text_render_cache.py
src/tet4d/ui/pygame/ui_utils.py
EOF
)
  unexpected_ui_engine_imports=()
  for f in "${ui_engine_imports[@]}"; do
    if ! grep -Fqx "$f" <<<"$UI_ENGINE_IMPORT_ALLOWLIST"; then
      unexpected_ui_engine_imports+=("$f")
    fi
  done
  if ((${#unexpected_ui_engine_imports[@]})); then
    print_unexpected_list \
      "Architecture violation: new ui adapter deep engine imports detected outside Stage 8 allowlist." \
      "${unexpected_ui_engine_imports[@]}"
    fail "Architecture violation: tet4d.ui imports deep engine internals outside baseline allowlist."
  fi
fi

# 5) Stability + benchmark tools should import engine via API only.
# profile_4d_render is a renderer benchmark and may use the UI adapter seam.
check_engine_api_only_imports "$TOOLS_STABILITY_DIR" "tools/stability"
check_engine_api_only_imports "$TOOLS_BENCHMARKS_DIR" "tools/benchmarks" '!tools/benchmarks/profile_4d_render.py'

# 6) Tools should not import deep UI internals directly; benchmark render profiler may use ui adapter package.
if [[ -d "$TOOLS_BENCHMARKS_DIR" ]]; then
  benchmark_ui_lines="$("${RG_BASE[@]}" \
    '^\s*(import|from)\s+tet4d\.ui(\.|(\s|$))' \
    "$TOOLS_BENCHMARKS_DIR" || true)"
  if [[ -n "$benchmark_ui_lines" ]]; then
    benchmark_ui_disallowed="$(printf '%s\n' "$benchmark_ui_lines" | grep -Ev \
      '^\s*tools/benchmarks/profile_4d_render\.py:[0-9]+:\s*(import|from)\s+tet4d\.ui\.pygame(\.|(\s|$))' \
      || true)"
    if [[ -n "$benchmark_ui_disallowed" ]]; then
      echo "Architecture violation: benchmark tools import unsupported UI modules." >&2
      printf '%s\n' "$benchmark_ui_disallowed" >&2
      fail "Architecture violation: tools/benchmarks may only use tet4d.ui.pygame for renderer profiling."
    fi
  fi
fi

exit 0
