# Consolidated Backlog

Generated: 2026-02-18  
Updated: 2026-07-06
Scope: active open backlog, governance watchlist, and compact recent change footprint.

## Current Authority

- Topology-playground architecture authority:
  `docs/plans/topology_playground_current_authority.md`
- Topology-playground visible-shell contract:
  `docs/plans/topology_playground_shell_redesign_spec.md`
- Topology-playground active debt ledger:
  `docs/plans/topology_playground_debt_register.md`
- Documentation routing authority:
  `docs/DOCUMENTATION_MAP.md`
- Governance/runtime policy authority:
  `config/project/policy_pack.json`
- Governance routing overlay:
  `docs/governance/README.md`
- Godot/C++ migration authority map:
  `docs/architecture/authority_map.md`
- Gameboard visual-language authority:
  `docs/plans/gameboard_visual_language_design.md`

Older topology-playground manifests and older batch notes are historical
background only unless reactivated by a future task.

## Active Work

Stage 31a repairs remote CI bootstrap after the Stage 31/32 push sequence
without changing gameplay, Godot visual implementation, parity semantics, or
roadmap scope. The first shared CI failure was the common verification step:
GitHub-hosted Ubuntu exposed `clang-format`, which made deferred native tooling
advisory mode fail opportunistically before pytest. CI now runs the same
`CODEX_MODE=1 ./scripts/verify.sh` contract used locally and marks native
tooling as explicit CI advisory until the documented strict-mode readiness
checklist is complete.

Python review-repair batch (2026-07-06): fix review findings inside existing
AI, replay, runtime, tutorial, and UI-logic ownership boundaries. Scope covers
controller-reachable ND playbot orientation representatives, follow-up score
selection, lossless JSON-safe replay config payloads, state-root override path
resolution, atomic JSON writes, saved keybinding duplicate validation with
documented compatibility aliases, integer setting clamps, missing submenu
target linting, keybinding catalog order/headings validation, and tutorial
setup rollback/application-acknowledgement sequencing. This is a hardening
batch only and does not introduce new gameplay authority, topology behavior,
parity logic, native authority, or authority transfer.

Current sub-batch (2026-05-05): topology-lab semantic freeze is pinned for
migration, Stage 2 topology/gameplay golden trace export records that behavior
as the Python-authoritative migration oracle, Stage 3 endgame golden trace
export records locked-cell explosion model behavior, and Stage 4 exports the
generated migration config bundle under `migration/exported_bundle/`. Follow-up
work now includes the Stage 5 Unity replay comparison spike under
`unity/Tet4D.Unity/` and the Stage 6 primary Godot replay spike under
`godot/Tet4D.Godot/`. Both consume copied bundle assets and replay frames
without adding engine-owned semantics. Follow-up work should still consume the
bundle and replay `migration/golden_traces/` before any Unity/Godot/C#/C++
implementation; Stage 6b aligns the Godot replay display with existing
Python/Pygame projection, board, color, and trail conventions while keeping
Godot replay-only; Stage 7 records Godot as the conditional primary product
shell direction and recommends C++ GDExtension for the future deterministic
core while keeping Python as oracle until trace parity passes; Stage 8 adds
only the C++ GDExtension skeleton/native-call smoke test, Stage 9 starts the
semantic port with the smallest plain bounded 2D core needed to match
`gameplay_plain_2d_short`, and Stage 10 completes that short trace's canonical
snapshot and `state_hash` parity. Stage 11 broadens plain bounded 2D parity
with small Python golden traces for rotation, hard-drop lock, and line clear;
it still does not open 3D, 4D, topology, endgame, live Godot gameplay, Python
runtime, C#, Steam, or console
implementation; Stage 12/12b and Stage 13 have accepted the narrow live plain
bounded 2D Godot shell with C++ as gameplay authority; Stage 14 was the
planning-only gate for plain bounded 3D/4D native trace parity, Stage 15 adds
the sidecar native plain-ND trace scaffold for the short 3D/4D golden traces,
Stage 18 adds native parity only for the plain 3D/4D rotation traces, and
Stage 19 adds native parity only for the plain 3D/4D plane-clear traces.
Stage 20 adds native parity only for the plain 3D/4D spawn-blocked game-over
traces. Stage 21 adds the planning-only live plain ND Godot prototype plan,
choosing live plain 3D for Stage 22 and live plain 4D for Stage 23 while
preserving the accepted live 2D shell. Stage 22 implements live plain 3D only:
C++ owns the live 3D session and command results, while Godot routes input,
renders snapshots through the existing mapper/renderer, and shows live 3D
HUD/hints. Stage 22b corrects Live 3D visual acceptance only: Live 3D cells
render as solid cuboids with centralized roles/outlines, Fit View uses a
readable 3D angle, and the HUD shows signed XY/XZ/YZ rotation feedback from
returned C++ command/status data. Stage 22c keeps that visual-only scope and
changes Live 3D cells to opaque exterior face panels with restrained
silhouettes so pieces read as solid external blocks rather than interior walls.
Stage 22d adds the design-only gameboard visual-language authority for the
remaining orientation ambiguity. Stage 22e/22g completed the Live 3D visual
grammar implementation and correction path, and Stage 22f manual acceptance
passed after those corrections.
Stage 22f manual Live 3D visual acceptance passed after Stage 22g corrections.
Stage 23 Live Plain 4D Godot Prototype is implemented narrowly: C++ owns the
live 4D session, Godot renders side-by-side W slices through the existing
mapper/renderer, Q/E move W, six direct rotation pairs are wired, and Live 2D,
Live 3D, Replay, topology, endgame, and golden traces remain preserved. Stage
23 Live Plain 4D Godot Prototype passed manual GUI acceptance after Stage
23b/23c/23d corrections. Live 4D is accepted as a narrow plain bounded
prototype. Stage 24 Live ND polish and hardening passed manual acceptance as
shell lifecycle/input hardening. Stage 25 topology Godot/C++ port planning is
documented in `docs/plans/topology_godot_core_port_plan.md`. Topology
implementation and endgame remain deferred. A topology trace contract audit /
expansion remains required before native topology implementation, but it is
not part of this parity Stage 26 selection.
Stage 23 Python oracle boundary audit is documented in
`docs/architecture/python_oracle_boundary_audit.md`: Python gameplay semantics
and golden traces remain oracle material, while pygame UI history, helper
panels, obsolete helpers, duplicated utilities, and temporary migration harness
layout are not automatically authoritative for Godot/C++ porting. This audit
does not transfer authority or authorize gameplay/topology/rendering/native
changes. The next structural-but-safe candidate remains trace envelope
validation after parity tooling/package review.
Stage 24 parity tooling/package review is documented in
`docs/architecture/parity_tooling_package_review.md`: the review records the
`tools/migration/` versus `tools/parity/` package decision because the four
maintained parity harnesses now form a reusable parity family. Stage 25 then
applies that isolated routing/refactor so reusable parity harnesses live under
`tools/parity/`, while parity logic, fixtures, and authority remain unchanged.
Stage 26 structural parity slice selection is documented in
`docs/architecture/structural_parity_slice_selection.md`: it selects trace
envelope validation for Stage 27 only. It does not implement a harness, add
fixtures, inspect trace events, change gameplay/topology/movement/rendering,
or transfer authority.
Stage 27 trace envelope validation parity is documented in
`docs/architecture/trace_envelope_validation_parity.md`: it adds a
fixture-backed `tools/parity/` harness for top-level trace envelope structure
only. It does not validate trace event semantics, board snapshots, piece
positions, topology traversal, movement/drop/collision/lock,
rendering/Godot/C++, native/provisional output, or authority transfer.
py-godot and Python runtime bridging inside Godot are not active architecture.
Shell-preserving cleanup and endgame visual polish remain non-blocking and
must not reopen semantics.
Pygame live-mode control cleanup now also treats `Esc` as the universal
back/quit key across live shells, removes `Q` as a live quit/back alias, keeps
visible quit/back buttons clickable, and preserves Live 4D `Q/E` as `w-` /
`w+` only; this remains a UI/input/HUD-copy batch and must not change gameplay
semantics.
Current active follow-ups:

- Dependency / utility reuse governance now has a mechanical stage: keep
  `docs/architecture/utility_index.md`, `docs/policies/POLICY_NO_REINVENTING_WHEEL.md`,
  `tools/governance/validate_utility_reuse.py`,
  `tools/governance/check_wheel_reuse_rules.py`, and
  `tools/governance/check_dedup_dead_code_rules.py` linked through the
  governance router and review checklist. Duplicate-helper findings remain
  advisory by default unless strict utility-reuse mode is explicitly enabled.
