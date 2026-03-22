# Topology Explorer Menu Audit

Status date: 2026-03-12
Status source of truth: [`docs/plans/topology_playground_current_authority.md`](docs/plans/topology_playground_current_authority.md)
Historical migration audit: [`docs/history/topology_playground/topology_playground_reality_audit.md`](../history/topology_playground/topology_playground_reality_audit.md)
Historical intent only: [`docs/history/topology_playground/topology_playground_migration.md`](../history/topology_playground/topology_playground_migration.md)

## Goal

Inventory the currently visible Topology Explorer / Playground controls and
classify what each one really is today:

- working
- partial
- legacy-only
- dead-or-misleading
- duplicated-by-other-control

This audit is intentionally about the live shell as the user sees it now. It is
not a rewrite plan and it does not reopen already completed migration stages.

## Scope

Inspected current live UI owners and routing:

- `src/tet4d/ui/pygame/launch/topology_lab_menu.py`
- `src/tet4d/ui/pygame/launch/topology_lab_state_factory.py`
- `src/tet4d/ui/pygame/topology_lab/controls_panel.py`
- `src/tet4d/ui/pygame/topology_lab/scene_state.py`
- `src/tet4d/ui/pygame/topology_lab/legacy_panel_support.py`
- `src/tet4d/ui/pygame/topology_lab/boundary_picker.py`
- `src/tet4d/ui/pygame/topology_lab/explorer_tools.py`
- `src/tet4d/ui/pygame/topology_lab/transform_editor.py`
- `src/tet4d/ui/pygame/topology_lab/preview.py`
- `tests/unit/engine/test_topology_lab_menu.py`
- `tests/unit/engine/test_topology_lab_experiments.py`

State-source legend used below:

- `canonical`: engine/runtime-owned `TopologyPlaygroundState`
- `shell-local`: `_TopologyLabState` only
- `legacy`: old `state.profile` / legacy export path
- `mixed`: canonical behavior with shell-local hover/focus/pending helpers

## A. Current Visible Controls Inventory

### Explorer-mode shell

