# CURRENT_STATE (Restart Handoff)

Last updated: 2026-05-17
Worktree expectation: clean unless an active batch is in progress

## Purpose

This file is the restart handoff for the current repo baseline. It is not a
historical ledger, a validation transcript, or a second workflow authority.
Historical rollout detail belongs in `docs/history/DONE_SUMMARIES.md`.

## Active Focus

- Primary product cleanup still routes through
  `docs/plans/topology_playground_current_authority.md` and
  `docs/BACKLOG.md`.
- Topology Lab semantic freeze is now the migration-blocking gameplay
  authority: `Editor` owns topology construction, gluing, preset selection,
  validation, and launch eligibility; `Sandbox` owns free probe/piece
  exploration and seam diagnostics; `Play` owns launched gameplay with its
  stricter drop/lock legality. Wrap / invert / sphere-like selections are
  transport presets, not visual presets or spawn presets.
- Stage 2 topology/gameplay golden trace export and Stage 3 endgame golden
  trace export now exist under `tools/migration/` with checked-in traces in
  `migration/golden_traces/`. Those traces are the Python-authoritative
  migration oracle for topology transport, Sandbox-vs-Play movement
  distinction, gameplay drop/lock policy, `Play This Topology` launch parity,
  and locked-cell endgame particle motion. Unity, Godot, C#, C++, or any other
  engine migration must replay those traces before introducing independent
  transport, drop/lock, or endgame simulation logic. Pygame shell and endgame
  visual polish are not the blocking items for that migration.
- Stage 4 migration packaging now exports a generated, disposable bundle under
  `migration/exported_bundle/` using `tools/migration/export_config_bundle.py`.
  The bundle includes a manifest, config snapshot, trace copies/indexes, schema
  index, authority-doc index, and README for future Unity/Godot replay spikes.
  It is not a source of truth: config remains authoritative in `config/`,
  Python semantics remain authoritative in `src/`, and trace authority remains
  in `migration/golden_traces/`.
- Stage 5 adds a Unity replay spike under `unity/Tet4D.Unity/` plus
  `tools/migration/sync_unity_bundle.py` to copy the generated bundle into
  Unity `StreamingAssets`. The Unity spike remains a replay-only comparison
  artifact: it loads copied topology/gameplay/endgame traces, browses cases,
  steps frames, and renders diagnostics, but it does not call Python at
  runtime or implement gameplay, topology transport, or endgame simulation
  semantics.
- Stage 6 now adds the primary engine-shell spike under `godot/Tet4D.Godot/`
  plus `tools/migration/sync_godot_bundle.py` to copy the generated bundle
  into `res://assets/tet4d_bundle/`. The Godot spike is replay-only and exists
  to evaluate menus, diagnostics panels, display clarity, playback controls,
  simple animation polish, and 4D trace readability. It does not call Python
  at runtime or implement gameplay, topology transport, or endgame simulation
  semantics. The current Godot shell now also uses a shared replay theme and
  centralized visual constants so the case browser, diagnostics column,
  viewport framing, timeline, and 4D W-slice cards read as a deliberate tool
  shell instead of a raw debug layout; replay-only status must be explicit in
  the top bar and controls, and default board/glyph contrast must be high
  enough that the shell cannot be mistaken for a dim unplayable placeholder.
  Startup now defaults to `Diagnostic High Contrast` display mode with
  centralized role-based opaque materials for cells, probes, particles, event
  markers, board outlines, and W-slice cards; optional `Tron` styling remains
  presentation-only and must not reduce baseline replay readability. The shell
  now starts at a real Main Menu and routes through Trace Replay Browser,
  Replay Viewer, Settings, Controls / Keyboard Hints, and Diagnostics screens;
  opening a copied trace switches to the viewer with visual-only interpolation
  between current and next exported frames only when stable trace identity
  exists (`particle_id` for endgame particles), discrete gameplay cell updates
  when stable identity is absent, short particle trails attached to their
  mapped particle positions, event marker pulse/fade, fixed replay speed
  presets, a shared trace-to-world coordinate mapper aligned with the
  Python/Pygame centered board display convention, Python trace color IDs for
  replay object materials, deterministic Python-informed orthographic Fit View
  using projected board bounds and immediate camera snapping, mapper-owned W
  label positions, frame/entity metadata diagnostics, a single
  container-owned Replay Viewer layout that constrains the replay `SubViewport`
  inside `GameArea`, keeps the scrollable right inspector as a fixed-width body
  sibling, exposes geometry diagnostics, visible `Fit View` / `Quit Replay`
  controls, and a replay-only keyboard hint strip; those effects are renderer
  presentation only and must not become gameplay, topology transport, or
  endgame simulation logic.
