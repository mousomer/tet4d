# CURRENT_STATE (Restart Handoff)

Last updated: 2026-07-11
Worktree expectation: clean unless an active batch is in progress

## Purpose

This file is the restart handoff for the current repo baseline. It is not a
historical ledger, a validation transcript, or a second workflow authority.
Historical rollout detail belongs in `docs/history/DONE_SUMMARIES.md`.

## Active Focus

- Primary product cleanup still routes through
  `docs/plans/topology_playground_current_authority.md` and
  `docs/BACKLOG.md`.
- Governance routing now has an explicit overlay:
  `docs/governance/README.md` routes Python, Godot UI, native C++,
  testing/parity, config/constants, secrets, and mixed migration work;
  `docs/architecture/authority_map.md` preserves Python as the semantic oracle
  and scopes Godot/C++ authority to documented, parity-backed transfers.
- Stage 45 Python reference hardening continues on
  `codex/python-reference-dedup-major-pass`. Stage 45A's mapped-pose legality
  and atomic commit owner remains in `engine/core/rules/piece_placement.py`.
  The continued pass centralizes spawn installation/game-over handling,
  rotation resolve-and-commit, and current-piece lock/clear/score/analysis state
  mutation; the public legality facade and ND planner now use public
  dimensional legality adapters. Regression coverage protects helper behavior
  and 2D/embedded-ND movement, rotation, hard-drop, spawn, lock, clear, and
  scoring equivalence. Topology-aware movement transport, dimensional
  spawn/bag rules, and planner algorithms remain explicitly separate. Python
  remains semantic authority; gameplay and topology rules, replay/parity
  schemas, Godot, native C++, migration bundles, and authority ownership are
  unchanged.
- Stages 43 and 44 are complete on `master`: the README/philosophy correction
  presents Python/pygame as the current full playable/reference implementation,
  and topology explorer render-time probes reuse bounded caches without
  semantic changes.
- Stage 35 gameplay/topology sweep is active on
  `codex/gameplay-topology-sweeps`: Topology Playground launch settings now
  clamp unsupported `rigid_play_mode` values from saved/source settings to
  `auto` before canonical runtime state construction; the sweep also adds
  invariant coverage for 2D/ND placement, translation, rotation, hard-drop,
  spawn, and topology seam behavior. `BoardND.can_place` now rejects duplicate
  candidate cells to match the central placement validator. This is Python
  gameplay/topology boundary hardening only and does not change topology
  traversal, drop/lock legality, rigid-play policy, Godot/C++ routing, parity
  logic, or authority ownership.
- Stage 36 replay/parity contract hardening is active on
  `codex/replay-parity-contract`: replay payloads now carry an explicit
  version marker, reject unknown or missing semantic fields with readable
  replay-format errors, and migration bundle manifests record replay, trace,
  config, topology, piece-set, and RNG identity needed for Python-to-native
  replay comparison. This is contract hardening only and does not change
  gameplay rules, topology features, Godot/C++ ownership, or authority
  transfer.
- Stage 37 engine public API boundary cleanup is active on
  `codex/engine-public-api-boundary`: UI/tutorial/frontend legality previews
  route through public engine legality queries instead of private gameplay
  helpers. This is authority-boundary cleanup only and does not change
  movement, rotation, drop/lock, spawn, topology traversal, Godot/C++ routing,
  or authority ownership.
- Stage 39 C++ core geometry slice is complete on `master`: native C++ exposes
  narrow parity-backed piece-geometry query helpers for ND block
  normalization, translation, rotation, and stable geometry hashing, with
  Python oracle parity coverage and Godot bridge smoke coverage. This is a
  deterministic helper slice only and does not transfer gameplay, topology,
  replay, parity-schema, or semantic authority away from Python.
- Stage 40 C++ legality/topology query slice is complete on `master`: native
  C++ exposes query-only legality and topology diagnostics for bounded piece
  pose/translation/rotation legality, collision, strict bounds, duplicate
  candidate-cell rejection, bounded/torus neighbor resolution, and seam
  transport metadata. The slice is parity-backed against Python public engine
  legality APIs, central placement validation, and `ExplorerTransportResolver`,
  and Godot sees it only through diagnostic GDExtension queries. It does not
  change gameplay, topology, replay, live-session state, or authority
  ownership.
