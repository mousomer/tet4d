# Plan Report: Menu Rehaul v2 + Macbook No-Keypad Controls (2026-02-20)

Status: Executed (core IA + no-keypad defaults implemented)  
Related backlog items: `BKL-P1-005`, `BKL-P1-006`  
Related RDS files: `docs/rds/RDS_MENU_STRUCTURE.md`, `docs/rds/RDS_KEYBINDINGS.md`

## 1. Objective

1. Rework menu IA and flow to make navigation faster and easier for new and returning players.
2. Reduce menu density and overlap pressure in compact windows.
3. Remove numeric-keypad dependency from default `macbook` profile camera controls.

## 2. External Guidance Reviewed

1. Xbox Accessibility Guidelines (XAG) 112 and 114:
2. [https://learn.microsoft.com/en-us/gaming/accessibility/xbox-accessibility-guidelines/112](https://learn.microsoft.com/en-us/gaming/accessibility/xbox-accessibility-guidelines/112)
3. [https://learn.microsoft.com/en-us/gaming/accessibility/xbox-accessibility-guidelines/114](https://learn.microsoft.com/en-us/gaming/accessibility/xbox-accessibility-guidelines/114)
4. WCAG 2.2:
5. [https://www.w3.org/WAI/WCAG22/Understanding/focus-appearance](https://www.w3.org/WAI/WCAG22/Understanding/focus-appearance)
6. [https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
7. [https://www.w3.org/WAI/WCAG22/Understanding/consistent-help.html](https://www.w3.org/WAI/WCAG22/Understanding/consistent-help.html)
8. WAI-ARIA APG menu patterns:
9. [https://www.w3.org/WAI/ARIA/apg/patterns/menu-button/](https://www.w3.org/WAI/ARIA/apg/patterns/menu-button/)
10. [https://www.w3.org/WAI/ARIA/apg/patterns/menubar/](https://www.w3.org/WAI/ARIA/apg/patterns/menubar/)
11. Apple HIG menus:
12. [https://developer.apple.com/design/human-interface-guidelines/menus](https://developer.apple.com/design/human-interface-guidelines/menus)
13. Game Accessibility Guidelines (basic):
14. [https://gameaccessibilityguidelines.com/basic/](https://gameaccessibilityguidelines.com/basic/)
15. Nielsen usability heuristics:
16. [https://www.nngroup.com/articles/ten-usability-heuristics/](https://www.nngroup.com/articles/ten-usability-heuristics/)

## 3. Rules Extracted For This Project

1. Keep navigation consistent across launcher and pause (`Up/Down`, `Left/Right`, `Enter`, `Esc`) and avoid key-role drift.
2. Keep top-level choices short and recognizable; move detail into focused subviews instead of long mixed lists.
3. Keep help access in a predictable position in both launcher and gameplay.
4. Keep visible focus and contrast strong for all states and compact layouts.
5. Put high-frequency actions first, destructive actions last and visually separated.
6. Preserve settings state and profile choices by default; users should not reconfigure every launch.

## 4. Proposed Menu IA v2

### 4.1 Top-level

1. `Play`
2. `Continue` (only when resumable state exists)
3. `Settings`
4. `Controls`
5. `Help`
6. `Bot`
7. `Quit`

### 4.2 `Play` flow

1. Choose mode card: `2D`, `3D`, `4D`.
2. Open mode setup with only mode-relevant options.
3. Primary action pinned at bottom: `Start`.

### 4.3 `Settings` flow

1. Keep global categories only: `Audio`, `Display`, `Analytics`.
2. Keep explicit `Save`, `Reset defaults`, and `Back` at bottom.
3. Keep mode-specific setup fields out of global settings.

### 4.4 `Controls` flow

1. First-level scopes: `General`, `2D`, `3D`, `4D`.
2. Inside each scope, keep category groups: `Translation`, `Rotation`, `Camera/View`, `System`.
3. Keep profile operations local and visible: `Load`, `Save`, `Save As`, `Reset`, `Create`, `Rename`, `Delete`.

### 4.5 `Help` flow

1. Quick page first (what to do now).
2. Full reference pages second (all actions/settings).
3. Keep action->key lines live from active bindings at render time.

## 5. Macbook No-Keypad Camera Mapping (Proposed)

Goal: keep numeric-row camera ergonomics while removing keypad dependence.

Default `macbook` 4D camera proposal:
1. `view_xw_neg/view_xw_pos`: `1/2`
2. `view_zw_neg/view_zw_pos`: `3/4`
3. `yaw_neg/yaw_pos`: `5/6`
4. `pitch_neg/pitch_pos`: `7/8`
5. `zoom_out/zoom_in`: `9/0`
6. `yaw_fine_neg/yaw_fine_pos`: `-/=`
7. `cycle_projection`: `P`
8. `reset`: `Backspace`

Conflict notes:
1. Does not collide with default 4D gameplay rotation ladder (`Q/W A/S Z/X R/T F/G V/B`).
2. Does not collide with default system keys (`Esc`, `M`, `Y`, `C`, `Tab` for help).
3. Keeps all camera keys on the right/top area of the keyboard for discoverability.

## 6. Implementation Plan

### Phase R1: Data and contract update

1. Update keybinding defaults for `PROFILE_MACBOOK` in `tetris_nd/keybindings_defaults.py`.
2. Regenerate shipped macbook profile files under `keybindings/profiles/macbook/`.
3. Update keybinding tests in `tetris_nd/tests/test_keybindings.py`.
4. Update `docs/rds/RDS_KEYBINDINGS.md` and `docs/FEATURE_MAP.md`.

### Phase R2: Menu IA and labels

1. Update menu structure config in `config/menu/structure.json`.
2. Update validation contracts in `tetris_nd/menu_config.py`.
3. Update launcher/pause row mapping and labels in menu runtime modules.
4. Keep launcher/pause parity checks green (`tetris_nd/tests/test_menu_policy.py`).

### Phase R3: Layout and readability hardening

1. Rebalance menu zones and row density in shared menu layout/render paths.
2. Ensure status line is always visible and non-overlapping.
3. Keep helper visuals secondary and collapsible in compact windows.

### Phase R4: Help/control synchronization

1. Confirm `Help` uses live runtime bindings for key display in all scopes.
2. Verify `Controls` and `Help` present identical action names/grouping.
3. Add regression tests for compact-window clipping/overlap.

## 7. Acceptance Criteria

1. `macbook` defaults contain no keypad camera bindings.
2. Launcher and pause menus use the same IA categories and naming.
3. Top-level menu is scannable and remains within row-count/depth limits.
4. No overlap regressions in normal and compact windows.
5. `ruff check .`, `pytest -q`, and `./scripts/ci_check.sh` pass.

## 8. Execution Update (2026-02-20)

1. `BKL-P1-005` implemented:
2. updated `tetris_nd/keybindings_defaults.py` (`DEFAULT_CAMERA_KEYS_4D_MACBOOK`) to no-keypad advanced camera keys.
3. updated shipped profile `keybindings/profiles/macbook/4d.json`.
4. updated keybinding regression expectations in `tetris_nd/tests/test_keybindings.py`.
5. `BKL-P1-006` core IA implemented:
6. launcher menu config updated in `config/menu/structure.json` to:
7. `Play`,`Continue`,`Settings`,`Controls`,`Help`,`Bot`,`Quit`.
8. launcher runtime updated in `front.py`:
9. `Play` opens 2D/3D/4D mode picker,
10. `Continue` launches last used mode.
11. pause menu config simplified in `config/menu/structure.json`.
12. pause runtime value labels and controls entry updated in `tetris_nd/pause_menu.py`.
13. controls entry now starts in `General` scope in launcher and pause keybindings entry points.
