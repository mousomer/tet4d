#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "$0")/.."

if [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
else
  echo "No Python runtime found." >&2
  exit 1
fi

"$PYTHON_BIN" -m ruff check \
  src/tet4d/engine/runtime/keybinding_runtime_state.py \
  src/tet4d/engine/runtime/keybinding_store.py \
  src/tet4d/engine/ui_logic/keybindings_catalog.py \
  src/tet4d/ui/pygame/keybindings.py \
  tests/unit/engine/test_keybindings.py \
  tests/unit/engine/test_keybindings_menu_model.py \
  tests/unit/engine/test_menu_navigation_keys.py \
  tests/unit/engine/test_tutorial_overlay.py \
  tests/unit/engine/test_tutorial_overlay_layout.py \
  tools/governance/validate_project_contracts.py

PYTHONPATH=src "$PYTHON_BIN" -m pytest -q \
  tests/unit/engine/test_keybindings.py \
  tests/unit/engine/test_keybindings_menu_model.py \
  tests/unit/engine/test_menu_navigation_keys.py \
  tests/unit/engine/test_help_topics.py \
  tests/unit/engine/test_tutorial_overlay.py \
  tests/unit/engine/test_tutorial_overlay_layout.py \
  tests/unit/engine/test_tutorial_content.py

"$PYTHON_BIN" tools/governance/validate_project_contracts.py

echo "check_keybinding_contract: OK"