- Stage 41 Godot playable loop parity acceptance is complete on `master`: the
  existing Godot Live Plain 2D/3D/4D entry points and bridge-backed live
  sessions are protected with headless deterministic coverage for spawn,
  movement, rotation, soft drop, hard drop, lock, HUD/status-visible snapshot
  state, and Python-golden parity export health. This is
  acceptance/protection only; it does not rebuild playable loops, change
  gameplay/topology/replay rules, introduce new native gameplay ownership,
  make Godot gameplay depend on the Stage 39/40 query helpers, or transfer
  semantic authority away from Python.
- Stage 42 demo-quality milestone is complete on `master`: first-run clarity,
  launch guidance, mode discovery, controls/help discoverability, and honest
  limitations were improved across the public README and Godot shell. This is
  product/readability work only; it does not change gameplay, topology, replay
  schemas, authority routing, native ownership, or Stage 45A dedup scope.
- Live-mode keyboard exit semantics are now aligned around `Esc` as the
  universal back/quit path in pygame shells and overlays. `Q` is no longer a
  live-mode quit/back alias, visible quit/back buttons remain clickable, and
  Live 4D keeps `Q/E` reserved for `w-` / `w+` movement only. This is UI/input
  routing plus HUD-copy cleanup only; gameplay semantics are unchanged.
- Stage 23 Live Plain 4D Godot Prototype is implemented narrowly. Manual GUI
  acceptance found W labels too small, Space leaking to focused UI activation,
  and active Live 4D cells too bright. Stage 23b corrects those acceptance
  defects by enlarging/backing W labels, consuming live Space as hard-drop
  before UI accept handling, and reducing Live 4D active-cell brightness while
  preserving active/locked distinction. Stage 23c further corrects Live 4D
  view/readability by replacing W labels with clear `W SLICE n/N` headers,
  opening/resetting Live 4D in a canonical fitted W-slice view, preserving Fit
  View as recovery, and adding safe camera controls on `I/K`, `O/L`, and
  `-`/`=`. Stage 23d corrects those zoom controls so Live 4D orthographic zoom
  changes camera size, supports `-`, `=`, and `+`, survives focused UI controls
  and mode switching, keeps mouse-wheel up/down direction correct, and keeps
  Fit View as the fitted W-slice recovery action.
  Stage 23 Live Plain 4D Godot Prototype passed manual GUI acceptance after
  Stage 23b/23c/23d corrections. Live 4D is accepted as a narrow plain bounded
  prototype. Stage 24 Live ND polish and hardening passed manual acceptance.
  Stage 25 topology Godot/C++ port planning is now documented in
  `docs/plans/topology_godot_core_port_plan.md`. Topology implementation and
  endgame remain deferred. Stage 24 hardens the Godot live ND shell only:
  re-entering an existing Live 2D, Live 3D, or Live 4D session from Replay now
  resumes the selected live mode without resetting its native C++ state,
  pauses non-selected live modes, clears live UI focus/repeat state on entry,
  and keeps pre-UI Space hard-drop and Live 4D camera/zoom capture active
  after focus changes. C++ gameplay semantics, trace parity, topology, and
  endgame remain unchanged. The manual Stage 24 checklist in
  `docs/plans/live_nd_manual_acceptance.md` passed before Stage 25 topology
  planning.
  Stage 25 is planning-only: Python remains the topology oracle, C++ is the
  future topology transport/gameplay authority after parity, Godot remains
  topology product shell/render/HUD/editor presentation, and the accepted
  plain bounded Live 2D/3D/4D plus Replay baseline must stay preserved. The
  next recommended stage is Stage 26 topology trace contract audit /
  expansion before native topology implementation.
- Stage 28 Godot shell compliance and layout stabilization is complete. The
  audit and layout contract live in
  `docs/architecture/godot_shell_layout_stabilization.md`; Godot remains a
  product-shell/replay-view and accepted live-shell presentation surface, and
  `ReplayHud` now installs explicit shell minimums so the right inspector
  cannot be consumed by the game panel.
- Stage 29 Godot shell settings registry foundation is complete. The
  architecture note is
  `docs/architecture/godot_shell_settings_source_of_truth.md`; the registry
  lives at `godot/Tet4D.Godot/config/shell_settings_registry.json` and covers
  only replay, display, theme, diagnostics, and controls-help shell settings.
  It adds no gameplay, topology, movement, keyboard rebinding, Python config
  migration, parity logic, native semantic authority, or authority transfer.
