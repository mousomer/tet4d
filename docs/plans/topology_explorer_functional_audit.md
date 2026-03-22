# Topology Explorer Functional Audit

Status date: 2026-03-12
Status source of truth: [`docs/plans/topology_playground_current_authority.md`](docs/plans/topology_playground_current_authority.md)
Historical migration audit: `docs/history/topology_playground/topology_playground_reality_audit.md`
UI-state source of truth:
- [`docs/plans/topology_explorer_menu_audit.md`](docs/plans/topology_explorer_menu_audit.md)
- [`docs/plans/topology_explorer_menu_cleanup_pass1.md`](docs/plans/topology_explorer_menu_cleanup_pass1.md)

## Scope

This stage is diagnostic only. It does not reopen completed migration work, and it does not attempt a broader UI redesign or topology-engine refactor.

Audited modules:

- `src/tet4d/ui/pygame/topology_lab/controls_panel.py`
- `src/tet4d/ui/pygame/launch/topology_lab_menu.py`
- `src/tet4d/ui/pygame/topology_lab/scene_state.py`
- `src/tet4d/ui/pygame/topology_lab/preview.py`
- `src/tet4d/ui/pygame/topology_lab/explorer_tools.py`
- `src/tet4d/ui/pygame/topology_lab/transform_editor.py`
- `src/tet4d/ui/pygame/topology_lab/boundary_picker.py`
- `src/tet4d/ui/pygame/topology_lab/legacy_panel_support.py`
- `src/tet4d/ui/pygame/topology_lab/piece_sandbox.py`
- `src/tet4d/engine/runtime/topology_explorer_preview.py`
- `src/tet4d/engine/runtime/topology_explorer_runtime.py`
- `src/tet4d/engine/runtime/topology_explorer_experiments.py`
- `src/tet4d/engine/runtime/topology_playground_launch.py`
- `src/tet4d/ui/pygame/topology_lab/play_launch.py`

## Instrumentation / Measurement Basis

Lightweight interaction-timing hooks were added in:

- `src/tet4d/engine/runtime/topology_explorer_audit.py`
- `src/tet4d/ui/pygame/topology_lab/controls_panel.py`
- `src/tet4d/ui/pygame/topology_lab/piece_sandbox.py`
- `src/tet4d/engine/runtime/topology_explorer_preview.py`

Measured phases now include:

- handler start / end
- preview compile start / end
- canonical sync
- scene refresh
- experiment compile / export
- play launch handoff

Measurement setup for the latency numbers below:

- fresh temporary state root under `state/audit_measure/`
- default explorer board sizes from `build_explorer_playground_settings(...)`
- default explorer preset family (`Empty` on the fresh state root)
- 4D numbers are used for the hotspot table because that is the dominant slow path

Observed startup baseline:

- 2D startup: `10.4 ms` total, including `7.6 ms` preview compile
- 3D startup: `38.5 ms` total, including `35.6 ms` preview compile
- 4D startup: `375.4 ms` total, including `369.8 ms` preview compile

No dead controls remain on the migrated explorer path after cleanup pass 1. Remaining problem areas are now degraded or legacy-backed rather than unbound.

## A. Current Functional State Of Controls

### Analysis View / Shell Controls