| Visible control | Where it appears | Category | Owner | Handler path | Actual behavior | Classification | State source | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `Game Type` (`Normal Game` / `Explorer Mode`) | Analysis View left menu | mode + legacy compatibility | `controls_panel.py` | `_adjust_row -> _cycle_gameplay_mode -> _sync_profile/_sync_explorer_state` | Switches the entire shell between the canonical explorer/editor path and the retained legacy profile rows. | `partial` | mixed | Works, but one branch is the live explorer shell while the other is a compatibility surface. The label does not explain that distinction. |
| `Dimension` | Analysis View left menu | topology editing | `controls_panel.py` | `_adjust_row -> _cycle_dimension` | Cycles 2D/3D/4D, reloads profiles, rebuilds explorer settings for explorer mode, refreshes canonical scene state. | `working` | mixed | Explorer mode updates canonical state; Normal Game reloads legacy profile state. |
| `Board X` / `Board Y` / `Board Z` / `Board W` | Analysis View left menu in `Explorer Mode` | topology editing | `controls_panel.py` | `_adjust_row -> _set_explorer_board_dim -> replace_play_settings` | Adjusts board dimensions and refreshes the explorer preview. | `working` | canonical | `Board Z` and `Board W` appear only in 3D/4D. |
| `Piece Set` | Analysis View left menu in `Explorer Mode` | topology editing | `controls_panel.py` | `_adjust_row -> _set_explorer_piece_set_index -> replace_play_settings` | Cycles the launch piece set used by play preview from the current playground draft. | `working` | canonical | Affects launch settings, not seam structure. |
| `Speed` | Analysis View left menu in `Explorer Mode` | topology editing | `controls_panel.py` | `_adjust_row -> _set_explorer_speed_level -> replace_play_settings` | Cycles the play-preview speed level. | `working` | canonical | Affects launch settings, not topology preview compilation. |
| `Explorer Preset` | Analysis View left menu in `Explorer Mode` | topology editing | `controls_panel.py` | `_adjust_row -> _cycle_explorer_preset -> replace_explorer_profile/replace_explorer_draft` | Replaces the live explorer topology profile with another preset and resets the draft slot/selection. | `working` | canonical | Duplicated elsewhere by transform-editor preset arrows. |
| `Selected Boundary` | Analysis View left menu in `Explorer Mode` | tool context | `controls_panel.py` | `_row_value_text -> _analysis_boundary_value_text -> current_selected_boundary_index` | Read-only display of the currently selected boundary. | `working` | canonical | Selecting the row only changes row focus; it does not edit anything. |
| `Selected Seam` | Analysis View left menu in `Explorer Mode` | tool context | `controls_panel.py` | `_row_value_text -> current_selected_glue_id` | Read-only display of the selected seam id. | `working` | canonical | Same selectable-row styling as editable rows, but no adjustment path. |
| `Draft Transform` | Analysis View left menu in `Explorer Mode` | tool context | `controls_panel.py` | `_row_value_text -> _explorer_transform_label` | Read-only textual summary of the current draft transform. | `working` | canonical | Same selectable-row styling as editable rows, but no adjustment path. |
| `Save Profile` | Analysis View left menu in `Explorer Mode` | topology editing | `controls_panel.py` | `_handle_enter_key -> _save_profile -> save_explorer_topology_profile` | Saves the current explorer topology profile. | `working` | canonical | Duplicated by the workspace action bar `Save` button. |
| `Export Explorer Preview` | Analysis View left menu in `Explorer Mode` | topology editing | `controls_panel.py` | `_handle_enter_key -> _run_export -> export_explorer_topology_preview` | Exports the current explorer preview payload. | `working` | canonical | Duplicated by the workspace action bar `Export` button. |
| `Build Experiment Pack` | Analysis View left menu in `Explorer Mode` | diagnostics | `controls_panel.py` | `_handle_enter_key -> _run_experiments` | Compiles/exports an experiment pack for the current draft and shows a recommendation in-shell. | `working` | canonical | Duplicated by the workspace action bar `Experiments` button. |
| `Back` | Analysis View left menu in `Explorer Mode` | topology editing | `controls_panel.py` | `_handle_enter_key -> state.running = False` | Exits the shell. | `working` | shell-local | Duplicated by the workspace action bar `Back` button. |
| `Navigate` | Tool ribbon in Explorer Editor | tool | `explorer_tools.py` + `scene_state.py` | `draw_tool_ribbon -> set_active_tool(TOOL_NAVIGATE)` | Enters camera/navigation mode. Boundary clicks do not author seams. | `working` | canonical | Camera mouse/key controls only work from this tool. |
| `Inspect` | Tool ribbon in Explorer Editor | tool | `explorer_tools.py` + `boundary_picker.py` | `set_active_tool(TOOL_INSPECT)` + `apply_boundary_pick` | Selects boundaries for inspection without starting seam creation. | `working` | canonical | Right-click still jumps into create/edit seam flow. |
| `Create` | Tool ribbon in Explorer Editor | tool | `explorer_tools.py` + `boundary_picker.py` | `set_active_tool(TOOL_CREATE)` + `_handle_create_pick` | First boundary click stores a pending source; second click chooses target and switches to `Edit`. | `working` | mixed | Uses shell-local `pending_source_index` while building a canonical draft pair. |
| `Edit` | Tool ribbon in Explorer Editor | tool | `explorer_tools.py` + `boundary_picker.py` | `set_active_tool(TOOL_EDIT)` + `_handle_edit_pick` | Selects an existing seam if one exists on the chosen boundary; otherwise reports no active gluing. | `working` | canonical | Current draft/permutation/signs stay editable in the transform editor. |
| `Probe` | Tool ribbon in Explorer Editor | tool | `explorer_tools.py` + `controls_panel.py` | `set_active_tool(TOOL_PROBE)` + `_apply_probe_step/_reset_probe` | Enables probe movement controls, probe reset action, and probe path/highlight updates. | `working` | canonical with shell-local unavailable fallback | Probe-unavailable errors are still mirrored locally. |
| `Sandbox` | Tool ribbon in Explorer Editor | tool | `explorer_tools.py` + `piece_sandbox.py` | `set_active_tool(TOOL_SANDBOX)` + sandbox action handlers | Enables sandbox piece controls, movement, rotation, trace toggles, and play-preview prep. | `working` | canonical | Activates sandbox state and preview-panel movement buttons. |
| `Play This Topology` | Tool ribbon in Explorer Editor | tool | `explorer_tools.py` + `controls_panel.py` | `set_active_tool(TOOL_PLAY)` | Only changes the active tool; actual play launch still requires `Enter`, `F5`, or the `Play This Topology` action button. | `partial` | canonical | Label reads like an immediate command, but it is only a mode toggle with no unique play-only panel. |
| Boundary picks | Explorer scene canvas | topology editing | `boundary_picker.py` | `_handle_mouse_boundary_target -> apply_boundary_pick/apply_boundary_edit_pick` | Left click behavior depends on active tool; right click from non-edit tools jumps directly into create/edit seam flow. | `working` | mixed | Selection/draft changes are canonical; hover and pending source are shell-local. |
| Seam picks | Explorer scene canvas | topology editing | `boundary_picker.py` | `_dispatch_mouse_target -> apply_glue_pick` | Clicking an existing seam selects it, highlights it, loads its slot into the draft, and switches to `Edit`. | `working` | canonical | Existing seam picks are only present when scene arrows/hit targets exist. |
| Preset `<` / `>` arrows | Transform editor | topology editing | `topology_lab_menu.py` + `controls_panel.py` | `_handle_mouse_editor_target -> _cycle_explorer_preset` | Cycles explorer presets from the right-hand editor. | `duplicated-by-other-control` | canonical | Same concept already exists as the `Explorer Preset` row in Analysis View. |
| Current preset pill | Transform editor | topology editing | `transform_editor.py` | none | Drawn like an active button, but it has no hit target and no action handler. | `dead-or-misleading` | none | Pure display, styled as clickable UI. |
| Glue slot buttons (`glue_*` / `new`) | Transform editor | topology editing | `controls_panel.py` | `_handle_mouse_editor_target -> _select_explorer_draft_slot` | Chooses an existing seam slot or the `new` slot and syncs draft/selection/highlight. | `working` | canonical | This is the live slot-selection control now that row-based seam editing was removed. |
| Permutation buttons | Transform editor | topology editing | `controls_panel.py` | `_handle_mouse_editor_target -> _update_explorer_draft` | Selects the tangent-axis permutation used for the current draft seam. | `working` | canonical | Direct transform-editing control. |
| Tangent sign toggle buttons | Transform editor | topology editing | `controls_panel.py` | `_handle_mouse_editor_target -> _toggle_explorer_sign` | Flips the sign of each tangent axis in the current draft transform. | `working` | canonical | Direct transform-editing control. |
| `Apply` | Workspace action bar | topology editing | `topology_lab_menu.py` + `controls_panel.py` | `_activate_action -> _apply_explorer_glue` | Validates and writes the current draft seam into the explorer profile. | `working` | canonical | This is the live seam commit control on the migrated path. |
| `Remove` | Workspace action bar | topology editing | `topology_lab_menu.py` + `controls_panel.py` | `_activate_action -> _remove_explorer_glue` | Deletes the selected seam slot from the explorer profile. | `working` | canonical | No duplicate row-based remove control remains in explorer mode. |
| `Play This Topology` | Workspace action bar | topology editing | `topology_lab_menu.py` + `controls_panel.py` | `_activate_action('play_preview') -> state.play_preview_requested -> _launch_play_preview` | Launches play directly from the current canonical playground state. | `working` | canonical | This is the clearest live play-launch control. |
| `Save` / `Export` / `Experiments` / `Back` | Workspace action bar | topology editing + diagnostics | `topology_lab_menu.py` + `controls_panel.py` | `_activate_action -> _save_profile/_run_export/_run_experiments/state.running=False` | Duplicates the same save/export/experiments/back commands already exposed as Analysis View rows. | `duplicated-by-other-control` | mixed | The action bar versions work, but they duplicate secondary-pane commands instead of defining one canonical command surface. |
| `Reset Probe` | Workspace action bar in `Probe` tool | tool | `topology_lab_menu.py` + `controls_panel.py` | `_activate_action('probe_reset') -> _reset_probe` | Resets the probe to the recommended starting coordinate for the current draft. | `working` | canonical with shell-local unavailable fallback | Only visible in `Probe`. |
| `Spawn` / `Prev Piece` / `Next Piece` / `Rotate` / `Show/Hide Trace` / `Reset` | Workspace action bar in `Sandbox` tool | tool | `topology_lab_menu.py` + `piece_sandbox.py` | `_handle_sandbox_action` | Operates the sandbox piece and its trace visibility. | `working` | canonical | Only visible in `Sandbox`. |
| Probe/Sandbox step buttons (`x-/x+/y-/y+/...`) | Preview panel footer in `Probe` or `Sandbox` | tool | `preview.py` + `topology_lab_menu.py` + `controls_panel.py` | `_draw_probe_controls_if_needed -> draw_probe_controls -> _handle_mouse_action_target` | In `Probe`, advances the probe. In `Sandbox`, the same visible buttons move the sandbox piece instead. | `working` | canonical with shell-local unavailable fallback | Functional, but overloaded: the same control surface changes meaning by active tool. |