- Stage 7 records the Godot engine decision and core-port plan in
  `docs/plans/godot_core_port_plan.md`. Godot is accepted as the primary
  product shell direction, conditional on completed manual visual acceptance of
  the Stage 6/6b replay viewer. The shell language remains GDScript. The
  recommended core language is C++ GDExtension; C# remains an alternative only
  if port speed clearly outweighs export, console, and long-term dependency
  concerns. Python remains the oracle/reference until trace parity passes.
  Stage 7 is documentation/governance only: it does not add C++, C#,
  GDExtension scaffolding, gameplay, topology, endgame, trace, config, or
  runtime changes. Stage 8 may start only with a C++ GDExtension skeleton,
  build/test scaffolding, and no gameplay port.
- Stage 8 adds that C++ GDExtension skeleton under `native/tet4d_core/` with
  the official `godot-cpp` repository as `native/third_party/godot-cpp`. The
  native plain-C++ helper layer is independent of Godot types, the Godot-facing
  wrapper is `Tet4DCoreApi`, and the only exposed calls are version/status,
  echo, stable text hash, and integer addition. The Godot bridge lives under
  `godot/Tet4D.Godot/scripts/native/`, and the smoke test is wired into the
  Godot test runner. This is native integration proof only and must not be
  extended into gameplay, topology, endgame, trace parity, config authority,
  Python runtime, C#, Steam, or console implementation in Stage 8.
- Stage 9 starts the semantic native port with the smallest plain bounded 2D
  core needed for `gameplay_plain_2d_short` parity. The contract is
  `docs/plans/plain_2d_core_parity_contract.md`. C++ now owns `Board2D`,
  `PieceShape2D` / `ActivePiece2D`, `GameState2D`, `GameCommand2D`, and
  `GameStepper2D` for that short trace only, plus deterministic trace export
  used by `tools/migration/compare_cpp_gameplay_trace.py`. Godot exposes only
  parity/smoke calls (`run_builtin_plain_2d_smoke_case`,
  `get_plain_2d_parity_status`, `export_plain_2d_trace_json`); it still does
  not expose playable controls or implement topology, 3D, 4D, endgame,
  Python runtime calls, or live gameplay APIs. Required trace fields match the
  Python golden trace; frame/final `state_hash` parity is explicitly deferred.
- Current topology-playground helper ownership is:
  `controls_panel_rows.py` for row inventory,
  `controls_panel_values.py` for display/value derivation,
  `controls_panel_actions.py` for explorer row mutations and seam-edit actions,
  `controls_panel_routing.py` for navigation/pane/shortcut/enter routing,
  `controls_panel_commands.py` for save/export/experiment command execution,
  `controls_panel_launch.py` for play-preview launch preparation and runtime
  handoff,
  `controls_panel.py` for the public shell facade and only the remaining
  shell-entry compatibility seams,
  `scene_state.py` for the state shape plus pane/tool/workspace routing,
  `scene_state_canonical.py` for canonical runtime sync/write and fallback
  storage handling,
  and `scene_state_probe.py` for probe selectors, probe mutations, and
  probe-state synchronization.
- Current topology-playground preview/playability contract is:
  `scene_preview_state.py` treats explorer topology plus resolved board dims as
  the only preview/playability signature, restores same-signature cached
  playability results when available, and queues deferred rigid analysis only
  for valid states whose rigid result is still unknown.
