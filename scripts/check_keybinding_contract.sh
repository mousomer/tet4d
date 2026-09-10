#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON_BIN="$(./scripts/resolve_python_env.sh)"

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