### Legacy rows still exposed by switching `Game Type` to `Normal Game`

| Visible control | Where it appears | Category | Owner | Handler path | Actual behavior | Classification | State source | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `Preset` | Left menu after `Game Type = Normal Game` | legacy compatibility | `legacy_panel_support.py` | `_adjust_row -> _apply_legacy_row_adjustment -> adjust_legacy_row('preset')` | Cycles legacy topology designer presets. | `legacy-only` | legacy | Not part of canonical explorer draft editing. |
| `Topology Mode` | Left menu after `Game Type = Normal Game` | legacy compatibility | `legacy_panel_support.py` | `_adjust_row -> _apply_legacy_row_adjustment -> adjust_legacy_row('topology_mode')` | Cycles legacy topology mode and rebuilds edge rules. | `legacy-only` | legacy | This is the old profile editor surface, not the explorer seam editor. |
| `X-` / `X+` / `Z-` / `Z+` / `W-` / `W+` | Left menu after `Game Type = Normal Game` | legacy compatibility | `legacy_panel_support.py` | `_adjust_row -> _apply_legacy_row_adjustment -> adjust_legacy_row(axis edge)` | Cycles per-edge legacy edge rules. | `legacy-only` | legacy | Visible axes depend on dimension. |
| `Y-` / `Y+` (`locked`) | Left menu after `Game Type = Normal Game` | legacy compatibility | `legacy_panel_support.py` | same as other legacy edge rows, but `disabled=True` | Drawn as locked rows and rejects edits in Normal Game. | `legacy-only` | legacy | Especially misleading because they look like ordinary topology controls inside the same shell. |
| `Save Profile` | Left menu after `Game Type = Normal Game` | legacy compatibility | `controls_panel.py` | `_handle_enter_key -> _save_profile -> save_topology_profile` | Saves the legacy topology profile. | `legacy-only` | legacy | Different payload from explorer save. |
| `Export Resolved Profile` | Left menu after `Game Type = Normal Game` | legacy compatibility | `controls_panel.py` + `legacy_panel_support.py` | `_handle_enter_key -> _run_export -> export_legacy_profile` | Exports the resolved legacy profile. | `legacy-only` | legacy | Different output and naming from `Export Explorer Preview`. |
| `Back` | Left menu after `Game Type = Normal Game` | legacy compatibility | `controls_panel.py` | `_handle_enter_key -> state.running = False` | Exits the shell. | `legacy-only` | shell-local | Same shell exit, but still part of the legacy-only menu set. |