- Stage 30 Godot replay shell UX acceptance is complete. The architecture note
  is `docs/architecture/godot_replay_shell_ux_acceptance.md`; manual launch
  confirmed the Godot main menu is readable, while automated interaction was
  blocked by macOS assistive-access permissions. The batch keeps fixes
  shell-local: Plain is now a distinct display theme/palette, the generated
  settings panel has clearer shell-only framing and wrapped labels, and the
  layout contract covers settings-panel horizontal reachability inside the
  right inspector. It adds no gameplay, topology, trace semantics, parity
  evidence, native authority, or authority transfer.
- Stage 31 Godot visual style authority is complete. The architecture note is
  `docs/architecture/godot_visual_style_authority.md`; it defines the Godot
  product-shell visual direction as diagrammatic, readable, high-contrast,
  technical, and lightly futuristic, fixes the `diagnostic`, `plain`, and
  `tron` theme model, records semantic colour roles, typography, spacing,
  component, board/replay, and accessibility rules, and accepts the current
  replay/settings shell as the MVP visual-style implementation baseline with
  known manual-navigation limitations. It is design authority only and adds no
  Godot implementation, gameplay, topology, trace semantics, parity evidence,
  native authority, or authority transfer.
- Stage 32 Godot visual style foundation is complete. The architecture note is
  `docs/architecture/godot_visual_style_foundation.md`; Godot now has a
  central `config/shell_theme_palettes.json`, style role/palette/manager/
  control-applier scripts under `godot/Tet4D.Godot/scripts/ui/style/`, `tron`
  as the default `theme.name`, and shared style-role routing for shell
  controls plus board/replay visual materials. This is product-shell styling
  only and adds no gameplay, topology, trace semantics, replay-frame
  semantics, parity evidence, native authority, or authority transfer.
- Stage 32b Godot Neon CAD Cockpit style refinement is complete under the same
  architecture note. It tightens direct shell-control styling, inspector value
  labels, panel role naming, and board/bottom-bar style snapshot coverage
  without adding a new theme, redesign authority, gameplay, topology, trace
  semantics, replay-frame semantics, parity evidence, native authority, or
  authority transfer.
- Stage 33 Godot Vector Arcade Cockpit UI overhaul is implemented on branch
  `codex/vector-arcade-cockpit-ui` under
  `docs/architecture/godot_vector_arcade_cockpit_overhaul.md`. It keeps the
  Stage 32 style-role architecture and moves the Godot shell toward
  command-card menus, grouped keycap/action hints, compact settings cards,
  explicit inspector sections, `Vector Arcade` display labeling for the
  internal `tron` theme ID, and stronger board/W-label visual emphasis. It is
  product-shell visual UX only and adds no gameplay, topology, trace
  semantics, replay-frame semantics, parity evidence, native authority, or
  authority transfer. Stage 38 accepts the Stage 33 cockpit UI branch on the
  current `master` baseline: manual GUI launch confirmed the command-card main
  menu readability and explicit Python-authority/replay-only framing, while
  Godot acceptance/layout tests exercised replay and live shell states for
  keyboard-hint persistence, unchanged hint-panel behavior, game-over error
  styling, bundle-status restoration, camera/help affordances, Tab/Fit View
  wording, right-inspector reachability, and live/replay declutter. This
  records product-shell acceptance only and adds no gameplay, topology,
  replay/parity schema, native semantic, or authority-transfer change. Stage
  33a is the corrective
  live-mode acceptance repair on the same branch: replace diagnostic live HUD
  prose with structured scoped status, full/quick grouped controls, status
  badges, and W-slice card/header hierarchy while preserving the same
  product-shell-only boundary and avoiding gameplay, topology, replay,
  parity, native semantic, or authority-transfer changes. Stage 33b is the
  follow-up declutter pass: W labels are demoted to subtle orientation markers,
  live quick controls are removed from the central board area, and the live
  replay bottom bar is hidden/reduced so the right inspector remains the single
  complete live control map. Stage 33c is the layout-consolidation pass after
  Stage 33b was accepted with issues: live modes hide the replay case-browser
  side panel, remove dangling top/viewport command-render detail, give the
  recovered space to the board, keep controls first in the right inspector, and
  leave diagnostics/settings secondary while preserving subtle W labels and the
  same product-shell-only boundary. Stage 33d is the compact live control-map
  pass after Stage 33c was accepted with issues: Live Plain 4D movement,
  rotation, and camera rows are grouped as inverse pairs, rotation gets one
  section-level CCW/CW hint, and system controls remain one-per-row without
  changing bindings or gameplay semantics. Stage 33e is the focused wording,
  camera-presentation, and palette polish pass after Stage 33d was accepted
  with issues: Plane Rotation wording replaces the awkward signed rotation
  text, live game-over reasons are mapped to user-facing labels, comma/period
  and Shift-drag add camera roll without gameplay dispatch, mouse camera hints
  document orbit/roll/zoom/Fit View, and the default Vector Arcade palette uses
  calmer Blueprint Arcade tokens. Stage 33f preserves the visible `Restart
  Game` button and endgame mouse camera controls while gameplay commands remain
  blocked, and moves the Calm Blueprint hierarchy into config-owned roles for
  `hint.section`, `hint.keycap.border`, `hint.keycap.text`, `hint.action`,
  `hint.note`, and `hint.error`. Stage 33f review repairs keep that boundary
  while preserving keyboard-hint settings across replay/live transitions,
  restoring bundle status after live mode, avoiding unchanged hint-panel
  rebuilds, styling live game-over badges from explicit status roles, routing
  W-label opacity through `label.w_layer`, repairing Tab/Fit View control-map
  drift, and removing obsolete camera pan code after Shift-drag became camera
  roll.