- Project drift protection now has a mechanical stage: keep
  `docs/governance/drift_protection_map.md`,
  `tools/governance/validate_drift_protection.py`,
  `tools/governance/validate_governance.py`, and
  `tools/governance/validate_project_contracts.py` aligned so governance
  routing, authority/parity, generated-file, debt/advisory, utility-index, and
  review-checklist drift fail with actionable diagnostics.
- topology semantics are now the migration-blocking authority: `Editor` owns
  construction/validation/launch eligibility, `Sandbox` owns free probing, and
  `Play` owns gameplay launch plus stricter drop/lock legality; wrap /
  invert / sphere-like choices remain transport presets rather than UI themes
- Stage 2 exports golden topology/gameplay traces from the Python authority;
  Stage 3 exports golden endgame traces from the headless locked-cell
  explosion model; Stage 4 exports a generated, non-authoritative config bundle
  with trace copies/indexes, config snapshots, schema metadata, and authority
  doc indexes; Stage 5 adds a Unity replay-only comparison spike that loads
  the copied bundle from `StreamingAssets`, and Stage 6 adds a Godot replay-
  only primary shell spike that loads the copied bundle from
  `res://assets/tet4d_bundle/`; both render frame data and expose case/frame
  browsing without implementing independent transport, gravity/drop, or
  endgame simulation logic; Stage 7 now chooses Godot as the conditional
  primary shell, keeps GDScript shell-only, recommends C++ GDExtension for the
  deterministic core, and defers implementation to Stage 8+ behind trace
  parity gates
- Stage 8 adds a minimal C++ GDExtension skeleton only: plain C++ helper layer,
  `Tet4DCoreApi` wrapper, GDScript bridge, build script, and Godot smoke test
  for version/status/echo/stable-hash/addition calls; gameplay/topology/endgame
  implementation remains blocked until later parity stages
- Stage 9 adds a minimal plain bounded 2D C++ parity core for
  `gameplay_plain_2d_short`: `Board2D`, `PieceShape2D` / `ActivePiece2D`,
  `GameState2D`, `GameCommand2D`, `GameStepper2D`, native tests, and
  `tools/migration/compare_cpp_gameplay_trace.py`; Godot exposes only
  parity/smoke calls and remains non-playable
- Stage 10 adds Python-compatible compact canonical JSON SHA-256 hashing and
  now matches `gameplay_plain_2d_short` per-frame/final `state_hash` values;
  the compare tool reports field-level diffs and checks hashes
- Stage 11 broadens plain bounded 2D parity to
  `gameplay_plain_2d_rotation_short`, `gameplay_plain_2d_hard_drop_lock`, and
  `gameplay_plain_2d_line_clear_short`; the native/Godot API remains
  parity-only by case id and does not expose live gameplay controls; manual
  replay inspection should treat these as post-command snapshots, with active
  gameplay cells rendered using role color rather than synthetic trace green
- Stage 12 adds the first live plain bounded 2D Godot shell: Godot routes
  input and renders native snapshots, while C++ owns all gameplay state
  transitions and hashes. Replay mode remains intact and separate.
- Stage 12b hardens that live plain bounded 2D shell without broadening scope:
  C++ owns a deterministic fixed classic sequence, Godot displays mode-specific
  live controls/status and renders live cells through the shared visual role
  system, and Stage 11 parity fixtures remain unchanged. Remaining Stage 12
  defect closure adds native-owned game-over reason/status fields, rejects
  gameplay commands after game-over except reset, stops Godot gravity ticks
  only after the native snapshot reports game-over, makes live/replay hint
  strips always-visible and mode-specific, and aligns live cell/grid styling
  with the Python colored board language.
- Stage 13 follows with plain bounded 2D gameplay polish only: shell-owned
  gravity timing, movement/soft-drop input repeat, pause/reset/mode-switch
  cleanup, next-piece/status HUD display, and tests. C++ remains the sole
  gameplay authority; 3D, 4D, topology, endgame, C#, Python runtime, and
  packaging work stay out of scope.
- Stage 14 is planning/governance only for plain bounded 3D/4D native parity.
  `docs/plans/plain_nd_core_parity_plan.md` records the Python ND oracle
  surfaces, existing `gameplay_plain_3d_short` /
  `gameplay_plain_4d_short` trace coverage, and the conservative sidecar ND
  strategy. Stage 14 does not implement 3D/4D code, live Godot 3D/4D gameplay,
  topology transport, endgame simulation, C#, Python runtime calls from
  Godot, or Godot-side gameplay legality.
- Stage 15 adds native plain-ND trace scaffolding beside the accepted 2D core:
  runtime-dimensional coordinates/board/piece/state/command types, export
  support for `gameplay_plain_3d_short` and `gameplay_plain_4d_short`,
  `compare_cpp_gameplay_trace.py --all-plain-nd`, native tests, and
  parity-only Godot bridge smoke coverage. Stage 16 then documents the next
  explicit ND trace expansion in `docs/plans/plain_nd_coverage_expansion_plan.md`.
  Stage 17 adds the corresponding Python-oracle golden traces for plain 3D/4D
  rotation, plane clear, and spawn-blocked game-over. Stage 18 implements
  native C++ parity only for `gameplay_plain_3d_rotation_short` and
  `gameplay_plain_4d_rotation_short`, updates `--all-plain-nd` to include the
  implemented rotation cases. Stage 19 implements native C++ parity only for
  `gameplay_plain_3d_plane_clear_short` and
  `gameplay_plain_4d_plane_clear_short`, updates `--all-plain-nd` to include
  the implemented clear/scoring cases. Stage 20 implements native C++ parity
  only for `gameplay_plain_3d_spawn_blocked_game_over` and
  `gameplay_plain_4d_spawn_blocked_game_over`, updates `--all-plain-nd` to
  include those cases, and keeps live ND gameplay deferred. It still does not
  add live 3D/4D Godot
  gameplay, topology, endgame, C#, Python runtime, or Godot-side gameplay
  legality. Stage 21 adds `docs/plans/live_plain_nd_godot_prototype_plan.md`
  as the live plain ND prototype plan only: Stage 22 prototypes live plain 3D
  first, Stage 23 adds live plain 4D, Godot reuses the existing coordinate
  mapper/renderer, and C++ remains the gameplay authority. Stage 22 implements
  that live plain 3D prototype only, keeping topology, endgame, C#, Python
  runtime calls, and Godot-side
  gameplay legality deferred. Stage 22b is limited to Live 3D cell depth,
  camera readability, and rotation HUD/readability feedback; it does not change
  C++ semantics or start Stage 23. Stage 22c further limits itself to Live 3D
  exterior-face readability, keeping the same mapper/renderer path and C++
  authority boundary. Stage 22d adds
  `docs/plans/gameboard_visual_language_design.md` as the design-only
  authority: Stage 22e must implement the canonical exterior diagram view,
  axis/near-far/drop landmarks, active-piece origin/orientation cue,
  rotation-plane feedback, and primary-surface HUD visibility before Stage 22f
  manual Live 3D acceptance. Stage 22f manual Live 3D visual acceptance passed
  after Stage 22g corrections. Stage 23 Live Plain 4D Godot Prototype is now
  unblocked.
- topology-playground shell-preserving cleanup remains centered on
  `src/tet4d/ui/pygame/topology_lab/scene_state.py` and
  `src/tet4d/ui/pygame/topology_lab/controls_panel.py`, with the
  `scene_state_canonical.py` / `scene_state_probe.py` and focused
  control-helper splits kept intact
- projected-render / locked-cell-explosion recovery is deferred unless an
  external backup appears, or a later branch rebuilds that runtime/render lane
  from current master without relying on a deleted git recovery branch
- documentation authorities should stay synchronized without treating merged
  project-structure-index, docs-authority-cleanup, or config-backed
  runtime-constants work as active implementation
- locked-cell explosion follow-up must keep the 3D true-board trace aligned
  with real bounce contact points and keep kinetic-energy readout validation
  pinned to live controller state rather than assumed visual behavior, with
  the compact explicit kinetic-energy formula and live speed-squared terms
  kept in sync with current particle velocities, keep seeded random-mass and
  collision-elasticity controls wired through the live simulation state, and
  keep bounce-frame trace continuity aligned with the rendered post-contact
  motion path; new movement-diagnostics monitoring should stay non-mutating,
  keep substage energy/localization logic tied to live simulation state, keep
  the shared `explosion_defaults` persistence path as the single source for
  standalone/explorer/endgame explosion defaults, keep endgame launch on the
  shared explosion runtime while using the saved `endgame_live_cell_fraction`
  subset adapter instead of releasing every locked cell into live simulation
  by default, keep legacy endgame settings from overriding saved shared
  boundary/collision/default behavior, and avoid devolving into a decorative
  final-energy readout