Controls not found as visible items in the current shell:

- no visible import control
- no visible dedicated transport-policy control (`rigid`, `cellwise`,
  `center-preserving`, etc.)

Transport behavior does exist in runtime/gameplay code, but there is no current
menu/control surface that exposes it directly in the Explorer Playground UI.

## B. Duplications and Ambiguities

### 1. Mode vs tool vs compatibility are visually mixed

- `Game Type` looks like a normal editing-mode chooser, but it actually toggles
  between the live canonical explorer shell and a retained legacy profile
  editor.
- The shell also exposes tool modes (`Navigate`, `Inspect`, `Create`, `Edit`,
  `Probe`, `Sandbox`, `Play This Topology`) and pane focus (`Analysis View`,
  `Explorer Editor`), so the user is asked to reason about three different
  "mode" concepts at once.
- Result: `Normal Game` inside the same shell looks like a current editor mode,
  not a compatibility branch.

### 2. The same command is exposed in more than one place

- `Save`, `Export`, `Experiments`, and `Back` exist both as Analysis View rows
  and as workspace action buttons.
- `Explorer Preset` exists both as an Analysis View row and as transform-editor
  preset arrows.
- `Play This Topology` exists as:
  - a tool-ribbon button,
  - a workspace action button,
  - keyboard launch (`Enter` in `Play` tool and `F5`).