| control | classification | owner / main handler | canonical state? | preview compile? | topology recompute? | latency | notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `Workspace Path` | `legacy-backed` | `controls_panel.py` / `_cycle_gameplay_mode(...)` | `mixed` | `yes` when routing back into explorer sync | `yes` | not separately timed | Still switches between the canonical explorer shell and the retained legacy compatibility surface. |
| `Dimension` | `working-but-slow` | `controls_panel.py` / `_cycle_dimension(...)` | `mixed -> canonical` | `yes` | `yes` | `376.2 ms` for `3D -> 4D` | One real 4D preview rebuild happens in `_sync_explorer_state(...)`, then `_mark_updated(...)` performs a second cached refresh. |
| `Board X / Board Y / Board Z / Board W` | `working-but-slow` | `controls_panel.py` / `_set_explorer_board_dim(...)` | `canonical` | `yes` | `yes` | `427.1 ms` for `Board X +1` in 4D | Full movement-graph preview rebuild on every board-size edit. |
| `Piece Set` | `working` | `controls_panel.py` / `_set_explorer_piece_set_index(...)` | `canonical` | `no` (cache hit, no preview compile span) | `no` | `0.026 ms` 4D scene refresh | Launch-only setting; it still routes through canonical sync/scene refresh but does not rebuild topology preview. |
| `Speed` | `working` | `controls_panel.py` / `_set_explorer_speed_level(...)` | `canonical` | `no` (cache hit, no preview compile span) | `no` | `0.024 ms` 4D scene refresh | Same as `Piece Set`: launch-only, not topology-affecting. |
| `Explorer Preset` | `working-but-degraded` | `controls_panel.py` / `_cycle_explorer_preset(...)` | `canonical` | `yes` | `yes` | `696.9 ms` in 4D | Valid preset switches are slow because they synchronously rebuild the 4D preview. Unsafe preset families can also leave `scene_preview_error` set when the active board dims do not satisfy bijection rules. |
| `Selected Boundary` | `working` | `controls_panel.py` / `_analysis_boundary_value_text(...)` | `canonical` | `no` | `no` | n/a | Display-only context row after cleanup pass 1. |
| `Selected Seam` | `working` | `controls_panel.py` / `current_selected_glue_id(...)` | `canonical` | `no` | `no` | n/a | Display-only context row. |
| `Draft Transform` | `working` | `controls_panel.py` / `_explorer_transform_label(...)` | `canonical` | `no` | `no` | n/a | Display-only context row. |
| `Save Profile` | `working` | `controls_panel.py` / `_save_profile(...)` | `canonical` on explorer path | `no` | `no` | not separately timed | Straight profile save; not part of the slow interaction set. |
| `Export Explorer Preview` | `working-but-slow` | `controls_panel.py` / `_run_export(...)` | `canonical` | `yes` | `no state mutation` | `402.8 ms` in 4D | Export recompiles the preview in `export_explorer_topology_preview(...)` instead of reusing `state.scene_preview`. |
| `Build Experiment Pack` | `working-but-slow` | `controls_panel.py` / `_run_experiments(...)` | `canonical` | `yes`, repeated | `yes` | `10.31 s` in 4D | The pack is compiled once for the in-shell recommendation and then compiled again during export. Default 4D pack = `7` candidates compiled `2x` = `14` preview compiles. |
| `Back` | `working` | `controls_panel.py` / `state.running = False` | `shell-local` | `no` | `no` | n/a | Simple shell exit. |

### Explorer Editor / Transform Editor / Scene Actions