- settings follow-up: reevaluate Settings and expose a complete Endgame /
  Explosion section for all persisted `explosion_defaults.*` fields.
- settings follow-up: optional future cleanup to unify the Settings custom loop
  with `MenuRunner` if/when it becomes a small, safe change (no rewrite, no
  duplicated row models, preserve numeric text mode).
- endgame shell follow-up: keep the staged simulator preview harness as the
  fast tuning surface for hold/rupture/shard/residue timing and future actual
  gameplay wiring, while continuing to keep escaping cells out of live
  particles and using only capped short-lived rupture proxies for preview-only
  source-to-boundary escape visualization; keep the new escape-event /
  data-only sound model in `endgame_shell_effects.py` as the single causal
  owner while renderer/audio adoption stays staged.
- persistence follow-up: migrate integer-backed categorical/bool fields toward
  named ids and booleans where feasible (keep semantic/storage typing explicit).
- governance follow-up: validate the new launcher root IA and tighten
  semantic/storage typing gates (`semantic_type` vs stored int indices).

- Open work:
  1. continue structural simplification of remaining
     `src/tet4d/ui/pygame/topology_lab/scene_state.py` routing/facade code and
     any still-live public compatibility seams without collapsing the new
     `scene_state_canonical.py` / `scene_state_probe.py` ownership split
  2. trim residual `src/tet4d/ui/pygame/topology_lab/controls_panel.py`
     shell-entry compatibility seams only when caller complexity drops and
     visible-shell ownership stays in place
  3. keep the explicit preview/playability signature and deferred-analysis
     contract pinned so future UI-only or non-topological state changes do not
     regress into unnecessary preview/playability recompute
  4. if projected-render / locked-cell-explosion work is revived later, rebuild
     it on a fresh branch from current master or from an external backup
     source instead of assuming a recoverable local git branch still exists
  5. keep documentation authorities synchronized without treating completed
     project-structure-index, docs-authority-cleanup, or config-backed
     runtime-constants work as active implementation

- Acceptance bar:
  1. `Topology Playground` remains the direct modern launcher entry
  2. visible workspaces remain `Editor` / `Sandbox` / `Play`
  3. topology/gameplay semantics remain frozen: sandbox probing may exceed
     play drop legality, launched gameplay preserves canonical topology
     transport semantics, and unsafe/playability diagnostics stay deterministic
  4. top bar remains limited to title, workspace tabs, validity chip, and the
     current dimension chip
  5. left sidebar remains limited to the accepted `Editor` / `Sandbox` /
     `Play` inventories, with diagnostics collapsed or secondary
  6. helper stays minimal and external, diagnostics stay secondary
  7. required UI text remains visible and unobscured at supported compact sizes
  8. first-frame explorer startup no longer waits for the full rigid
     playability scan, and same-signature refreshes reuse cached playability
     results
  9. follow-up branches stay single-concern and `CODEX_MODE=1 ./scripts/verify.sh`
     stays green

## 3. Active Open Backlog / TODO

Compatibility mirror for legacy backlog validators. The active execution view
remains the compact sections above.

Cadence: update this mirror whenever the active sub-batch or validation
contracts change.
Trigger: topology-playground runtime work, governance/contract work, or any
batch that changes active acceptance criteria.
Done criteria: the compact backlog stays accurate, this compatibility mirror
stays synchronized, and the contract validator accepts the backlog shape.

1. `WATCH` `[BKL-P3-001]` Backlog contract compatibility:
   keep the compact backlog structure aligned with the still-enforced legacy
   backlog validator until the maintenance contract is updated to the newer
   compact format.
2. `ACTIVE` `[BKL-P3-009]` Topology-playground startup/runtime latency:
   preserve deferred rigid playability analysis, signature-based cache reuse,
   and launch-time forced completion without reopening the frozen shell
   contract.
3. `DONE` `[BKL-P3-010]` Stage 2 golden trace export:
   authoritative topology/gameplay traces are exported from the frozen Python
   lab under `migration/golden_traces/`, and
   `tools/migration/compare_trace.py` regenerates and compares them before
   engine migration work implements independent transport or drop/lock logic.
4. `DONE` `[BKL-P3-011]` Stage 3 endgame trace/export:
   locked-cell endgame motion now has a headless deterministic model API,
   checked-in golden traces under `migration/golden_traces/endgame/`, and
   `tools/migration/compare_trace.py` drift coverage alongside topology and
   gameplay traces.
5. `DONE` `[BKL-P3-012]` Stage 4 config bundle/export:
   the generated migration bundle under `migration/exported_bundle/` packages
   manifest metadata, config snapshots, trace copies/indexes, schema metadata,
   authority-doc indexes, and README guidance;
   `tools/migration/export_config_bundle.py` and
   `tools/migration/compare_config_bundle.py` enforce deterministic drift checks
   without moving config, trace, or Python semantic authority.
6. `DONE` `[BKL-P3-013]` Stage 5 Unity replay spike:
   `unity/Tet4D.Unity/` now consumes a copied Stage 4 bundle from
   `Assets/StreamingAssets/tet4d_bundle/`, exposes replay-only loading for
   topology/gameplay/endgame traces, and keeps Unity on a renderer/browser
   boundary via `tools/migration/sync_unity_bundle.py` rather than direct repo
   reads or runtime Python calls.
7. `DONE` `[BKL-P3-014]` Stage 6 Godot replay spike:
   `godot/Tet4D.Godot/` now consumes a copied Stage 4 bundle from
   `res://assets/tet4d_bundle/`, exposes replay-only loading for
   topology/gameplay/endgame traces plus a themed diagnostic-first
   product-shell UI with labeled 4D W-slice cards, clearer timeline controls,
   quieter side panels, centralized replay-shell visual constants, explicit
   replay-only status messaging, startup-default `Diagnostic High Contrast`
   display mode, centralized role-based opaque replay materials, and
   higher-contrast board/glyph presentation, now with startup autoplay on a
   dynamic copied endgame trace superseded by a minimal screen shell (Main
   Menu, Trace Replay Browser, Replay Viewer, Settings, Controls / Keyboard
   Hints, Diagnostics), visual-only identity-safe frame interpolation,
   discrete gameplay-cell updates when identity is absent, shared
   Python/Pygame-aligned trace-to-world coordinate mapping, Python trace color
   IDs for replay object materials, deterministic Python-informed orthographic
   Fit View using projected board bounds, mapper-owned W label positions,
   attached particle trails, frame/entity
   metadata diagnostics, a single explicit Replay Viewer shell layout that
   reserves top status, left case browser, center `GameArea`, right scrollable
   diagnostics/events/settings inspector, and bottom playback regions so the
   replay `SubViewport` cannot consume side panels, event pulses/fades, replay
   state timeline copy, fixed replay speed presets, and visible fit/quit/help
   replay controls,
   and keeps Godot on a renderer/browser boundary via
   `tools/migration/sync_godot_bundle.py` rather than direct repo reads or
   runtime Python calls.
8. `DONE` `[BKL-P3-015]` Stage 7 Godot core-port plan:
   `docs/plans/godot_core_port_plan.md` records Godot as the conditional
   primary product shell after Stage 6/6b manual visual acceptance, GDScript as
   the shell language, C++ GDExtension as the recommended deterministic core
   path, C# as an alternative only when port speed outweighs export/console
   concerns, and Python as the oracle/reference until topology, gameplay, and
   endgame trace parity passes. Stage 7 is docs/governance only and does not
   add C++, C#, GDExtension, gameplay, topology, endgame, trace, config, or
   runtime implementation.
9. `DONE` `[BKL-P3-016]` Stage 8 C++ GDExtension skeleton:
   add only the native integration proof: official `godot-cpp` submodule,
   `native/tet4d_core/` source tree, plain C++ helper layer, `Tet4DCoreApi`
   wrapper, `.gdextension` addon, GDScript bridge, build script, and Godot
   smoke test for version/status/echo/stable-hash/addition calls. This stage
   must not add gameplay, topology, endgame, trace parity, Python runtime, C#,
   Steam, console, or config authority implementation.
10. `DONE` `[BKL-P3-017]` Stage 9 plain 2D deterministic core parity:
    port only enough C++ core behavior to match
    `gameplay_plain_2d_short` required fields, expose only parity/smoke APIs
    through Godot, keep state-hash parity deferred, and do not add live
    gameplay controls, topology, 3D, 4D, endgame, Python runtime, C#, Steam, or
    console implementation.