Result: it is hard to tell which surface is the real one and which is only
there for convenience or compatibility.

### 3. Different concepts are combined in one visual block

- The transform editor mixes real transform-editing controls (slot selection,
  permutation, tangent flips) with explorer-preset switching, even though preset
  selection is not itself a transform-editing concept.
- The preview-panel step grid is reused for two different meanings:
  - probe traversal in `Probe`
  - sandbox piece movement in `Sandbox`

Result: right-side controls look denser and more "complete" than they really
are, but the conceptual boundaries are weak.

### 4. Legacy-only controls still look first-class

- The legacy `Preset`, `Topology Mode`, and edge-rule rows use the same visual
  row styling as live explorer controls.
- `Export Resolved Profile` appears in the same shell as `Export Explorer
  Preview`, but exports a different artifact from a different state owner.
- The locked `Y-` / `Y+` rows especially read like half-implemented current
  controls instead of intentionally retained legacy behavior.

### 5. Read-only rows are styled like editable menu rows

- `Selected Boundary`
- `Selected Seam`
- `Draft Transform`

These rows do show real state, but they share the same row-selection behavior
as editable menu items, so they read like latent controls rather than status
readouts.

## C. Dead / Partial / Misleading Controls

- `Game Type`: partial. It works, but it silently swaps between the canonical
  explorer surface and a retained legacy-only editor.
- Tool-ribbon `Play This Topology`: partial. It does not launch play directly;
  it only arms the later play request path.
- Transform-editor current preset pill: dead-or-misleading. It is drawn like a
  clickable button and has no handler.
- Probe/Sandbox step grid: working but semantically overloaded. The same visible
  control surface means two different things depending on tool.
- Read-only analysis rows (`Selected Boundary`, `Selected Seam`, `Draft
  Transform`): working as status displays, but visually mixed with editable menu
  rows.
- Legacy `Y-` / `Y+` rows: legacy-only and locked. They are especially likely
  to be read as half-wired current controls.

## D. Recommended Next Cleanup Actions

### Finish

- Decide whether `Play This Topology` is a tool or an action. If it remains a
  tool, give it unique behavior beyond "press Enter/F5 now".
- Make read-only analysis state rows visually read-only instead of ordinary menu
  rows.
- Give the preview-panel movement grid explicit per-tool labeling so probe and
  sandbox semantics are not visually collapsed together.

### Hide

- Hide the legacy `Normal Game` row set behind an explicit compatibility affordance
  instead of presenting it as a peer of `Explorer Mode`.
- Hide duplicate action-bar commands once one canonical command surface is
  chosen.

### Remove

- Remove the decorative transform-editor preset pill hit affordance, or stop
  styling it like a button.
- Remove one of the two explorer-preset entry points after choosing the
  canonical owner.

### Merge

- Merge `Save` / `Export` / `Experiments` / `Back` into one command surface.
- Merge play launch into one affordance.
- Keep transform editing in the right-side editor, but keep preset/settings
  changes in one clearly separate surface.

### Relabel

- Relabel `Game Type` so the legacy branch is clearly a compatibility surface,
  not a current editor mode.
- Relabel or remove the `Play This Topology` tool-ribbon button.
- Relabel action-bar `Export` to match the actual artifact (`Export Explorer
  Preview`).
- Label the preview footer by tool (`Probe moves` vs `Sandbox moves`) instead of
  using one unlabeled step grid.

## E. Minimal Future Stage Breakdown

1. Remove the most misleading duplicate affordances.
   - Preset pill, duplicated preset controls, duplicated command buttons.
2. Isolate the legacy compatibility surface from the primary explorer shell.
   - `Game Type` / `Normal Game` should stop reading like a first-class modern
     editing mode.
3. Clarify command-vs-tool responsibilities.
   - Especially `Play This Topology`, save/export placement, and the probe vs
     sandbox movement grid.
4. Cleanly separate editable settings from read-only analysis context.
   - Keep Analysis View secondary without making it look half-editable.

## Short Conclusion

The current Explorer Playground does have one real canonical editor path, but
the visible menus still mix that path with:

- duplicated commands,
- read-only rows dressed like controls,
- a legacy compatibility branch presented as a peer mode,
- and one dead preset-pill affordance in the transform editor.

The next cleanup stage should remove ambiguity before adding more functionality.