| control | classification | owner / main handler | canonical state? | preview compile? | topology recompute? | latency | notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `Navigate` | `working` | `explorer_tools.py` / `set_active_tool(TOOL_NAVIGATE)` | `canonical` | `no` | `no` | n/a | Camera/navigation mode only. |
| `Inspect` | `working` | `explorer_tools.py` + `boundary_picker.py` / `apply_boundary_pick(...)` | `canonical` | `no` | `no` | immediate | Boundary inspection only. |
| `Create` | `working-but-degraded` | `boundary_picker.py` / `_handle_create_pick(...)` | `mixed` | `no` until `Apply` | `no` until `Apply` | immediate | Still depends on shell-local `pending_source_index` while the draft itself lives in canonical state. |
| `Edit` | `working` | `boundary_picker.py` / `_handle_edit_pick(...)` | `canonical` | `no` until `Apply` | `no` until `Apply` | immediate | Seam selection and draft targeting work on the canonical path. |
| `Probe` | `working-but-degraded` | `scene_state.py` + `controls_panel.py` / `set_active_tool(...)`, `_apply_probe_step(...)` | `canonical` with local fallback | `no` | `no` | `0.345 ms` 4D step | Normal probe movement is canonical. When preview compilation fails, `scene_state.py` still falls back to shell-local `Probe unavailable:` snapshots. |
| `Sandbox` | `working` | `scene_state.py` + `piece_sandbox.py` / `set_active_tool(...)` | `canonical` | `no` | `no` | `0.273 ms` 4D step | Uses runtime-owned sandbox state. |
| `Play Mode` | `partial` | `explorer_tools.py` / `set_active_tool(TOOL_PLAY)` | `canonical` | `no` | `no` | n/a | Still only arms the later play-launch path. It is not a direct launch action. |
| Boundary picks | `working` | `boundary_picker.py` / `apply_boundary_pick(...)`, `apply_boundary_edit_pick(...)` | `mixed` | `no` until `Apply` | `no` until `Apply` | immediate | Left click follows the active tool; right click still jumps into create/edit seam flow. |
| Seam picks | `working` | `boundary_picker.py` / `apply_glue_pick(...)` | `canonical` | `no` until `Apply` | `no` until `Apply` | immediate | Loads the selected seam into the current draft slot and switches to `Edit`. |
| Transform-editor preset display | `working` | `transform_editor.py` / `draw_transform_editor(...)` | `canonical` | `no` | `no` | n/a | Now explicitly read-only. It is no longer a dead clickable pill. |
| Glue slot buttons | `working` | `controls_panel.py` / `_select_explorer_draft_slot(...)` | `canonical` | `no` until `Apply` | `no` until `Apply` | immediate | Live slot-selection control for seam editing. |
| Permutation buttons | `working` | `controls_panel.py` / `update_explorer_draft(...)` | `canonical` | `no` until `Apply` | `no` until `Apply` | immediate | Draft-only transform edit. |
| Tangent sign toggles | `working` | `controls_panel.py` / `_toggle_explorer_sign(...)` | `canonical` | `no` until `Apply` | `no` until `Apply` | immediate | Draft-only transform edit. |
| `Apply` | `working-but-slow` | `controls_panel.py` / `_apply_explorer_glue(...)` | `canonical` | `yes` | `yes` | `682.7 ms` create / `718.0 ms` edit in 4D | Nearly all visible latency is the synchronous 4D preview compile after the profile mutation. |
| `Remove` | `working-but-slow` | `controls_panel.py` / `_remove_explorer_glue(...)` | `canonical` | `yes` | `yes` | `420.1 ms` in 4D | Same preview rebuild path as `Apply`, but on the zero-glue result. |
| `Play This Topology` (action bar) | `working` | `topology_lab_menu.py` + `controls_panel.py` / `_launch_play_preview(...)` | `canonical` | `no` in shell path | `no` in shell path | `0.048 ms` shell handoff in 4D | Explorer-side launch handoff is not a hotspot. Any larger wait after click is downstream gameplay startup, not explorer interaction code. |

### Probe / Sandbox Tool-Specific Controls

| control | classification | owner / main handler | canonical state? | preview compile? | topology recompute? | latency | notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `Reset Probe` | `working` | `controls_panel.py` / `_reset_probe(...)` | `canonical` with local fallback | `no` | `no` | not separately timed | Fast state reset. |
| Probe move grid (`x-/x+/y-/y+/z-/z+/w-/w+`) | `working` | `topology_lab_menu.py` / `_handle_mouse_action_target(...) -> _apply_probe_step(...)` | `canonical` with local fallback | `no` | `no` | `0.345 ms` 4D step | Explicitly labeled `Probe moves` after cleanup pass 1. |
| Sandbox move grid (`x-/x+/y-/y+/z-/z+/w-/w+`) | `working` | `topology_lab_menu.py` / `_handle_mouse_action_target(...) -> piece_sandbox.move_sandbox_piece(...)` | `canonical` | `no` | `no` | `0.273 ms` 4D step | Explicitly labeled `Sandbox piece moves` after cleanup pass 1. |
| `Spawn` | `working` | `topology_lab_menu.py` / `_handle_sandbox_action('sandbox_spawn')` | `canonical` | `no` | `no` | not separately timed | Sandbox-only state update. |
| `Prev Piece` / `Next Piece` | `working` | `topology_lab_menu.py` / `_handle_sandbox_action(...)` | `canonical` | `no` | `no` | not separately timed | Changes sandbox shape selection only. |
| `Rotate` | `working` | `topology_lab_menu.py` / `_handle_sandbox_action('sandbox_rotate')` | `canonical` | `no` | `no` | not separately timed | Sandbox-only rigid-rotation check. |
| `Show Trace` / `Hide Trace` / `Reset` | `working` | `topology_lab_menu.py` / `_handle_sandbox_action(...)` | `canonical` | `no` | `no` | not separately timed | Trace toggle / local sandbox reset only. |

