# Plan: 4D Basis-Rollout Regression Fixes

Date: 2026-02-19  
Status: Completed

## Scope

User-reported regressions after 4D basis decomposition:

1. Exploration-mode rotations appear broken.
2. `w` movement behaves incorrectly under 4D basis view changes.
3. Need `macbook` key profile without function-key dependency.
4. Compact profile should stop using `,/.` for `w` movement.
5. `w` movement must remain "between-layer-boards" intent under viewer-relative movement model.
6. Stale extra layer panel can remain after reducing displayed layer count.

## Approach

1. Keep gameplay simulation unchanged; patch render/input mapping only.
2. Add explicit 4D movement-axis override path so `move_w_neg/move_w_pos` map to basis layer axis.
3. Remove render quantization that truncates fractional rotation tween cells.
4. Add explicit layer-region clearing hardening in 4D frame draw path.
5. Extend keybinding profile system with `macbook` profile and non-function defaults for 4D view controls.
6. Update compact (`small`) 4D `w` movement defaults to `N` / `/`.

## Validation

1. Add/adjust unit tests in:
- `tetris_nd/tests/test_front4d_render.py`
- `tetris_nd/tests/test_nd_routing.py`
- `tetris_nd/tests/test_keybindings.py`
2. Run:
- `ruff check`
- focused pytest suites
- full `pytest -q`
- `./scripts/ci_check.sh`

## Completion Notes

1. Implemented in:
- `tetris_nd/frontend_nd.py`
- `tetris_nd/front4d_game.py`
- `tetris_nd/front4d_render.py`
- `tetris_nd/keybindings_defaults.py`
- `tetris_nd/keybindings.py`
2. Keybinding profile assets updated:
- `keybindings/4d.json`
- `keybindings/profiles/small/4d.json`
- `keybindings/profiles/macbook/2d.json`
- `keybindings/profiles/macbook/3d.json`
- `keybindings/profiles/macbook/4d.json`
3. Regression tests added/updated:
- `tetris_nd/tests/test_front4d_render.py`
- `tetris_nd/tests/test_nd_routing.py`
- `tetris_nd/tests/test_keybindings.py`