- Current projected gameplay render contract is:
  active-piece translation/rotation tweening must keep stable board
  presentation frozen for the full move while only active-piece geometry
  animates; in `3D` / `4D`, helper marks, projected grid primitives,
  anchoring/fit, and locked-cell projection stay frozen against that cached
  presentation, tweened active-piece cells stay on the opaque active-piece
  draw path, and `4D` caches frozen per-layer presentation once per discrete
  move/tween start instead of rebuilding it every frame. Shared
  `bottom_boundary` / `all_boundaries` projection-guide modes now span `2D` /
  `3D` / `4D` as render-only overlays driven by animated active-piece render
  state against that stable presentation, with dimension-specific boundary
  targets and no gameplay/explorer-legality mutation.
- Current menu-control typing contract is:
  settings and setup fields must keep explicit semantic types through parsing,
  normalization, and rendering; `toggle` is boolean-only, `selector` is
  categorical-only, `slider` is numeric-only, and discrete numeric setup or
  settings rows may use `stepper` instead of a slider.
- Current menu anti-redundancy contract is:
  single-option pages are forbidden unless they use an exempt `layout_role`
  or an explicit `allow_single_option: true` plus a documented reason; the
  existing `Controls` and general keybinding landing pages are deliberate
  exemptions, not silent shims.
- Current launcher root IA is:
  root launches `2D` / `3D` / `4D` directly (same-row `Play` / `Setup`),
  includes `Replay Last`, `Leaderboard`, `Help / Tutorials`, and `Advanced`;
  `Advanced` owns `Settings`, `Topology Playground`, `Explosion Simulator`,
  `Bot`, and `Last Custom Topology`; `Quit` is no longer a visible root row
  (shortcut behavior remains). `Settings` is now split into `Gameplay`,
  `Board / Setup Defaults`, `Controls`, `Display`, `Audio`, and
  `Endgame / Explosion` (including full per-dimension `explosion_defaults.*`
  editing surfaces); Settings still uses its custom loop but now renders the
  shared menu side buttons for `Backspace` / `Esc` / `Q`. Shared menu input
  semantics now use
  `Backspace` as ordinary menu-up/back, `Esc` as exit-only from the current
  menu root (after cancelling active modal/text input), and `Q` as global
  quit; `Backspace` / `Esc` / `Q` are rendered as persistent clickable side
  buttons in the shared menu shell.
- Current seam-translation animation contract is:
  translation tweening must keep gameplay-owned piece cell order as the stable
  source-to-destination correspondence, so ordinary moves and safe seam
  traversals preserve mino identity while non-safe seam traversals still stay
  transport-derived instead of rematching destination cells by set-based
  heuristics; explorer-mode traversal legality still allows those non-safe
  seam traversals, while gameplay-only rigid restrictions remain gameplay-
  owned.