### Legacy Compatibility Surface Still Reachable Through `Workspace Path`

| control | classification | owner / main handler | canonical state? | preview compile? | topology recompute? | latency | notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `Legacy Preset` | `legacy-backed` | `legacy_panel_support.py` / `adjust_legacy_row('preset')` | `legacy` | `no` on migrated explorer path | `legacy-only` | not timed | Compatibility row only. |
| `Legacy Topology` | `legacy-backed` | `legacy_panel_support.py` / `adjust_legacy_row('topology_mode')` | `legacy` | `no` on migrated explorer path | `legacy-only` | not timed | Compatibility row only. |
| `X- / X+ / Z- / Z+ / W- / W+` | `legacy-backed` | `legacy_panel_support.py` / `adjust_legacy_row(axis edge)` | `legacy` | `no` on migrated explorer path | `legacy-only` | not timed | Retained per-edge legacy controls. |
| `Y- / Y+` | `legacy-backed` | `legacy_panel_support.py` / locked row | `legacy` | `no` | `legacy-only` | not timed | Intentionally locked in `Normal Game (legacy compat)`. Still looks like a compatibility artifact, not a modern explorer control. |
| `Save Legacy Profile` | `legacy-backed` | `controls_panel.py` / `_save_profile(...)` | `legacy` | `no` | `legacy-only` | not timed | Legacy profile save path. |
| `Export Legacy Resolved Profile` | `legacy-backed` | `controls_panel.py` + `legacy_panel_support.py` / `_run_export(...)` | `legacy` | `no` | `legacy-only` | not timed | Legacy export bridge is still intentionally present. |
| `Back` (legacy surface) | `legacy-backed` | `controls_panel.py` / `state.running = False` | `shell-local` | `no` | `no` | n/a | Shell exit, but still part of the compatibility branch. |

## B. Slow Interaction Paths