- Python review repairs are in progress on branch
  `codex/python-review-fixes` under the existing architecture owners: AI
  playbot planning now targets controller-reachable ND orientation
  representatives and combines follow-up scores correctly; replay scripts
  preserve JSON-safe config fields; runtime settings, keybindings,
  state-root path resolution, and atomic JSON writes are hardened;
  menu/keybinding catalogs report missing targets and order drift; tutorial
  setup application is rollback-safe and pending setup is consumed only after
  setup is successfully applied to committed game state. This batch adds no
  gameplay authority transfer, topology semantics, parity evidence, native
  authority, or Godot/C++ routing change.
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
- Stage 10 completes that deferred short-trace hash work: the native C++ core
  now computes Python-compatible SHA-256 over compact canonical JSON, emits
  per-frame and final `state_hash` values matching
  `gameplay_plain_2d_short`, and strengthens
  `tools/migration/compare_cpp_gameplay_trace.py` to compare hashes and report
  field-level diffs. The Godot-facing surface remains parity/smoke-only with
  `get_plain_2d_required_field_parity`; no live gameplay, topology, 3D, 4D,
  endgame, Python runtime, C#, Steam, or console API is added.
- Stage 11 broadens the plain bounded 2D parity foundation with three new
  Python golden traces: `gameplay_plain_2d_rotation_short`,
  `gameplay_plain_2d_hard_drop_lock`, and
  `gameplay_plain_2d_line_clear_short`. The native C++ core now matches all
  Stage 11 plain 2D traces on required fields plus per-frame/final
  `state_hash`, and the Godot-facing surface remains parity-only by case id:
  `list_plain_2d_parity_cases`, `export_plain_2d_trace_json(case_id)`, and
  `get_plain_2d_required_field_parity(case_id)`. This still does not expose
  live gameplay controls, topology, 3D, 4D, endgame, Python runtime, C#,
  Steam, or console APIs.
- Manual Stage 11 replay acceptance should inspect post-command snapshots, not
  invented hard-drop animation. Gameplay active cells render with the replay
  active role color and a smaller cell scale so synthetic trace color IDs do
  not produce a green merged blob.
- Stage 12 adds a narrow live plain bounded 2D Godot shell. Godot captures
  input and renders C++ snapshot JSON through the existing renderer; the native
  `Plain2DSession` owns movement, rotation, gravity tick, hard drop, lock,
  line clear, scoring, spawn, status, and state hash. Replay mode remains
  separate. This does not authorize 3D, 4D, topology, endgame, Python runtime,
  C#, Steam, or console work.