- Current locked-cell explosion contract is:
  `src/tet4d/ui/pygame/locked_cell_explosion/` owns standalone particle-state,
  seam/boundary transport, explicit `boundary_response` (`escape` / `bounce`)
  plus `particle_collisions` (`off` / `on`) handling, engine-backed render
  state projection, and class-prioritized aggregated audio; connected seams
  must transport both position and velocity, non-connected boundaries must
  obey only `boundary_response`, the main launcher now exposes a direct
  standalone `Explosion Simulator` surface backed by the explorer topology
  preset registry rather than a simulator-local topology list, topology-
  playground `Sandbox` now launches that same dedicated simulator surface
  seeded from current sandbox cells/topology instead of an in-scene overlay,
  `3D` / `4D` simulator preview now defaults to true board-native views
  instead of topology-playground projection panes, standalone/explorer source
  selection now includes engine-backed `single_cell`, `single_piece`, and
  deterministic `piece_change` snapshots plus inherited-state handoff,
  shared simulation state now tracks live kinetic energy plus live
  compact speed-squared terms derived from current particle velocities,
  default standalone launches keep a documented uniform particle-mass
  assumption of `m = 1.0`, simulator diagnostics show a compact live
  explicit kinetic-energy formula sourced from the current active particles,
  simulator controls now include live `uniform` / deterministic `random`
  mass modes with bounded mass-range controls plus numeric particle-collision
  elasticity while boundary bounce stays on its separate elastic rule,
  and the same shared state now also owns a non-mutating movement-
  diagnostics monitor with `off` / `summary` / `full` modes that tracks
  per-step/substage kinetic-energy deltas, contacts, suspicious events,
  and focused particle drilldown from live particle state,
  simulator projection-reference rendering now reuses the shared
  topology-lab projection renderer with explorer-only chrome disabled so
  hidden-slice labels, probe dots, and seam-pill ribbons stay out of the
  simulator while remaining available in real explorer views,
  simulator preview now supports an optional thin
  `Trace` overlay in both board-native
  and projection-reference modes plus a bounded user-controlled text-editable
  retention value, true-board preview now routes independent shared
  `grid_mode` (`none` / `edge` / `full`) plus `shadow_mode` selection through
  board-native rendering with projected board-line occlusion in `3D` / `4D`,
  and board-native trace projection in `3D` / `4D` must use the same actual
  particle centers as the rendered explosion cells with no half-cell render
  offset; bounce contacts in that shared trail history must record the true
  boundary-plane contact point before any interior stabilization/nudge so the
  rendered trace follows the simulated center path through boundary turns,
  including the immediate same-frame post-bounce continuation instead of
  implying a visible wall pause,
  simulator defaults now persist through the shared `state/menu_settings.json`
  `explosion_defaults.<mode>` authority via a real `Save Defaults` action
  instead of simulator-local hardcoded startup values, and that same saved
  defaults model now seeds standalone startup, explorer-triggered simulator
  launches where relevant, and overlapping endgame explosion-controller
  defaults with transient runtime-only simulator state excluded from
  serialization; endgame snapshot capture must not let the legacy endgame
  settings branch override saved shared boundary/collision/default behavior;
  that shared saved profile now also owns
  `endgame_live_cell_fraction` (default `0.12`), and endgame launch applies a
  thin deterministic live-subset adapter before calling the shared explosion
  runtime so only a readable fraction of locked gameplay cells enter live
  simulation, using `0` when no locked cells exist and otherwise clamping
  `round(fraction * available_locked_cells)` to `1..available_locked_cells`;
  native-board endgame moving-cell rendering must
  consume only that selected live subset, while non-selected or escaping cells
  stay out of the board-native particle path; escaping cells are represented
  only as capped deterministic short-lived shell artifacts plus bounded
  grid-break overlay marks derived from those artifacts, not full cell/cube
  render states or a destructible grid model, full selected topology seam rules
  now feed the shared survivor runtime without gameplay drop/lock gravity-axis
  exclusions, trace and shadow defaults control projected endgame rendering,
  4D W-movement style reaches the actual layer draw path, and rupture timing
  now uses a stronger config-backed charge/breakaway/artifact-visibility window
  with low-alpha cracked-board residue derived from capped grid-break marks and
  static shell state; the standalone simulator now also owns a preview-only
  staged shell harness with config-backed hold/rupture/shard/residue timing,
  a preview-only time-scale control, frozen source-cell hold rendering before
  rupture, capped short-lived cell-shaped rupture proxies that launch from
  those exact frozen source cells toward the selected boundary impacts, and
  impact/shard/residue overlays that keep escaping cells out of the shared
  controller/native-board survivor particle path; shell-preview model causality
  now also routes through `endgame_shell_effects.py` escape-event chains plus
  data-only sound-event generation before any later renderer/audio adoption,
  `4D` true-board preview now supports selectable `fade` / `box_size`
  W-movement animation styles while reusing the gameplay layer-scale path,
  shared ND camera input now reuses the existing gameplay/explorer
  camera-control path, and
  seam/bounce contact presentation must start on the actual board boundary
  planes while bounce-mode post-contact state remains strictly inside the
  board volume; the canonical rendered/simulated board boundary is the shared
  cell-extent face box at `-0.5 .. size - 0.5` per axis reused by seam/bounce
  contact, box/edge-grid rendering, and render-only boundary guides; wrapped
  simulator rows/footer text must remain unobscured, and game-end render/audio
  handoff must route through the shared controller rather than gameplay
  tetromino ownership.