11. `DONE` `[BKL-P3-018]` Stage 10 plain 2D snapshot/hash parity:
    complete canonical snapshot and `state_hash` parity for
    `gameplay_plain_2d_short`, keep Godot API parity-only, and defer broader
    2D traces, live gameplay controls, topology, 3D, 4D, endgame, Python
    runtime, C#, Steam, and console implementation.
12. `DONE` `[BKL-P3-019]` Stage 11 broaden plain 2D gameplay parity:
    add small deterministic Python golden traces for rotation, hard-drop lock,
    and line clear; extend the native C++ parity model and case-id APIs only
    enough to match required fields plus `state_hash`; keep Godot non-playable
    and do not expose player movement, topology, 3D, 4D, endgame, Python
    runtime, C#, Steam, or console implementation.
13. `DONE` `[BKL-P3-020]` Stage 12 narrow playable plain-2D Godot shell:
    add a Live 2D mode where Godot captures input and renders snapshots while
    native C++ owns movement, rotation, tick, hard drop, lock, line clear,
    scoring, spawn, and state hash. Keep replay mode intact and do not expose
    topology, 3D, 4D, endgame, Python runtime, C#, Steam, or console work.
14. `DONE` `[BKL-P3-021]` Stage 13 plain 2D gameplay polish:
    polish only the accepted live plain bounded 2D slice with shell-owned
    gravity timing, held-key repeat, pause/reset, mode switching, HUD cleanup,
    and replay preservation while C++ remains gameplay authority.
15. `DONE` `[BKL-P3-022]` Stage 14/15 plain ND core parity foundation:
    document and implement the path from accepted native plain 2D to plain
    bounded 3D/4D trace parity for `gameplay_plain_3d_short` and
    `gameplay_plain_4d_short`, keeping Python as oracle, preserving the
    accepted 2D live path, choosing sidecar ND implementation before broad
    generalization, and forbidding topology, endgame, live Godot 3D/4D
    gameplay, C#, Python runtime calls from Godot, and Godot-side gameplay
    legality.
16. `DONE` `[BKL-P3-023]` Stage 17 plain ND oracle trace expansion:
    add Python-oracle golden traces for plain 3D/4D rotation, plane clear, and
    spawn-blocked game-over while keeping native parity scoped to implemented
    cases.
17. `DONE` `[BKL-P3-024]` Stage 18 native plain ND rotation parity:
    implement native C++ parity only for `gameplay_plain_3d_rotation_short`
    and `gameplay_plain_4d_rotation_short`, including active-cell,
    `last_rotation_plane`, `last_rotation_steps`, and frame/final
    `state_hash` parity through `--all-plain-nd`. Clear/scoring,
    spawn-blocked game-over, live Godot 3D/4D gameplay, topology, endgame, C#,
    Python runtime calls, and Godot-side ND legality remain deferred.
18. `DONE` `[BKL-P3-025]` Stage 19 native plain ND clear/scoring parity:
    implement native C++ parity only for
    `gameplay_plain_3d_plane_clear_short` and
    `gameplay_plain_4d_plane_clear_short`, including full gravity-axis
    plane/hyperplane clear, compaction, generic `lines`, score, locked-cell
    digest, and frame/final `state_hash` parity through `--all-plain-nd`.
    Spawn-blocked game-over, live Godot 3D/4D gameplay, topology, endgame, C#,
    Python runtime calls, and Godot-side ND legality remain deferred.
19. `DONE` `[BKL-P3-026]` Stage 20 native plain ND spawn-blocked game-over parity:
    implement native C++ parity only for
    `gameplay_plain_3d_spawn_blocked_game_over` and
    `gameplay_plain_4d_spawn_blocked_game_over`, including Python spawn
    position, blocked active-piece preservation, unchanged locked cells,
    `drop_lock_status.game_over`, and frame/final `state_hash` parity through
    `--all-plain-nd`. Live Godot 3D/4D gameplay, topology, endgame, C#,
    Python runtime calls, and Godot-side ND legality remain deferred.
20. `DONE` `[BKL-P3-027]` Stage 21 live plain ND Godot prototype plan:
    add `docs/plans/live_plain_nd_godot_prototype_plan.md` as a planning-only
    authority for future live plain ND work. It chooses Stage 22 as live plain
    3D first, Stage 23 as live plain 4D, defines the future native API shape,
    input/rotation controls, rendering/HUD reuse, and keeps Stage 21 free of
    live ND implementation, topology, endgame, C#, Python runtime calls, and
    Godot-side gameplay legality.
21. `DONE` `[BKL-P3-028]` Stage 22 live plain 3D Godot prototype:
    add a native `PlainNDSession`-backed live 3D facade, Godot Live 3D mode,
    direct X/Z movement and XY/XZ/YZ rotation command routing, live 3D
    HUD/hints, and shared mapper/renderer support. Live 2D and replay remain
    preserved; live 4D, topology, endgame, C#, Python runtime calls, and
    Godot-side gameplay legality remain deferred.
22. `DONE` `[BKL-P3-029]` Stage 22b Live 3D visual acceptance correction:
    make Live 3D cells render as solid cuboids through the existing renderer,
    keep Live 2D shallow styling and Replay rendering separate, use a more
    readable Live 3D Fit View angle, and show signed XY/XZ/YZ rotation feedback
    from native command/status data without changing C++ semantics.
23. `DONE` `[BKL-P3-030]` Stage 22c Live 3D exterior-cell readability:
    replace cage-like Live 3D cell presentation with opaque exterior face
    panels, restrained silhouettes, subtle face-orientation cues, and an active
    outline pulse after returned native rotation snapshots while preserving
    Live 2D, Replay, C++ semantics, and the existing coordinate mapper.
24. `DONE` `[BKL-P3-031]` Stage 22d gameboard visual-language design:
    add `docs/plans/gameboard_visual_language_design.md` as the design-only
    authority for Live 3D and future Live 4D readability. It distinguishes the
    resolved exterior-cell convexity problem from remaining orientation
    ambiguity and defines the canonical view, cells, landmarks, rotation
    feedback, HUD, and manual acceptance grammar without renderer changes.
25. `DONE` `[BKL-P3-032]` Stage 22e Live 3D visual-language implementation:
    implement the Stage 22d authority through the existing mapper/renderer path
    without changing C++ gameplay semantics, accepted Live 2D, or Replay. The
    current partial implementation reserves the Godot shell panel regions and
    introduces a focused presentation/projection owner; Stage 22g adds the
    above-board canonical camera preset/status, compact bundle status,
    stronger active-vs-locked cell roles, and an active origin marker.
    Stage 22f manual Live 3D visual acceptance passed after Stage 22g
    corrections.
26. `DONE` `[BKL-P3-033]` Stage 22f acceptance gate before Stage 23:
    manual Live 3D visual acceptance passed against
    `docs/plans/godot_live_3d_manual_acceptance.md` after Stage 22g
    corrections. Stage 23 Live Plain 4D Godot Prototype is implemented
    narrowly.
27. `DONE` `[BKL-P3-034]` Stage 22g Live 3D visual acceptance corrections:
    correct the failed initial Stage 22f observations by using an above-board
    canonical Live 3D view, exposing camera preset/view diagnostics, keeping
    bundle status compact/readable with inspector detail, and making active
    cells stronger than locked cells with an origin/orientation marker. This
    is visual-only; Stage 22f passed after these corrections.
28. `DONE` `[BKL-P3-035]` Stage 23 Live Plain 4D Godot Prototype:
    add a separate Live 4D mode backed by C++ `PlainNDSession`, expose narrow
    `live_4d_*` bridge methods, render side-by-side W slices through the
    existing mapper/renderer and inherited exterior cell grammar, route Q/E as
    W movement, route R/T, F/G, V/B, Y/U, H/J, and N/M as XY, XZ, YZ, XW, YW,
    and ZW rotations, and show `LIVE 4D · C++ CORE` HUD state with signed last
    rotation and W context. Live 2D, Live 3D, Replay, topology, endgame, and
    golden traces remain preserved.
29. `DONE` `[BKL-P3-036]` Stage 23b Live 4D acceptance corrections:
    correct the manual GUI acceptance defects by making W-slice labels larger
    with high-contrast backing, consuming Space as live hard-drop before
    focused UI controls can handle accept/back/reset, and reducing Live 4D
    active-cell brightness while keeping active/locked roles distinct. This
    is visual/input-only; C++ gameplay semantics, topology, endgame, Live 2D,
    Live 3D, and Replay remain preserved.