- Stage 12b keeps that boundary and makes the live surface acceptable enough
  for manual playability checks: the live session uses a C++-owned fixed
  classic sequence (`I, O, T, S, Z, J, L`) separate from Stage 11 parity
  fixtures, exposes the current piece in live snapshots/status, and Godot shows
  live-specific controls/status while rendering cells through the shared visual
  role system. The remaining Stage 12 defect closure keeps game-over semantics
  native-owned: snapshots expose `game_over`, `game_over_reason`, `paused`, and
  `state_hash`, gameplay commands are rejected after game-over except reset,
  Godot stops only its automatic gravity ticks when native game-over is true,
  the live hint strip is always visible and mode-specific, and live cells use
  Python-like colored tetromino styling with crisp borders and a readable board
  grid through the shared renderer.
- Stage 13 is a plain bounded 2D live polish stage, not the old 3D-port slot.
  Godot may own elapsed-time accumulation, held-key detection, HUD labels, and
  mode switching, but it only sends command strings. C++ still owns gravity
  tick results, movement/rotation legality, lock, line clear, score, piece
  sequence, next/current piece reporting, game-over, and state hash. Live
  replay switching preserves the native session unless Reset/New Game is used.
  Ghost/drop preview remains deferred until C++ computes it.
- Stage 14 is planning/governance only for extending the native core from the
  accepted plain bounded 2D baseline to plain bounded 3D/4D trace parity. The
  plan is `docs/plans/plain_nd_core_parity_plan.md` and chooses a conservative
  sidecar ND path: preserve `Plain2DSession` and Stage 11/13 2D behavior, then
  target `gameplay_plain_3d_short` and `gameplay_plain_4d_short` as native
  trace parity work. Python remains the oracle until C++ matches those traces,
  including `state_hash`; no 3D/4D live Godot gameplay, topology, endgame, C#,
  Python runtime calls from Godot, or Godot-side gameplay legality is
  authorized by Stage 14.
- Stage 15 implements that sidecar path as trace parity infrastructure only.
  The native C++ core now has a separate plain-ND model and trace exporter for
  `gameplay_plain_3d_short` and `gameplay_plain_4d_short`, with
  `tools/migration/compare_cpp_gameplay_trace.py --all-plain-nd` checking the
  Python golden traces including frame/final `state_hash`. Godot exposes only
  parity/list/export/status methods for these ND traces. Stage 16 adds the
  next coverage-planning step in `docs/plans/plain_nd_coverage_expansion_plan.md`.
  Stage 17 adds Python-oracle traces for plain 3D/4D rotation, plane clear,
  and spawn-blocked game-over. Stage 18 implements native C++ parity only for
  `gameplay_plain_3d_rotation_short` and
  `gameplay_plain_4d_rotation_short`, including `last_rotation_plane`,
  `last_rotation_steps`, active-cell, and `state_hash` parity. Stage 19
  implements native C++ parity only for
  `gameplay_plain_3d_plane_clear_short` and
  `gameplay_plain_4d_plane_clear_short`, including full gravity-axis
  plane/hyperplane clear, compaction, generic `lines`, score, locked-cell
  digest, and frame/final `state_hash` parity. Stage 20 implements native C++
  parity only for `gameplay_plain_3d_spawn_blocked_game_over` and
  `gameplay_plain_4d_spawn_blocked_game_over`, including Python spawn
  position, blocked active-piece preservation, unchanged locked cells,
  `drop_lock_status.game_over`, and frame/final `state_hash` parity. This
  does not authorize live Godot 3D/4D gameplay, topology transport, endgame
  simulation, C#, Python runtime calls from Godot, or Godot-side gameplay
  legality. Stage 21 is planning-only for the next live plain ND product step:
  `docs/plans/live_plain_nd_godot_prototype_plan.md` chooses Stage 22 as a
  live plain 3D Godot prototype, Stage 23 as live plain 4D, requires reuse of
  the existing Godot trace coordinate mapper/renderer path, and keeps C++ as
  the sole gameplay legality owner. Stage 21 itself adds no live ND session
  code, Godot live ND mode, topology, endgame, C#, or Python runtime calls.
  Stage 22 implements that live plain 3D prototype only: C++ now owns a live
  `PlainNDSession`-backed 3D session and `live_3d_*` facade, Godot adds a
  separate Live 3D mode that sends command strings and renders returned
  snapshots through the existing mapper/renderer, and the HUD/hints show
  `LIVE 3D · C++ CORE`. Stage 22b is a visual acceptance correction for that
  same Live 3D slice: cells render as solid cuboids with Live 3D-specific
  material/outline roles, Fit View uses a readable Live 3D angle, and the HUD
  shows signed last-rotation feedback from C++ command/status results. Stage
  22c continues that visual-only pass by rendering Live 3D cells as opaque
  exterior face panels with restrained silhouettes and subtle face brightness
  cues so pieces read as solid external blocks rather than interior walls.
  Stage 22d adds the design-only gameboard visual-language authority at
  `docs/plans/gameboard_visual_language_design.md`: the remaining issue is
  active-piece orientation ambiguity, not convexity. Stage 22e must implement
  the canonical exterior diagram view, stable axis/near-far/drop landmarks, an
  explicit active-piece origin/orientation cue, rotation-plane feedback,
  primary-surface HUD visibility, the structural Godot shell layout, and a
  focused presentation/projection owner through the existing mapper/renderer
  path. Stage 22e is partial after the shell layout and presentation-boundary
  stabilization in this handoff. The initial Stage 22f manual inspection did
  not pass because the Live 3D default view read from below, camera view-state
  diagnostics were absent, bundle status could be clipped, and active cells
  were not distinct enough from locked cells. Stage 22g is a visual-only
  correction pass for those observations: Live 3D Fit/default uses the
  above-board `LIVE_3D_EXTERNAL_DIAGRAM_VIEW`, the HUD exposes camera
  preset/projection/yaw/pitch/roll/fit state and compact bundle health, and
  active Live 3D cells get stronger face/outline priority plus an origin
  marker. Stage 22f manual Live 3D visual acceptance passed after Stage 22g
  corrections, as recorded in
  `docs/plans/godot_live_3d_manual_acceptance.md`. Stage 23 Live Plain 4D
  Godot Prototype is implemented narrowly: C++ owns the live 4D session through
  `PlainNDSession`, Godot exposes a separate Live 4D mode, renders side-by-side
  W slices through the existing mapper/renderer, routes Q/E as W movement, and
  routes six direct rotation plane pairs while keeping Live 2D, Live 3D, Replay,
  golden traces, topology, and endgame preserved. Topology/endgame remain
  deferred. py-godot and any Python runtime bridge inside Godot are not the
  active architecture.
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
- `deep_imports.ai_to_engine_non_api.count = 28` (allowed under current rule)
- `engine_core_purity.violation_count = 0`
- `migration_debt_signals.pygame_imports_non_test.count = 0`
- `tech_debt.score = 5.67` (`low`)