| action | latency measurement | call path | suspected root cause |
| --- | --- | --- | --- |
| First 4D preview compile (startup) | `375.4 ms` shell startup, `369.8 ms` preview compile | `_initial_topology_lab_state(...) -> _initialize_explicit_explorer_startup(...) / _sync_explorer_state(...) -> _refresh_explorer_scene_state(...) -> compile_explorer_topology_preview(...) -> build_movement_graph(...)` | First 4D movement-graph compile dominates shell entry cost. |
| Dimension change (`3D -> 4D`) | `376.2 ms` handler, including `370.6 ms` preview compile | `_cycle_dimension(...) -> _sync_explorer_state(...) -> _refresh_explorer_scene_state(...) -> compile_explorer_topology_preview(...) -> build_movement_graph(...)` | 4D preview rebuild is the main cost. `_mark_updated(...)` then adds a second canonical sync + cached refresh pass. |
| Board-size change (4D) | `427.1 ms` handler, including `424.0 ms` preview compile | `_set_explorer_board_dim(...) -> _mark_play_settings_updated(...) -> _refresh_explorer_scene_state(...) -> compile_explorer_topology_preview(...) -> build_movement_graph(...)` | Every board-size edit recompiles the full 4D movement graph synchronously. |
| Preset switch (4D) | `696.9 ms` handler, including `692.6 ms` preview compile | `_cycle_explorer_preset(...) -> _mark_updated(...) -> _refresh_explorer_scene_state(...) -> compile_explorer_topology_preview(...) -> build_movement_graph(...)` | Valid preset switches are blocked on a full 4D graph rebuild. Unsafe presets can also leave the shell in an invalid-preview state. |
| Seam create / edit (4D) | `682.7 ms` create, `718.0 ms` edit | `_apply_explorer_glue(...) -> _mark_updated(...) -> _refresh_explorer_scene_state(...) -> compile_explorer_topology_preview(...) -> build_movement_graph(...)` | Every topology mutation recompiles the full preview graph synchronously. One-glue states are much slower than the empty default state. |
| Seam remove (4D) | `420.1 ms` handler, including `416.4 ms` preview compile | `_remove_explorer_glue(...) -> _mark_updated(...) -> _refresh_explorer_scene_state(...) -> compile_explorer_topology_preview(...) -> build_movement_graph(...)` | Still a synchronous full preview rebuild, even though it returns to the empty topology. |
| Preview export (4D) | `402.8 ms` handler, including `398.5 ms` preview compile | `_run_export(...) -> export_explorer_topology_preview(...) -> compile_explorer_topology_preview(...) -> build_movement_graph(...) -> write_json_object(...)` | Export does not reuse the already-compiled live preview payload. |
| Experiment pack generation (4D) | `10.31 s` handler, split into `5.11 s` compile + `5.20 s` export | `_run_experiments(...) -> compile_runtime_explorer_experiments(...) -> compile_parallel_explorer_experiments(...) -> _experiment_entry(...) -> compile_explorer_topology_preview(...) -> build_movement_graph(...)`; export then reruns the whole pack via `export_runtime_explorer_experiments(...)` | Full pack compiled twice. Default 4D pack has `7` candidates, so the handler executes `14` preview compiles. Expensive unsafe families (`Projective Space`, `Sphere`) each take ~`1.68-1.74 s`. |
| Probe move (4D) | `0.345 ms` | `_apply_probe_step(...) -> advance_explorer_probe(...)` | Not a hotspot. |
| Sandbox move (4D) | `0.273 ms` | `piece_sandbox.move_sandbox_piece(...) -> move_sandbox_piece_runtime(...)` | Not a hotspot. |
| Play preview launch handoff (4D shell path) | `0.048 ms` handler, `0.028 ms` launch phase with gameplay launch stubbed | `_launch_play_preview(...) -> launch_playground_state_gameplay(...) -> build_gameplay_config_from_topology_playground_state(...) -> front4d_game.run_game_loop(...)` | Explorer-side handoff is not the stall. Any larger delay after click is downstream gameplay startup, not the explorer interaction layer itself. |

## C. Preview / Topology Recompute Triggers

### Triggers Preview Compilation

- Explorer shell startup / initial explicit explorer state construction
- `Dimension`
- `Board X / Y / Z / W`
- `Explorer Preset`
- `Apply`
- `Remove`
- `Export Explorer Preview`
- `Build Experiment Pack` (`7` candidates compiled twice on the default 4D pack)

### Does Not Trigger Preview Compilation

- `Piece Set`
- `Speed`
- `Workspace Path` while staying on the already-loaded explorer branch
- tool-ribbon mode changes (`Navigate`, `Inspect`, `Create`, `Edit`, `Probe`, `Sandbox`, `Play Mode`)
- boundary picks / seam picks / glue-slot selection / permutation buttons / sign toggles until `Apply`
- probe movement
- sandbox movement / spawn / rotate / reset / trace toggle
- `Play This Topology` shell handoff

### Triggers Canonical State Sync / Shell Reconstruction

- Explorer startup
- `Workspace Path`
- `Dimension`
- `Board X / Y / Z / W`
- `Piece Set`
- `Speed`
- `Explorer Preset`
- `Apply`
- `Remove`

### Triggers Experiment Analysis

- `Build Experiment Pack` only

### Triggers Sandbox State Rebuild / Refit

- entering `Sandbox`
- `Spawn`
- `Prev Piece` / `Next Piece`
- `Rotate`
- `Reset`
- `Piece Set` change (shape catalog / fit recalculated on next sandbox ensure)
- dimension change or explorer startup when sandbox state is rehydrated from canonical playground state

## D. Legacy / Snapshot Involvement

Remaining legacy or snapshot-backed paths are now narrow, but they are still real:

- `Workspace Path` still fronts the retained legacy compatibility surface. All `Legacy *` rows, the locked `Y- / Y+` rows, and `Export Legacy Resolved Profile` still route through `legacy_panel_support.py` and `state.profile`.
- `scene_state.py` still retains shell snapshot fields for `probe_coord`, `probe_trace`, `probe_path`, `highlighted_glue_id`, and `pending_source_index`.
- Probe fallback still has a snapshot-only branch. `current_probe_*` reads from shell-local state whenever the trace contains `Probe unavailable:` via `_probe_unavailable_locally(...)`.
- `Create` still depends on shell-local `pending_source_index` while selected boundary and draft data are canonical. This is a small but real mixed-ownership path.
- `piece_sandbox._runtime_state_for_sandbox(...)` can still rebuild canonical playground state on demand if a caller reaches sandbox helpers before canonical state is present.
- `Dimension` still does duplicated shell orchestration: `_cycle_dimension(...)` performs `_sync_explorer_state(...)` and then `_mark_updated(...)`, so canonical sync and scene refresh are each reached twice. The second pass is cached and cheap, but it is still duplicated reconstruction.

None of the measured multi-hundred-millisecond stalls are caused by the legacy compatibility branch itself. The large stalls are all on synchronous preview / experiment compilation. The remaining legacy and snapshot involvement shows up as degraded control semantics and duplicated orchestration rather than as the main latency hotspot.

## E. Ranked Performance Hotspots

1. `Build Experiment Pack`
   - `10.31 s` in 4D because the full preset-family pack is compiled twice (`14` preview compiles total on the default pack).
2. 4D topology-mutation preview rebuilds
   - `Explorer Preset`, `Apply`, and `Edit` all sit in the `0.68-0.72 s` range because each blocks on `build_movement_graph(...)`.
3. 4D board / startup preview rebuilds
   - first 4D entry is ~`370 ms`; 4D board-size change is ~`424 ms`; seam removal back to empty still costs ~`416 ms`.
4. Preview export recompilation
   - `Export Explorer Preview` is ~`403 ms` because it compiles again instead of exporting `state.scene_preview`.
5. Duplicate dimension-change orchestration
   - not the largest absolute cost, but still unnecessary: `_cycle_dimension(...)` hits canonical sync / scene refresh twice, once for the real compile and once for a cached second pass.

Not hotspots:

- probe movement
- sandbox movement
- piece-set change
- speed change
- explorer-side play-launch handoff

## F. Proposed Fix Stages

### Stage A - Interaction Latency Reduction

- Remove duplicated `_sync_explorer_state(...)` + `_mark_updated(...)` refresh work on dimension/gameplay-path changes.
- Short-circuit cheap launch-setting edits (`Piece Set`, `Speed`) before scene refresh when the preview signature has not changed.

### Stage B - Preview Compile Caching / Reuse

- Promote the `(profile, dims)` preview cache into a reusable owner that export and experiment code can share.
- Export the current `state.scene_preview` when the requested signature already matches the live scene instead of recompiling.

### Stage C - Experiment Pack Single-Pass Generation

- Compile the experiment batch once, keep the payload in memory, and export that same payload.
- Do not call `compile_parallel_explorer_experiments(...)` once for recommendation and then again for export.

### Stage D - Legacy / Snapshot Retirement

- Isolate `Workspace Path -> Normal Game (legacy compat)` behind an explicit compatibility affordance instead of a peer row in the main explorer shell.
- Remove shell-local `pending_source_index` / probe-unavailable snapshot fallbacks once the remaining consumers migrate.

### Stage E - Unsafe Preset Handling

- Preflight unsafe preset families against the active board dimensions before blocking the shell on a synchronous compile.
- Surface invalid-result affordances more explicitly so `Explorer Preset` reads as intentionally risky rather than partially broken.

## Short Conclusion

The explorer is no longer vague-slow. The slow paths are specific and concentrated:

- one 4D preview compile costs ~`0.37-0.72 s` depending on the current topology,
- preview export costs ~`0.40 s` because it recompiles,
- experiment pack generation costs ~`10.3 s` because it recompiles the entire preset family twice,
- probe and sandbox movement are already fast and are not the stall source.

The main remaining functional degradations are also specific:

- `Workspace Path` is still legacy-backed,
- `Play Mode` is still only a mode toggle,
- `Explorer Preset` can still enter preview-invalid unsafe families,
- `Create` and probe-unavailable handling still retain shell-local support state.