30. `DONE` `[BKL-P3-038]` Stage 23c Live 4D view/readability corrections:
    replace W labels with `W SLICE n/N` headers and larger chips, include
    header clearance in Fit View bounds, open/reset Live 4D in the canonical
    fitted W-slice view, keep Fit View as recovery, and add safe camera keys
    `I/K`, `O/L`, and `-`/`=`. This is presentation/input-only; Q/E W movement,
    Space hard drop, Esc quit/back, Live 2D, Live 3D, Replay, and C++ gameplay
    semantics remain preserved.
31. `DONE` `[BKL-P3-039]` Stage 23d Live 4D zoom-control correction:
    make Live 4D zoom keys change orthographic camera size rather than camera
    distance, support `-`, `=`, `+`, keypad variants, and correct mouse-wheel
    direction, capture camera keys before focused UI controls can consume them,
    expose size/zoom diagnostics, and preserve Fit View as the fitted W-slice
    recovery action. This is
    Godot shell/camera/input only; C++ gameplay semantics, Q/E W movement,
    Space hard drop, Esc quit/back, I/K pitch, O/L yaw, Live 2D, Live 3D, and
    Replay remain preserved.
32. `DONE` `[BKL-P3-037]` Stage 23 manual Live 4D acceptance rerun:
    Stage 23 Live Plain 4D Godot Prototype passed manual GUI acceptance after
    Stage 23b/23c/23d corrections. Live 4D is accepted as a narrow plain
    bounded prototype. Stage 24 Live ND polish and hardening is now unblocked.
    Topology and endgame remain deferred.
33. `DONE` `[BKL-P3-040]` Stage 24 Live ND polish and hardening:
    harden Godot live shell lifecycle/input behavior after Stage 23 acceptance.
    Returning from Replay to an existing Live 2D, Live 3D, or Live 4D session
    resumes the selected mode without resetting native C++ state, pauses
    non-selected live modes, clears focus/repeat state, and preserves pre-UI
    Space hard-drop plus Live 4D camera/zoom capture after focus changes and
    mode switching. Fit View remains recovery; Q/E remain W-/W+ in Live 4D;
    Space remains hard drop; Esc remains back/quit; Live 2D, Live 3D, Replay,
    topology, endgame, trace parity, and C++ gameplay semantics remain
    preserved. Manual Stage 24 acceptance via
    `docs/plans/live_nd_manual_acceptance.md` passed, so Stage 25 topology
    planning is unblocked.
34. `DONE` `[BKL-P3-041]` Stage 25 topology Godot/C++ port planning:
    add `docs/plans/topology_godot_core_port_plan.md` as the planning-only
    topology port authority after accepted plain bounded Live ND. Python
    remains the topology oracle, C++ is the future topology
    transport/gameplay authority after parity, Godot remains the topology
    product shell/render/HUD/editor presentation owner, accepted Live
    2D/3D/4D and Replay stay preserved, and a later topology trace contract
    audit / expansion is still recommended before native topology
    implementation. No topology gameplay, C++ topology transport, Godot
    topology editor UI, endgame, C#, Python runtime calls from Godot, or
    Godot-side gameplay legality is added.
35. `DONE` `[BKL-P3-042]` Stage 28 Godot shell compliance and layout
    stabilization:
    add `docs/architecture/godot_shell_layout_stabilization.md` as the audit
    and layout-contract record, keep Godot inside product-shell/replay-view
    and accepted live-shell presentation boundaries, and stabilize the Replay
    Viewer so the left browser, center game viewport, right inspector, and
    bottom controls have explicit minimum-size ownership. Python gameplay
    semantics, topology, trace semantics, parity evidence, native authority,
    and authority transfer remain unchanged.
36. `DONE` `[BKL-P3-043]` Stage 29 Godot shell settings registry foundation:
    add `godot/Tet4D.Godot/config/shell_settings_registry.json`, registry
    validation, shell-local/session storage, generated settings controls, and
    Godot tests for registry and panel generation. The first settings slice is
    limited to replay, display, theme, diagnostics, and controls-help shell
    settings; no gameplay, topology, movement, keyboard rebinding, Python
    config migration, parity logic, native semantic authority, or authority
    transfer is added.
37. `DONE` `[BKL-P3-044]` Stage 30 Godot replay shell UX acceptance:
    add `docs/architecture/godot_replay_shell_ux_acceptance.md`, document the
    manual launch/readability result and assistive-access navigation blocker,
    and keep the fixes to shell-local readability: distinct Plain display
    theme/palette, clearer generated settings panel framing/wrapping, and
    layout coverage for settings-panel reachability inside the right
    inspector. No gameplay, topology, trace semantics, parity evidence, native
    authority, or authority transfer is added.
38. `DONE` `[BKL-P3-045]` Stage 31 Godot visual style authority:
    add `docs/architecture/godot_visual_style_authority.md` as the design
    authority for Godot product-shell visual work. It fixes the visual
    direction, the `diagnostic` / `plain` / `tron` theme model, semantic
    colour roles, concrete palettes, typography, spacing, component styling,
    board/replay visual language, accessibility constraints, and the MVP
    baseline decision accepting the current replay/settings shell with known
    manual-navigation limitations. No Godot implementation, gameplay,
    topology, trace semantics, parity logic, native authority, or authority
    transfer is added.
39. `DONE` `[BKL-P3-046]` Stage 32 Godot visual style foundation:
    add `godot/Tet4D.Godot/config/shell_theme_palettes.json`, split
    role/palette/style-manager/control-applier scripts under
    `godot/Tet4D.Godot/scripts/ui/style/`, make `tron` the default
    `theme.name`, apply shared style roles to shell controls/settings surfaces,
    route board/replay visual materials through the same palette roles, and
    add Godot tests for palettes, style manager behavior, settings integration,
    style application, and replay visual role mapping. No gameplay, topology,
    trace semantics, replay-frame semantics, parity logic, native authority, or
    authority transfer is added.

## Governance Watchlist

- Keep docs/manifests/current-state/backlog synchronized in the same batch as
  code changes.
- Keep generated maintenance docs current after status-layer edits.
- Keep policy inventories in `config/project/policy_pack.json`, not in
  `tools/governance/validate_project_contracts.py`.
- Keep `CURRENT_STATE.md` limited to restart handoff material; do not
  reintroduce batch ledgers or validation transcripts there.
- Keep `docs/WORKFLOW_CODEX.md` context-switch profiles explicit and aligned
  with the current authority stack.
- Do not let historical topology-playground manifests drift back into active
  authority.
- Keep canonical runtime selectors as the only explorer-path input authority.
- Keep the `controls_panel_rows.py` / `controls_panel_values.py` /
  `controls_panel_actions.py` split intact, keep routing/command/launch detail
  in `controls_panel_routing.py` / `controls_panel_commands.py` /
  `controls_panel_launch.py`, and do not drift those responsibilities back
  into `controls_panel.py`.
- Keep the preview/playability signature limited to explorer topology plus
  resolved board dims, keep cached same-signature reuse in
  `scene_preview_state.py`, and do not let probe/sandbox/helper or
  non-topological launch state trigger new rigid-playability recompute.
- Keep the `scene_state.py` / `scene_state_canonical.py` /
  `scene_state_probe.py` split intact; do not drift canonical sync/write or
  probe normalization back into one mixed state file.
- Keep the legacy topology editor isolated to
  `Settings -> Board / Setup Defaults -> Legacy Topology Editor`.
- Keep the shared menu shell aligned across launcher, setup, pause, keybindings,
  leaderboard, and bot options; `Settings` still uses a custom loop but now
  renders the shared side buttons. Do not reintroduce subtitle-only header
  variants and keep the launcher/pause input-config surface consistently
  labeled `Keybindings`.
- Keep keyboard configuration inside the shared `Settings` flow, and do not
  reintroduce a parallel launcher-only keyboard-profiles submenu or revive the
  authored `Controls` wrapper as a visible one-item runtime page.

## Recent Completed Work

Completed on 2026-04-30:

- settings shell parity follow-up: `Settings` now renders the shared side
  buttons (`Backspace` back, `Esc` exit-only at settings root after cancelling
  text entry, `Q` global quit) while retaining its existing custom loop; full
  Settings/MenuRunner unification remains optional future cleanup.