Dominant remaining pressure:

1. `delivery_size_pressure = 2.76`
2. `code_balance = 1.91`
<!-- END GENERATED:current_state_metric_snapshot -->

<!-- BEGIN GENERATED:current_state_drift_watch -->
## Live Drift Watch

Generated from `tools/governance/check_drift_protection.py` and `config/project/policy_pack.json`.

Top 8 live Python hotspots by real LOC:

1. `tools/governance/validate_project_contracts.py`: `3785` real LOC
2. `tests/unit/engine/test_topology_lab_menu.py`: `3721` real LOC
3. `tests/unit/render/test_locked_cell_explosion.py`: `3466` real LOC
4. `src/tet4d/ui/pygame/locked_cell_explosion/surface.py`: `3039` real LOC
5. `tests/unit/governance/test_governance_validate_project_contracts.py`: `2329` real LOC
6. `src/tet4d/ui/pygame/front4d_render.py`: `2152` real LOC
7. `scripts/arch_metrics.py`: `1891` real LOC
8. `src/tet4d/ui/pygame/endgame_animation.py`: `1866` real LOC

Thin-wrapper budgets:

1. `cli/front.py: 800/840 real LOC (compatibility launcher wrapper)`
2. `cli/front2d.py: 15/24 real LOC (thin 2D launcher shim)`
3. `cli/front3d.py: 15/24 real LOC (thin 3D launcher shim)`
4. `cli/front4d.py: 15/24 real LOC (thin 4D launcher shim)`
5. `src/tet4d/engine/api.py: 136/160 real LOC (small engine compatibility facade)`
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
- Keep dependency / utility reuse governance linked through
  `docs/architecture/utility_index.md`,
  `docs/policies/POLICY_NO_REINVENTING_WHEEL.md`, and
  `tools/governance/validate_utility_reuse.py`; duplicate-helper findings are
  advisory unless strict utility-reuse mode is explicitly enabled.
- Next migration task after Stage 12 verification is to harden the live plain
  2D shell against Python behavior with additional parity traces before
  expanding to 3D/4D/topology.