- Governance after the policy-pack migration stays locked to:
  `config/project/policy_pack.json` for machine-readable policy,
  `docs/WORKFLOW_CODEX.md` for human workflow, and `CURRENT_STATE.md` for
  restart-only handoff.
- Generated ownership and source-of-truth inventories live in
  `docs/PROJECT_STRUCTURE.md`, not here.

## Current Authority

- For topology-playground architecture and active migration-state questions,
  start with `docs/plans/topology_playground_current_authority.md`.
- For topology-playground shell behavior, use
  `docs/plans/topology_playground_shell_redesign_spec.md`.
- For repo workflow, verification sequencing, and context-switch guidance, use
  `docs/WORKFLOW_CODEX.md`.
- For active open work and current change footprint, use `docs/BACKLOG.md`.
- For the generated migration bundle and packaging boundary, use
  `docs/plans/migration_config_bundle.md`.
- For the Unity replay spike boundary, use
  `docs/plans/unity_trace_replay_spike.md`.
- For the Godot replay spike boundary, use
  `docs/plans/godot_trace_replay_spike.md`.
- For the Godot core-port decision and Stage 8+ migration order, use
  `docs/plans/godot_core_port_plan.md`.
- For historical detail only, use `docs/history/DONE_SUMMARIES.md` and
  `docs/history/topology_playground/current_state_archive_2026-03-31.md`.

## Known Watchouts

- Do not reopen Stage 1 governance by reintroducing deleted split-authority
  files or a second machine-readable policy source.
- Do not let `tools/governance/validate_project_contracts.py` regain
  policy-shaped inventories that belong in `config/project/policy_pack.json`.
- Do not let `CURRENT_STATE.md` regrow batch ledgers, validation histories, or
  generated ownership snapshots.
- Do not let `controls_panel.py` re-absorb routing, command, launch, or
  non-shell explorer mutation helpers; keep any retained compatibility
  re-exports thin and keep deferred playability ownership in
  `scene_preview_state.py`.
- Do not let probe-only, sandbox-only, helper-only, or non-topological launch
  state drift into the preview/playability signature; only explorer topology
  plus resolved board dims should invalidate cached preview/playability
  results.
- Do not let `scene_state.py` re-absorb canonical sync/write glue or
  probe-state normalization now owned by `scene_state_canonical.py` and
  `scene_state_probe.py`, and do not drift boundary/glue selection or
  highlight-glue helpers back through that facade once callers import the
  focused owner modules directly.
- Do not let projected `3D` / `4D` active-piece animation recompute board
  presentation from transient tween geometry; helper marks, projected
  gridlines, and locked-cell projection must remain tied to the frozen
  presentation snapshot for the move.
- Do not let seam-crossing translation animation rematch destination cells by
  sorting, canonicalization, nearest-neighbor pairing, or any other unordered
  endpoint heuristic; gameplay/transport cell order is the animation identity
  contract.
- Keep `docs/BACKLOG.md` as the open-work tracker and
  `docs/PROJECT_STRUCTURE.md` as the generated structure/source-of-truth
  inventory.

Sections with `BEGIN/END GENERATED:*` markers are maintained by
`tools/governance/generate_maintenance_docs.py`.

<!-- BEGIN GENERATED:current_state_metric_snapshot -->
## Current Metric Snapshot

From `python scripts/arch_metrics.py`:

- `deep_imports.engine_to_ui_non_api.count = 0`
- `deep_imports.engine_to_ai_non_api.count = 0`
- `deep_imports.ui_to_engine_non_api.count = 258` (allowed under current rule)
- `deep_imports.ai_to_engine_non_api.count = 27` (allowed under current rule)
- `engine_core_purity.violation_count = 0`
- `migration_debt_signals.pygame_imports_non_test.count = 0`
- `tech_debt.score = 5.32` (`low`)

Dominant remaining pressure:

1. `delivery_size_pressure = 2.66`
2. `code_balance = 1.67`
<!-- END GENERATED:current_state_metric_snapshot -->

<!-- BEGIN GENERATED:current_state_drift_watch -->
## Live Drift Watch

Generated from `tools/governance/check_drift_protection.py` and `config/project/policy_pack.json`.

Top 8 live Python hotspots by real LOC:

1. `tests/unit/engine/test_topology_lab_menu.py`: `3721` real LOC
2. `tests/unit/render/test_locked_cell_explosion.py`: `3466` real LOC
3. `src/tet4d/ui/pygame/locked_cell_explosion/surface.py`: `3039` real LOC
4. `src/tet4d/ui/pygame/front4d_render.py`: `2152` real LOC
5. `tools/governance/validate_project_contracts.py`: `1914` real LOC
6. `scripts/arch_metrics.py`: `1890` real LOC
7. `src/tet4d/ui/pygame/endgame_animation.py`: `1866` real LOC
8. `src/tet4d/ui/pygame/locked_cell_explosion/board_view.py`: `1691` real LOC

Thin-wrapper budgets:

1. `cli/front.py: 800/840 real LOC (compatibility launcher wrapper)`
2. `cli/front2d.py: 15/24 real LOC (thin 2D launcher shim)`
3. `cli/front3d.py: 15/24 real LOC (thin 3D launcher shim)`
4. `cli/front4d.py: 15/24 real LOC (thin 4D launcher shim)`
5. `src/tet4d/engine/api.py: 91/160 real LOC (small engine compatibility facade)`
6. `src/tet4d/ui/pygame/front2d_game.py: 116/180 real LOC (2D orchestration entrypoint)`

Tutorial wording drift guard:

1. Lesson copy must not start with `Goal:` or `Action:`.
2. Tutorial overlay must keep `Do this:`, `Tip:`, and `USE:` tokens.
<!-- END GENERATED:current_state_drift_watch -->

## Restart Checklist

1. `git branch --show-current`
2. `git status --short`
3. Read:
   - `AGENTS.md`
   - `CURRENT_STATE.md`
   - `docs/WORKFLOW_CODEX.md`
   - `docs/BACKLOG.md`
   - `docs/PROJECT_STRUCTURE.md`
4. If the task is architecture-sensitive, capture fresh metrics:

```bash
python scripts/arch_metrics.py
```

5. Re-run the local gate before commit or handoff:

```bash
CODEX_MODE=1 ./scripts/verify.sh
```

## Next Steps

- Continue topology-playground cleanup from `docs/BACKLOG.md` without reopening
  the frozen shell contract.
- Continue trimming only the remaining real shell-entry seams in
  `controls_panel.py` and `scene_state.py` without collapsing the focused
  helper splits back into one file.
- Keep the hardened preview/playability contract explicit: same-signature
  refreshes restore cached results when available, invalid preview states do
  not queue pointless rigid scans, and play-preview launch only forces
  completion when a valid rigid result is still pending.
- Keep the projected animation contract explicit: board presentation in `3D` /
  `4D` remains stable through active-piece tweens, tweened active-piece cells
  stay opaque, `4D` builds that frozen presentation once per move/tween
  start, and only the active-piece geometry may vary across tween frames.
- Keep the seam-translation contract explicit: active-piece tweening preserves
  stable per-cell identity for ordinary and safe seam traversals, and keeps
  non-safe seam traversals transport-derived instead of re-pairing cells from
  unordered destination sets while explorer-mode traversal legality still
  allows those non-safe crossings.
- Keep the locked-cell explosion contract explicit: standalone simulator first,
  explorer sandbox integration second, game-end handoff third; preserve
  velocity-aware seam transport, split `boundary_response` /
  `particle_collisions` semantics, keep true board-native `3D` / `4D`
  simulator views plus engine-backed snapshot sources/kinetic-energy display,
  and preserve class-prioritized aggregated audio
  instead of reintroducing gameplay-object ownership or one-sound-per-event
  playback.
- Keep governance edits pack-driven and update workflow/backlog/current-state
  docs together when boundary rules change.