- semantic persistence migration follow-up: migrated key categorical fields to
  canonical semantic IDs (`*_id`) with legacy `*_index` compatibility shadows,
  migrated int-backed toggles to real booleans, added `storage_type` /
  `legacy_storage_type` metadata to prevent enum/bool slider regressions, and
  tightened governance + generated settings/config references to reflect the new
  semantic persistence contract.

Completed on 2026-04-29:

- menu IA follow-up: shared menu input semantics now use `Backspace` for
  ordinary menu-up/back and `Esc` as exit-only from the current menu root;
  the shared menu shell now renders persistent clickable side buttons for
  `Backspace` / `Esc` / `Q` without reintroducing a visible Quit row.
- settings reevaluation follow-up: Settings is now split into `Gameplay`,
  `Board / Setup Defaults`, `Controls`, `Display`, `Audio`, and
  `Endgame / Explosion`; `Controls` owns Keyboard Bindings; and
  `Endgame / Explosion` exposes full per-dimension persisted
  `explosion_defaults.<2d|3d|4d>.*` editing surfaces.

Completed on 2026-04-27:

- clean-reset endgame deletion pass so active endgame moving-cell rendering now
  depends only on the shared survivor-subset explosion controller, the old
  relic fallback no longer reconstructs all locked cells as native-board moving
  particles, and deferred escaping-cell shell artifacts remain intentionally
  unimplemented for later follow-up
- endgame survivor-only runtime contract pass so the live subset now uses
  `endgame_live_cell_fraction` over available locked cells (not total board
  capacity), snapshot state is split into deterministic
  `persistent_live_cells` plus complementary `escaping_cells`, and the shared
  explosion controller is seeded only from that persistent survivor subset
- endgame shell-artifact pass so `escaping_cells` now produce capped,
  deterministic, short-lived streak/shard/spark overlays while survivors remain
  the only moving board cells in the shared explosion controller
- endgame grid-break overlay pass so existing escaping shell artifacts now
  drive capped short-lived tear/stress marks without introducing destructible
  grid state or rendering escapers as cells/cubes
- endgame manual-verification follow-up so survivor counts now directly follow
  `endgame_live_cell_fraction` without high 3D/4D floors, full selected
  topology seams reach survivor runtime without gameplay gravity-axis
  exclusions, projected shadow/W-movement settings are consumed in endgame
  render paths, and rupture timing uses a slower config-backed visible
  charge/breakaway/artifact window
- endgame visual-tuning follow-up so rupture uses stronger config-backed flash,
  shell, and crack intensity while capped grid-break marks plus static shell
  state leave a low-alpha cracked-board residue behind survivor particles
  without reviving all-cells relics or escaping-cell rendering

Completed on 2026-04-20:

- workflow-codex profile follow-up landed on its separate docs branch, so
  every context-switch profile in `docs/WORKFLOW_CODEX.md` now carries an
  explicit `Verify:` line and `Skip unless cross-cutting:` scope, a dedicated
  `render` profile now covers large render/frontend hotspots, and the
  `governance` profile now explicitly calls out
  `tools/governance/generate_maintenance_docs.py`
- docs-authority cleanup landed on `master`, so
  `docs/plans/topology_playground_debt_register.md`,
  `docs/plans/cleanup_master_plan.md`, and `docs/BACKLOG.md` now reflect the
  current topology-playground debt/domain tables instead of keeping stale
  resolved rows or duplicate completed-date headers in active reporting
- config-backed runtime-constants governance landed on `master`, so
  `config/project/policy_pack.json` now defines
  `code_rules.config_backed_runtime_constants`, unified governance validation
  enforces config-backed authority for targeted repo-owned runtime constants,
  the loader-import bypass is covered by focused tests, and the duplicated
  leaderboard fallback constant is gone
- project-structure index batch landed on `master`, so generated
  `docs/PROJECT_STRUCTURE.md` now carries symbol skim, likely-test hints, and
  confidence labels backed by `tools/governance/generate_maintenance_docs.py`
  plus focused indexing tests, and that work is no longer part of active
  implementation wording

Completed on 2026-04-18:

- shared menu pointer-activation fix so `MenuRunner` now owns mouse
  hover/press/release hit-testing for launcher and pause rows/action-group
  chips, the leaderboard name-entry prompt buttons and leaderboard shell
  `Back` chip now route through real pointer targets instead of keyboard-only
  handling, and the bot-options shell `Back` affordance follows the same
  visible-bounds click contract

Completed on 2026-04-17:

- shell-preserving topology-playground latency/caching hardening so
  `scene_preview_state.py` now treats explorer topology plus resolved board
  dims as the effective preview/playability signature, restores same-signature
  cached playability results immediately when available, avoids queueing
  deferred rigid scans for invalid preview states, and keeps play-preview
  launch forcing completion only for still-pending valid rigid analysis
- shell-preserving topology-playground control-shell cleanup so
  `controls_panel_routing.py` now owns navigation/pane/shortcut/enter routing,
  `controls_panel_commands.py` owns save/export/experiment command execution,
  and `controls_panel_launch.py` owns play-preview launch preparation/runtime
  handoff, leaving `controls_panel.py` as a thinner visible-shell facade while
  preserving launcher/test compatibility seams and deferred playability work in
  `scene_preview_state.py`
- shell-preserving topology-playground state cleanup so `scene_state.py` now
  keeps the state model plus pane/tool/workspace routing, while
  `scene_state_canonical.py` owns canonical runtime sync/write and fallback
  storage handling and `scene_state_probe.py` owns probe selectors/mutations
  and probe-state synchronization without reopening the shell contract or the
  deferred preview/playability ownership in `scene_preview_state.py`
- shell-preserving topology-playground cleanup so explorer row-mutation and
  seam-edit helpers now live in
  `src/tet4d/ui/pygame/topology_lab/controls_panel_actions.py`, dropping
  `controls_panel.py` to a smaller shell/orchestration owner while preserving
  deferred rigid playability analysis, same-signature cache reuse, and the
  existing launcher/test compatibility seams
- post-policy-pack hardening so `CURRENT_STATE.md` is restart-only again,
  `docs/WORKFLOW_CODEX.md` now defines explicit `review` / `engine` /
  `menu_ui` / `topology_explorer` / `packaging` / `governance` / `handoff`
  context-switch profiles, and project-contract validation now reads menu and
  policy-index inventories from `config/project/policy_pack.json` instead of
  Python literals

Completed on 2026-04-15:

- frozen packaging follow-up so the canonical PyInstaller spec now includes
  hidden imports for the lazy `tet4d.ai.playbot.*` package surface, preventing
  Windows frozen launcher/setup imports from failing on missing
  `tet4d.ai.playbot.dry_run`

Completed on 2026-04-12:

- flattened the authored launcher/settings menu tree so `Play` keeps same-row
  `Play` / `Setup` actions, `Settings` removes the old single-child wrappers,
  and `Game` absorbs gameplay-adjacent micro-pages into one shared scrolling
  settings surface
- unified remaining menu-family stragglers such as leaderboard and bot options
  onto the shared shell treatment, while keybindings now uses the same menu
  typography family as the rest of the launcher/settings/pause shell
- upgraded the endgame relic field so persistent motion, topology behavior,
  speed controls, and optional collisions all operate on true ND relic state
  before projection instead of flattened post-process drift
- hardened Windows release packaging so stale MSI/CAB outputs are cleaned
  before each build, external CAB emission is a hard build failure, and the
  release workflow uploads only MSI artifacts from Windows jobs

Completed on 2026-04-10:

- dedicated post-terminal endgame animation phase so `2D`, projected `3D`,
  and projected `4D` gameplay now freeze a final board snapshot, drive locked
  cells and shell/frame fragments from deterministic seeded fragment state
  instead of live-board mutation, and keep leaderboard/session completion tied
  to the completed terminal transition rather than the first raw `game_over`
  tick
- leaderboard contract cleanup so leaderboard prompts now trigger only on
  completed standard-play `game_over` transitions, never from explorer mode or
  quit/menu/restart exits, and persisted score storage now keeps the top `10`
  entries per gameplay dimension instead of one mixed global cap
- projected `3D` / `4D` active-piece occlusion pass so board gridlines and
  board-box edges now resolve against the active piece per projected fragment
  from screen overlap plus projected depth instead of one global draw-order

Completed on 2026-04-11:

- post-terminal relic-field follow-up so the endgame now splits into finite
  `endgame_shatter` and persistent `endgame_relic_field` phases, shell/grid/
  box fragments die after the rupture, and locked-cell debris is captured into
  deterministic bounded orbit/drift families instead of continuing as one-shot
  ballistic spray
- endgame preset follow-up so the persistent relic field now freezes a shared
  preset id plus a separate interaction mode into the endgame snapshot,
  supports the required `wrap_all`, `invert_all`, and `sphere` topology-flavored
  motion fields, and exposes those controls together under
  the `Settings -> Game` endgame section instead of scattering them across new
  menus or multiplying preset ids for collision variants
- leaderboard registration now stays in the post-terminal gameplay flow as a
  compact modal overlay on top of the existing endgame surface instead of
  taking over the screen as a dedicated full-page prompt, while preserving the
  same form-state and persistence authority
- shared menu-slider layout correction so launcher, setup, and in-game slider
  rows now use one larger config-backed slider geometry contract with explicit
  label/value/track allocation, preventing clipping in supported compact menu
  shells instead of relying on per-screen width guesses

- canonical menu-source-of-truth pass so `config/menu/structure.json` now
  defines the launcher tree, pause tree, settings hierarchy, the flattened
  scrolling `Game` page, keyboard bindings placement, retained legacy
  placement, and the typed row/component model
  without parallel Python-owned settings sections or launcher routes
- shared menu-overflow pass so settings, keybindings, and bot options now use
  one auto-scrolling viewport with reserved scrollbar width, selection
  visibility enforcement, and shared scrollbar geometry instead of clipping
  oversized menus off-screen
- settings IA flattening pass so `Settings -> Game` is now one scrolling page
  with `Gameplay`, `Board / Geometry`, `Movement / Rotation`,
  `Endgame Effects`, and `Difficulty / Pace` sections instead of a submenu
  forest

- standalone-first locked-cell explosion subsystem landed under
  `src/tet4d/ui/pygame/locked_cell_explosion/`, modeling frozen locked cells as
  seam-aware particles with dedicated topology transport, explicit
  `boundary_response` / `particle_collisions` axes, render projection helpers,
  and class-prioritized seam/boundary/collision audio aggregation
- keep the explosion launcher on shared UI/runtime paths: ND camera input must
  keep reusing the existing scene-camera controls, trace retention stays a
  bounded numeric control, and launcher rows must not drift away from
  numeric-slider / categorical-selector typing discipline
- topology-playground `Sandbox` can now launch that same standalone explosion
  path directly from the current sandbox cell population for arbitrary explorer
  topologies, while keeping the effect explorer-owned rather than gameplay-
  legality-owned
- game-end handoff now snapshots locked cells plus topology inputs into the
  explosion subsystem, freezes gameplay progression, and routes locked-cell
  render/audio ownership through the dedicated controller instead of live-board
- regression correction (2026-04-18): the main launcher now exposes a direct
  `Explosion Simulator` surface, the old collapsed interaction enum is retired,
  explorer/game-end both route through the split `boundary_response` /
  `particle_collisions` config, and particle-collision audio is heavily capped
  so seam traversal stays readable under dense motion instead of routing the
  effect back through gameplay movement code or tetromino ownership
- explosion-render polish pass (2026-04-21): simulator trace history is longer
  but remains bounded and time/distance-gated, true-board `3D` / `4D` preview
  now resolves board lines against explosion cells through the shared projected
  occlusion path instead of painting cells over the box/grid, seam/bounce
  contact presentation now starts on the exact board boundary plane with
  bounce containment kept inside the board volume, the simulator now separates
  `grid_mode` from `shadow_mode`, and topology preset presentation reuses the
  shared explorer preset-section authority so sphere-like / experimental
  families remain available without a simulator-local registry
- explosion-simulator regression fix pass (2026-04-22): true-board trace draw
  is now rendered with stronger stroke/alpha above board/grid layers so live
  use stays readable in `2D` / `3D` / `4D`, simulator-local mouse dropdown
  boundary alignment now reuses one canonical cell-extent face definition
  (`-0.5 .. size - 0.5` per axis) across seam/bounce contact, the drawn
  board box, edge-grid rendering, and render-only boundary/shadow guides,
  board-native `3D` / `4D` trace endpoints now project the actual particle
  centers instead of a duplicated half-cell-offset point, and
  simulator-local mouse dropdown
  interaction now opens/selects values without obscuring labels, simulator grid
  options now expose explicit `none | edge | full` naming while shadow remains
  independent, trace retention is text-editable with bounded parse/clamp
  validation, and `4D` true-board preview now exposes selectable `fade` /
  `box_size` W-movement animation using the existing gameplay layer-scale path
- menu normalization pass so runtime launcher/settings/keybindings consumers
  now read a compiled normalized graph rather than the raw authored menu tree,
  singleton wrappers are collapsed before render/input use, and the one-row
  `Visual / Animation` page no longer survives as a visible runtime submenu
- authored menu-flattening + direct-play pass so `config/menu/structure.json`
  now drops the settled `Controls`, `Legacy`, and one-row `Visual /
  Animation` wrappers entirely, `Play -> 2D/3D/4D` uses same-row
  `Play` / `Setup` action groups instead of another layer, direct `Play`
  launches from persisted settings, and `Setup` still routes through the
  existing setup screens before using the same gameplay launch path
- ND endgame-motion pass so persistent relic updates now advance and collide in
  ND state before projection, `wrap_all` / `invert_all` / `sphere` differ by
  ongoing ND boundary behavior rather than only start layout, 4D relics can
  traverse hidden axes and blend across frozen layer boards, and the `Game`
  page now includes separate `Relic field speed` and `Shatter speed` controls
  instead of baking speed into preset identity
- shared menu-shell completion pass so leaderboard and bot options now render
  on the same title/back-chip/framed-panel/footer shell as the other menu
  surfaces, and keybindings main rows now use the shared menu typography
  instead of a separate panel-font treatment
- post-terminal cleanup follow-up so the helper side panel no longer repeats a
  separate `GAME OVER` label and the frozen endgame fragments remain visible
  indefinitely instead of fading away after a fixed lifetime
  assumption, with shared primitive emission/resolution coverage and `2D`
  intentionally left on its simpler path


Completed on 2026-03-29:

- compact governance + planning layer consolidation around
  `docs/DOCUMENTATION_MAP.md`, the reduced active plan layer, and the unified
  governance/code-rules manifests
- topology-playground explorer board-size floor update so explorer height can
  now be reduced from `8` to `6` without reopening the frozen shell contract
- topology-playground preset naming alignment so the all-wrap `3D` and `4D`
  explorer presets now surface explicitly as torus presets while preserving
  stable compatibility ids
- topology-playground local preview cache pass so identical explorer preview
  signatures can reuse a versioned repo-local on-disk cache under `state/`
  instead of rebuilding movement graphs every run
- dead-seam cleanup pass so unused gameplay/runtime wrapper helpers,
  test-only help/menu validation seams, and the test-only menu-graph linter
  no longer stay alive through isolated unit-test coverage; `launcher_play`
  remains a live launcher dependency and is not part of that removal set
- dead-test cleanup pass so cache-debug tests no longer pin projection/control
  icon internals, camera/view key smoke now exercises live routing helpers
  instead of dead wrapper entrypoints, and topology-lab sandbox tests no
  longer depend on a dead private rotation helper
- topology-explorer movement-graph fast path so preview compilation now builds
  graph edges through direct interior-step arithmetic, precomputed boundary
  seam lookups, and same-signature in-process graph-row memoization instead of
  routing every cell-step through the fully general transport resolver path
- topology-playground persistent cache completion so the same versioned
  topology cache now retains preview payloads, movement-graph rows, and rigid
  playability analysis on disk, and Advanced gameplay exposes cache measure
  plus cache clear actions for that persistent cache set
- topology-playground cache-miss warning fix so absent repo-local explorer
  preview cache files now behave as ordinary silent misses while corrupt
  existing cache files still use the existing warning-and-rebuild path
- topology-playground/layout visibility pass so compact sidebar rows and
  Advanced gameplay rows now wrap label/value text instead of obscuring it,
  shared action buttons/workspace tabs now wrap instead of hard truncating,
  and the external helper lane keeps a wider readable budget on supported
  compact shells
- topology-playground helper-panel redesign so the right helper now renders as
  a minimal structured controls card with one short workspace/tool context
  line plus movement and rotation keys pulled from the current active
  keybindings for the active dimension
- topology-playground text-layout dedup so shared wrapped-text primitives now
  handle row sizing plus centered compact-label rendering for launcher
  settings rows, Topology Playground rows, workspace tabs, and transform /
  action buttons instead of keeping near-duplicate wrapping logic in each
  caller
- topology-playground row-render dedup so launcher settings and Topology
  Playground control rows now share the same selection-highlight and wrapped
  label/value text renderer instead of maintaining parallel drawing loops
- topology-playground panel/text dedup so helper/preview cards and centered
  launcher title/status/hint lines now reuse shared framed-panel and fitted
  centered-text helpers instead of repeating local drawing boilerplate
- topology-playground compact-chip dedup so top-bar validity/dimension chips
  and footer helper chips now reuse one shared centered chip renderer instead
  of repeating local fit-center-border badge drawing logic
- topology-playground fitted-text cleanup so remaining shell title/header and
  compact control-label callers now route through the shared fitted-text
  helpers instead of keeping local fit-text render boilerplate
- topology-playground duplicate-panel cleanup so local framed-panel and
  fitted-text helpers in projection/transform surfaces now use the existing
  shared pygame UI primitives instead of keeping separate caller-local
  drawing helpers
- topology-playground dead-code cleanup so the shared side-panel and modern
  explorer-workspace paths no longer carry unused parameters, and the current
  `vulture` sweep is back to clean high-confidence results
- launcher settings split fix so top-level `Game`, `Display`, and `Audio`
  entries now open category-specific settings screens instead of reopening the
  bundled hub behind separate labels
- launcher settings IA cleanup so the `Advanced` submenu is retired, `Legacy
  Topology Editor Menu` moves up to the main settings level, and the old
  `Game -> Advanced gameplay...` sub-flow is retired in favor of an inline
  `Advanced gameplay` section inside the game settings screen
- launcher settings config-authority cleanup so settings section
  titles/subtitles/header membership/row ownership and launcher category
  routes now live in `config/menu/structure.json`, top-level settings policy
  now derives from that same section contract, bad section header/row
  references now fail validation instead of degrading filtered settings
  screens, and launcher/settings Python is reduced to validated
  config-driven rendering and dispatch
- repo documentation follow-up so menu graph and filtered settings edits now
  have a dedicated contributor guide in `docs/MENU_STRUCTURE_EDITING.md`,
  with docs routing and menu-structure RDS copy updated to match the current
  config-first contract
- keybinding contract-hardening follow-up so `config/keybindings/defaults.json`
  and saved profile payloads are now validated against the same
  catalog-backed action/group/dimension contract, and direct config edits now
  have a dedicated contributor guide in `docs/KEYBINDINGS_EDITING.md`
- keybinding runtime-ownership completion so mutable live keybinding maps now
  sit in `src/tet4d/engine/runtime/keybinding_runtime_state.py`, built-in
  defaults enforce complete required-action coverage, payloads now carry an
  explicit schema version, partial custom profile overrides remain allowed by
  contract, and `./scripts/check_keybinding_contract.sh` now provides the
  focused validation path for direct keybinding config work
- keybinding runtime-accessor cleanup so engine/runtime now exports narrow
  keybinding read accessors and the help/tutorial/control/setup callers that
  only need runtime grouped bindings or active-profile reads no longer depend
  on the wider pygame keybinding adapter
- keybinding docs follow-up so contributors now have both the full
  `docs/KEYBINDINGS_EDITING.md` contract guide and a shorter
  `docs/SHORT_KEYBINDINGS_GUIDE.md` checklist for common direct config edits
- keybinding config-format follow-up so defaults and saved payloads now accept
  readable key-name strings in addition to integer keycodes, with the store
  normalizing them before runtime use and docs explaining the allowed forms
- keybinding stale-source cleanup so dead legacy defaults code is removed and
  the obsolete `keybindings/profiles/small/` built-in directory is purged at
  startup instead of silently coexisting with the canonical root `keybindings/*.json`
- keybinding round-trip repair so every serialized keypad token written by the
  runtime is accepted again at load/validation time, and invalid custom
  profiles now surface a hard load failure instead of broad silent overwrite
- dead-code pruning follow-up so another small set of unreferenced helpers and
  stale compatibility leftovers now drops out of playbot, core, gameplay,
  help, settings, and topology-lab code without changing live behavior
- `vulture` bucket-1 pruning follow-up so the obvious non-test UI/tooling
  leftovers identified by the current high-confidence sweep are removed before
  any deeper verify-first or public-bridge pruning pass
- dead-wrapper retirement follow-up so test-only topology-lab sidebar/preview/
  probe-control seams and their wrapper-pinning tests are removed instead of
  preserved as fake compatibility surfaces
- config-reference/theme follow-up so `config/ui/theme.json` now participates
  in the generated configuration reference, project-config tests now pin theme
  color fallback/validation behavior, and topology-playground color reads stay
  lazy at the UI seam instead of freezing once at import time
- topology-playground sandbox-neighbor row click fix so the modern shell now
  toggles Sandbox `Neighbors` directly on mouse click in `3D` / `4D` instead
  of requiring keyboard row adjustment to disable the overlay
- topology-playground sandbox auto-move latency fix so Sandbox moves no longer
  force a full rigid-playability rescan while the canonical analysis is still
  pending in `AUTO` mode
- topology-playground compact footer action-lane sizing fix so the six-button
  Sandbox footer keeps labels like `Next Piece` and `Show Path` visible under
  the compact shell layout tested in CI
- topology-playground authority/spec/status/menu alignment around the settled
  modern `Topology Playground` contract and legacy-editor placement
- shared menu-shell rework so launcher/setup/pause/settings/keybindings now
  share title-cased subtitle-free headers, visible `Back` affordances,
  bounded numeric sliders, flash-on-change row feedback, bulkier title-font
  selection, and slightly more Tron-1982-inspired panel/background treatment
- topology-playground shell-layout extraction plus deterministic cross-surface
  text-visibility coverage
- topology-playground preview/cache extraction and shared canonical-state
  write-path cleanup
- topology-playground deferred rigid-playability caching pass, including
  same-signature reuse and profiler-script repair
- topology-playground compact-shell readability pass for sidebar/helper width
  allocation and wrapped helper copy
- topology-playground seam-edit help pass so the current Editor seam workflow
  is now documented both in `docs/help/TOPOLOGY_PLAYGROUND_SEAM_EDITING.md`
  and in the shared launcher/pause help topic registry
- topology-playground exploration return-menu fix so `Explore This Topology`
  now exits directly back to the main playground shell on `menu` instead of
  opening the generic independent gameplay pause menu first
- windows packaging hardening pass so the published Windows installer is
  enforced as one self-contained `.msi`, stale `*.msi` / `*.cab` outputs are
  cleaned before each run, external CAB emission now fails the Windows build,
  and the release workflow uploads only Windows `*.msi` artifacts
- dead-code cleanup pass removing zero-reference board/menu/tutorial helper
  shims plus the unused topology-lab `_TEST_COMPAT_EXPORTS` tuple
- built-in keybinding defaults redesign so shipped movement uses a compact
  standard-first cluster, rotation uses the fixed `RT FG VB YU HJ NM` ladder,
  and 3D/4D camera defaults now share the same core number-row layout with an
  explicit 4D reset on `0`
- built-in keybinding materialization fix so startup now refreshes stale
  built-in profile JSON files from the current shipped defaults payload
  instead of silently consuming older on-disk movement/rotation/camera
  layouts
- final governance-pack prune after unified manifest cutover, including
  maintenance-doc regeneration and local gate re-verification

## 5. Change Footprint

Current batch:

- docs-authority cleanup in `docs/plans/topology_playground_debt_register.md`,
  `docs/plans/cleanup_master_plan.md`, and `docs/BACKLOG.md`
- stale active-debt and cleanup-domain wording removed so current ledgers match
  the live repo state more closely
- merged project-structure index work stays in recent-completed reporting
  instead of the current-batch footprint

## Historical Milestones

March 2026 milestones retained here as compact orientation only:

- 2026-03-22:
  visible-shell redesign locked for launcher + Topology Playground, with
  direct `Topology Playground` entry and legacy editor isolation
- 2026-03-20 to 2026-03-21:
  `Editor` / `Sandbox` / `Play` workspace model stabilized, sandbox-first
  entry locked, helper/neighbor/probe contracts clarified, and focused menu /
  projection / gameplay tests aligned
- 2026-03-17 to 2026-03-19:
  shared gameplay animation settings expanded and threaded through 2D/3D/4D
  runtime setup
- 2026-03-12 to 2026-03-14:
  canonical-state migration deepened across launch, probe, sandbox, unsafe
  topology handling, playability signaling, and play launch semantics
- 2026-03-10 to 2026-03-11:
  early topology-playground staged migration and sandbox/runtime ownership
  movement landed

For detailed historical implementation notes, use:

- `CURRENT_STATE.md`
- `docs/history/DONE_SUMMARIES.md`
- `docs/history/topology_playground/`
